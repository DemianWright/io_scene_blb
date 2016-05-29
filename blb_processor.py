# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
'''
A module for processing Blender data into the BLB file format for writing.

@author: Demian Wright
'''

from decimal import Decimal, Context, setcontext, ROUND_HALF_UP
from math import ceil
from mathutils import Vector

# Blender requires imports from ".".
from . import logger, common, constants

# Number of decimal places to round floating point numbers.
FLOATING_POINT_DECIMALS = 6
FLOATING_POINT_PRECISION = Decimal("0.000001")

# Set the Decimal number context: 6 decimal points and 0.5 is rounded up.
setcontext(Context(prec=FLOATING_POINT_DECIMALS, rounding=ROUND_HALF_UP))


def calculate_coverage(brick_size=None, calculate_side=None, hide_adjacent=None, forward_axis=None):
    """Calculates the BLB coverage data for a brick.

    Args:
        brick_size (sequence of integers): An optional sequence of the sizes of the brick on each of the XYZ axes.
                                           If not defined, default coverage will be used.
        calculate_side (namedtuple): An optional named tuple of boolean values where the keys are the names of the brick sides.
                                     A value of true means that coverage will be calculated for that side of the brick according the specified size of the brick.
                                     A value of false means that the default coverage value will be used for that side.
                                     Must be defined if brick_size is defined.
        hide_adjacent (namedtuple): An optional named tuple of boolean values where the keys are the names of the brick sides.
                                    A value of true means that faces of adjacent bricks covering this side of this brick will be hidden.
                                    A value of false means that adjacent brick faces will not be hidden.
                                    Must be defined if brick_size is defined.
        forward_axis (Axis): The optional user-defined BLB forward axis.
                             Must be defined if brick_size is defined.

    Returns:
        A sequence of BLB coverage data.
    """

    coverage = []

    # TODO: Loop?

    # Does the user want to calculate coverage in the first place?
    if calculate_side is not None:
        # Initially assume that forward axis is +X, data will be swizzled later.

        # Top: +Z
        if calculate_side.top:
            # Calculate the area of the top face.
            area = brick_size[constants.INDEX_X] * brick_size[constants.INDEX_Y]
        else:
            area = constants.DEFAULT_COVERAGE

        # Hide adjacent face: True/False
        coverage.append((hide_adjacent.top, area))

        # Bottom: -Z
        if calculate_side.bottom:
            area = brick_size[constants.INDEX_X] * brick_size[constants.INDEX_Y]
        else:
            area = constants.DEFAULT_COVERAGE
        coverage.append((hide_adjacent.bottom, area))

        # North: +X
        if calculate_side.north:
            area = brick_size[constants.INDEX_X] * brick_size[constants.INDEX_Z]
        else:
            area = constants.DEFAULT_COVERAGE
        coverage.append((hide_adjacent.north, area))

        # East: -Y
        if calculate_side.east:
            area = brick_size[constants.INDEX_Y] * brick_size[constants.INDEX_Z]
        else:
            area = constants.DEFAULT_COVERAGE
        coverage.append((hide_adjacent.east, area))

        # South: -X
        if calculate_side.south:
            area = brick_size[constants.INDEX_X] * brick_size[constants.INDEX_Z]
        else:
            area = constants.DEFAULT_COVERAGE
        coverage.append((hide_adjacent.south, area))

        # West: +Y
        if calculate_side.west:
            area = brick_size[constants.INDEX_Y] * brick_size[constants.INDEX_Z]
        else:
            area = constants.DEFAULT_COVERAGE
        coverage.append((hide_adjacent.west, area))

        # Swizzle the coverage values around according to the defined forward axis.
        # Coverage was calculated with forward axis at +X.
        # The order of the values in the coverage is:
        # 0 = a = +Z: Top
        # 1 = b = -Z: Bottom
        # 2 = c = +X: North
        # 3 = d = -Y: East
        # 4 = e = -X: South
        # 5 = f = +Y: West

        # Technically this is wrong as the order would be different for -Y forward, but since the bricks must be cuboid in shape, they are symmetrical.
        if forward_axis == constants.Axis.positive_y or forward_axis == constants.Axis.negative_y:
            # New North will be +Y.
            # Old North (+X) will be the new East
            coverage = common.swizzle(coverage, "abfcde")

        # Else forward_axis is +X or -X: no need to do anything, the calculation was done with +X.

        # No support for Z axis remapping yet.
    else:
        # Use the default coverage.
        # Do not hide adjacent face.
        # Hide this face if it is covered by constants.DEFAULT_COVERAGE plates.
        coverage = [(0, constants.DEFAULT_COVERAGE)] * 6

    return coverage


class BrickBounds(object):
    """A class for storing brick bounds Blender data.

    Stores the following data:
        - Blender object name,
        - object dimensions,
        - minimum world coordinate,
        - and maximum world coordinate.
    """

    def __init__(self):
        # The name of the Blender object.
        self.name = None

        # The dimensions are stored separately even though it is trivial to calculate them from the coordinates because they are used often.
        self.dimensions = []

        self.world_coords_min = []
        self.world_coords_max = []


class BLBData(object):
    """A class for storing the brick data to be written to a BLB file.

    Stores the following data:
        - size (dimensions) in plates,
        - grid data,
        - collision data,
        - coverage data,
        - and sorted quad data.
    """

    def __init__(self):
        # Brick XYZ integer size in plates.
        self.brick_size = []

        # Brick grid data sequences.
        self.brick_grid = []

        # Brick collision box coordinates.
        self.collision = []

        # Brick coverage data sequences.
        self.coverage = []

        # TODO: Full breakdown of the quad data.
        # Sorted quad data sequences.
        self.quads = []


class BLBProcessor(object):
    """A class that handles processing Blender data and preparing it for writing to a BLB file."""

    class OutOfBoundsException(Exception):
        """An exception thrown when a vertex position is outside of brick bounds."""
        pass

    class ZeroSizeException(Exception):
        """An exception thrown when a definition object has zero brick size on at least one axis."""
        pass

    # TODO: Make into a property.
    # Error allowed for manually created definition objects. Used for rounding vertex positions to the brick grid.
    __HUMAN_ERROR = Decimal("0.1")

    # TODO: I bet I could refactor all of these methods into regular functions and just pass the data between them here.

    def __init__(self, context, properties):
        """Initializes the BLBProcessor with the specified properties."""
        self.__context = context
        self.__properties = properties
        self.__bounds_data = BrickBounds()
        self.__blb_data = BLBData()

        self.__vec_bounding_box_min = Vector((float("+inf"), float("+inf"), float("+inf")))
        self.__vec_bounding_box_max = Vector((float("-inf"), float("-inf"), float("-inf")))

        # Change the forward axis property to enum for easier handling.
        self.__properties.axis_blb_forward = constants.AXIS_STRING_ENUM_DICT[self.__properties.axis_blb_forward]

    @classmethod
    def __is_even(cls, value):
        """Returns True if given value is divisible by 2."""
        return value % 2 == 0

    @classmethod
    def __to_decimal(cls, value, decimals=FLOATING_POINT_DECIMALS):
        """Converts the given value to a Decimal value with up to 6 decimal places of precision."""

        if decimals > FLOATING_POINT_DECIMALS:
            decimals = FLOATING_POINT_DECIMALS

        # First convert float to string with n decimal digits and then make a Decimal out of it.
        return Decimal(("{0:." + str(decimals) + "f}").format(value))

    @classmethod
    def __force_to_int(cls, values):
        """Returns a new list of sequence values casted to integers."""
        result = []

        for val in values:
            result.append(int(val))

        return result

    @classmethod
    def __are_not_ints(cls, values):
        """
        Returns True if at least one value in the given list is not numerically equal to its integer counterparts.
        '1.000' is numerically equal to '1' while '1.001' is not.
        """

        for val in values:
            if val != int(val):  # TODO: Fix OverflowError & crash where nothing is selected and exporting only selection.
                return True

    @classmethod
    def __get_world_min(cls, obj):
        """Returns a new Vector(X,Y,Z) of the minimum world space coordinates of the given object."""

        vec_min = Vector((float("+inf"), float("+inf"), float("+inf")))

        for vert in obj.data.vertices:
            # Local coordinates to world space.
            coord = obj.matrix_world * vert.co

            vec_min[constants.INDEX_X] = min(vec_min[constants.INDEX_X], coord[constants.INDEX_X])
            vec_min[constants.INDEX_Y] = min(vec_min[constants.INDEX_Y], coord[constants.INDEX_Y])
            vec_min[constants.INDEX_Z] = min(vec_min[constants.INDEX_Z], coord[constants.INDEX_Z])

        return vec_min

    @classmethod
    def __record_world_min_max(cls, sequence_min, sequence_max, obj):
        """Updates the minimum and maximum found vertex coordinate.

        Checks if the specified Blender object's vertices' world space coordinates are smaller or greater than the coordinates stored in their respective
        minimum and maximum sequences and updates the values in those sequences with the object's coordinates if they are smaller or greater.

        Args:
            sequence_min (sequence of numbers): The sequence of smallest XYZ world space coordinates found so far.
            sequence_max (sequence of numbers): The sequence of largest XYZ world space coordinates found so far.
            obj (Blender object): The Blender object whose vertex coordinates to check against the current minimum and maximum coordinates.
        """
        for vert in obj.data.vertices:
            coordinates = obj.matrix_world * vert.co

            for i in range(0, 3):
                sequence_min[i] = min(sequence_min[i], coordinates[i])
                sequence_max[i] = max(sequence_max[i], coordinates[i])

    @classmethod
    def __index_to_position(cls, obj, index):
        """Returns the world coordinates for the vertex whose index was given in the current polygon loop."""
        return obj.matrix_world * obj.data.vertices[obj.data.loops[index].vertex_index].co

    @classmethod
    def __vertex_index_to_normal(cls, obj, index):
        """Calculates the normalized vertex normal for the specified vertex in the given object."""
        return (obj.matrix_world.to_3x3() * obj.data.vertices[obj.data.loops[index].vertex_index].normal).normalized()

    @classmethod
    def __all_within_bounds(cls, sequence, bounding_dimensions):
        """
        Checks if all the values in the given sequence are within the given bounding values.
        Assumes that both sequences have the same number of elements.
        Returns True only if all values are within the bounding dimensions.
        """
        # Divide all dimension values by 2.
        halved_dimensions = [value / Decimal("2.0") for value in bounding_dimensions]

        # Check if any values in the given sequence are beyond the given bounding_dimensions.
        # bounding_dimensions / 2 = max value
        # -bounding_dimensions / 2 = min value

        for index, value in enumerate(sequence):
            if value > halved_dimensions[index]:
                return False

        for index, value in enumerate(sequence):
            if value < -(halved_dimensions[index]):
                return False

        return True

    @classmethod
    def __modify_brick_grid(cls, brick_grid, volume, symbol):
        """Modifies the given brick grid by adding the given symbol to every grid slot specified by the volume."""

        # Ranges are exclusive [min, max[ index ranges.
        width_range = volume[constants.INDEX_X]
        depth_range = volume[constants.INDEX_Y]
        height_range = volume[constants.INDEX_Z]

        # Example data for a cuboid brick that is:
        # - 2 plates wide
        # - 3 plates deep
        # - 4 plates tall
        # Ie. a brick of size "3 2 4"
        #
        # uuu
        # xxx
        # xxx
        # ddd
        #
        # uuu
        # xxx
        # xxx
        # ddd

        # For every slice of the width axis.
        for w in range(width_range[0], width_range[1]):
            # For every row from top to bottom.
            for h in range(height_range[0], height_range[1]):
                # For every character the from left to right.
                for d in range(depth_range[0], depth_range[1]):
                    # Set the given symbol.
                    brick_grid[w][h][d] = symbol

    def __round_value(self, value, precision=1.0, decimals=FLOATING_POINT_DECIMALS):
        """Returns the given value as Decimal rounded to the given precision (default 1.0) and decimal places (default FLOATING_POINT_DECIMALS)."""

        # Creating decimals through strings is more accurate than floating point numbers.
        fraction = Decimal("1.0") / self.__to_decimal(precision, decimals)
        # I'm not entirely sure what the Decimal("1") bit does but it works.
        return self.__to_decimal((value * fraction).quantize(Decimal("1")) / fraction)

    def __round_values(self, values, precision=None, decimals=FLOATING_POINT_DECIMALS):
        """Returns a new list of Decimal values with the values of the given sequence rounded to the given precision (default no rounding) and decimal places (default FLOATING_POINT_DECIMALS)."""

        result = []

        if precision is None:
            for val in values:
                result.append(self.__to_decimal(val, decimals))
        else:
            for val in values:
                result.append(self.__round_value(val, precision, decimals))

        return result

    def __world_to_local(self, world_position, local_bounds_object=None):
        """
        Translates the given world space position so it is relative to the geometric center of the given local space bounds.
        If no local_bounds_object is defined, data from bounds_data is used.
        Returns a list of Decimal type local coordinates rounded to eliminate floating point errors.
        """

        if local_bounds_object is not None:
            bounds_min = self.__get_world_min(local_bounds_object)
            dimensions = local_bounds_object.dimensions
        else:
            # Use the bounds object data.
            bounds_min = self.__bounds_data.world_coords_min
            dimensions = self.__bounds_data.dimensions

        local_center = self.__round_values((bounds_min[constants.INDEX_X] + (dimensions[constants.INDEX_X] / Decimal("2.0")),
                                            bounds_min[constants.INDEX_Y] + (dimensions[constants.INDEX_Y] / Decimal("2.0")),
                                            bounds_min[constants.INDEX_Z] + (dimensions[constants.INDEX_Z] / Decimal("2.0"))))

        # If given position is in Decimals do nothing.
        if isinstance(world_position[0], Decimal):
            world = world_position
        else:
            # Otherwise convert to Decimal.
            world = self.__round_values(world_position)

        local = []

        for index, value in enumerate(world):
            local.append(value - local_center[index])

        return self.__round_values(local)

    def __sequence_z_to_plates(self, xyz):
        """
        Performs round_values(sequence) on the given sequence and scales the Z component to match Blockland plates.
        If the given sequence does not have exactly three components (assumed format is (X, Y, Z)) the input is returned unchanged.
        """

        if len(xyz) == 3:
            sequence = self.__round_values(xyz)
            sequence[constants.INDEX_Z] /= constants.PLATE_HEIGHT
            return sequence
        else:
            return xyz

    def __round_to_plate_coordinates(self, coordinates, brick_dimensions):
        """
        Rounds the given sequence of XYZ coordinates to the nearest valid plate coordinates in a brick with the specified dimensions.
        Returns a list of rounded Decimal values.
        """

        result = []
        # 1 plate is 1.0 Blender units wide and deep.
        # Plates can only be 1.0 units long on the X and Y axes.
        # Valid plate positions exist every 0.5 units on odd sized bricks and every 1.0 units on even sized bricks.
        if self.__is_even(brick_dimensions[constants.INDEX_X]):
            result.append(self.__round_value(coordinates[constants.INDEX_X], 1.0))
        else:
            result.append(self.__round_value(coordinates[constants.INDEX_X], 0.5))

        if self.__is_even(brick_dimensions[constants.INDEX_Y]):
            result.append(self.__round_value(coordinates[constants.INDEX_Y], 1.0))
        else:
            result.append(self.__round_value(coordinates[constants.INDEX_Y], 0.5))

        # Round to the nearest full plate height. (Half is rounded up)
        if self.__is_even(brick_dimensions[constants.INDEX_Z] / constants.PLATE_HEIGHT):
            result.append(self.__round_value(coordinates[constants.INDEX_Z], constants.PLATE_HEIGHT))
        else:
            result.append(self.__round_value(coordinates[constants.INDEX_Z], (constants.PLATE_HEIGHT / Decimal("2.0"))))

        return result

    def __sort_quad(self, quad):
        """
        Calculates the section for the given quad within the given bounds.
        The quad section is determined by whether the quad is in the same plane as one the planes defined by the bounds.
        Returns the index of the section name in QUAD_SECTION_ORDER sequence.
        """

        # This function only handles quads so there are always exactly 4 position lists. (One for each vertex.)
        positions = quad[0]

        # Divide all dimension values by 2 to get the local bounding values.
        # The dimensions are in Blender units so Z height needs to be converted to plates.
        local_bounds = self.__sequence_z_to_plates([value / Decimal("2.0") for value in self.__bounds_data.dimensions])

        # Assume omni direction until otherwise proven.
        direction = 6

        # Each position list has exactly 3 values.
        # 0 = X
        # 1 = Y
        # 2 = Z
        for axis in range(3):
            # If the vertex coordinate is the same on an axis for all 4 vertices, this face is parallel to the plane perpendicular to that axis.
            if positions[0][axis] == positions[1][axis] == positions[2][axis] == positions[3][axis]:
                # Is the common value equal to one of the bounding values?
                # I.e. the quad is on the same plane as one of the edges of the brick.
                # Stop searching as soon as the first plane is found.
                # If the vertex coordinates are equal on more than one axis, it means that the quad is either a line (2 axes) or a point (3 axes).

                # Assuming that forward axis is Blender +X (constants.Axis.positive_x).
                # Then in-game the brick north is to the left of the player, which is +Y in Blender.
                # I know it makes no sense.

                # Positive values.
                if positions[0][axis] == local_bounds[axis]:
                    # +X = East
                    if axis == 0:
                        direction = 3
                        break
                    # +Y = North
                    elif axis == 1:
                        direction = 2
                        break
                    # +Z = Top
                    else:
                        direction = 0
                        break

                # Negative values.
                elif positions[0][axis] == -local_bounds[axis]:
                    # -X = West
                    if axis == 0:
                        direction = 5
                        break
                    # -Y = South
                    elif axis == 1:
                        direction = 4
                        break
                    # -Z = Bottom
                    else:
                        direction = 1
                        break
                # Else the quad is not on the same plane with one of the bounding planes = Omni
            # Else the quad is not planar = Omni

        # Top, bottom, and omni are always the same.
        # The initial values are according to +X forward axis.
        if direction <= 1 or direction == 6 or self.__properties.axis_blb_forward == constants.Axis.positive_x:
            return direction

        # Rotate the direction according the defined forward axis.
        elif self.__properties.axis_blb_forward == constants.Axis.positive_y:
            # [2] North -> [3] East: (2 - 2 + 1) % 4 + 2 = 3
            # [5] West -> [2] North: (5 - 2 + 1) % 4 + 2 = 2
            return (direction - 1) % 4 + 2
        elif self.__properties.axis_blb_forward == constants.Axis.negative_x:
            # [2] North -> [4] South: (2 - 2 + 2) % 4 + 2 = 4
            # [4] South -> [2] North
            return direction % 4 + 2
        elif self.__properties.axis_blb_forward == constants.Axis.negative_y:
            # [2] North -> [5] West: (2 - 2 + 3) % 4 + 2 = 5
            # [5] West -> [4] South
            return (direction + 1) % 4 + 2
        # TODO: Does not support Z axis remapping yet.

    def __grid_object_to_volume(self, obj):
        """
        Note: This function requires that it is called after the bounds object has been defined.
        Calculates the brick grid definition index range [min, max[ for each axis from the vertex coordinates of the given object.
        The indices represent a three dimensional volume in the local space of the bounds object where the origin is in the -X +Y +Z corner.
        Returns a tuple in the following format: ( (min_width, max_width), (min_depth, max_depth), (min_height, max_height) )
        Can raise OutOfBoundsException and ZeroSizeException.
        """

        halved_dimensions = [value / Decimal("2.0") for value in self.__bounds_data.dimensions]

        # Find the minimum and maximum coordinates for the brick grid object.
        grid_min = Vector((float("+inf"), float("+inf"), float("+inf")))
        grid_max = Vector((float("-inf"), float("-inf"), float("-inf")))
        self.__record_world_min_max(grid_min, grid_max, obj)

        # Recenter the coordinates to the bounds. (Also rounds the values.)
        grid_min = self.__world_to_local(grid_min)
        grid_max = self.__world_to_local(grid_max)

        # Round coordinates to the nearest plate.
        grid_min = self.__round_to_plate_coordinates(grid_min, self.__bounds_data.dimensions)
        grid_max = self.__round_to_plate_coordinates(grid_max, self.__bounds_data.dimensions)

        if self.__all_within_bounds(grid_min, self.__bounds_data.dimensions) and self.__all_within_bounds(grid_max, self.__bounds_data.dimensions):
            # Convert the coordinates into brick grid sequence indices.

            # Minimum indices.
            if self.__properties.axis_blb_forward == constants.Axis.negative_x or self.__properties.axis_blb_forward == constants.Axis.negative_y:
                # Translate coordinates to negative X axis.
                # -X: Index 0 = front of the brick.
                # -Y: Index 0 = left of the brick.
                grid_min[constants.INDEX_X] = grid_min[constants.INDEX_X] - halved_dimensions[constants.INDEX_X]
            else:
                # Translate coordinates to positive X axis.
                # +X: Index 0 = front of the brick.
                # +Y: Index 0 = left of the brick.
                grid_min[constants.INDEX_X] = grid_min[constants.INDEX_X] + halved_dimensions[constants.INDEX_X]

            if self.__properties.axis_blb_forward == constants.Axis.positive_x or self.__properties.axis_blb_forward == constants.Axis.negative_y:
                # Translate coordinates to negative Y axis.
                # +X: Index 0 = left of the brick.
                # -Y: Index 0 = front of the brick.
                grid_min[constants.INDEX_Y] = grid_min[constants.INDEX_Y] - halved_dimensions[constants.INDEX_Y]
            else:
                # Translate coordinates to positive Y axis.
                # +Y: Index 0 = front of the brick.
                # -X: Index 0 = left of the brick.
                grid_min[constants.INDEX_Y] = grid_min[constants.INDEX_Y] + halved_dimensions[constants.INDEX_Y]

            # Translate coordinates to negative Z axis, height to plates.
            grid_min[constants.INDEX_Z] = (grid_min[constants.INDEX_Z] - halved_dimensions[constants.INDEX_Z]) / constants.PLATE_HEIGHT

            # Maximum indices.
            if self.__properties.axis_blb_forward == constants.Axis.negative_x or self.__properties.axis_blb_forward == constants.Axis.negative_y:
                grid_max[constants.INDEX_X] = grid_max[constants.INDEX_X] - halved_dimensions[constants.INDEX_X]
            else:
                grid_max[constants.INDEX_X] = grid_max[constants.INDEX_X] + halved_dimensions[constants.INDEX_X]

            if self.__properties.axis_blb_forward == constants.Axis.positive_x or self.__properties.axis_blb_forward == constants.Axis.negative_y:
                grid_max[constants.INDEX_Y] = grid_max[constants.INDEX_Y] - halved_dimensions[constants.INDEX_Y]
            else:
                grid_max[constants.INDEX_Y] = grid_max[constants.INDEX_Y] + halved_dimensions[constants.INDEX_Y]

            grid_max[constants.INDEX_Z] = (grid_max[constants.INDEX_Z] - halved_dimensions[constants.INDEX_Z]) / constants.PLATE_HEIGHT

            # Swap min/max Z index and make it positive. Index 0 = top of the brick.
            temp = grid_min[constants.INDEX_Z]
            grid_min[constants.INDEX_Z] = abs(grid_max[constants.INDEX_Z])
            grid_max[constants.INDEX_Z] = abs(temp)

            if self.__properties.axis_blb_forward == constants.Axis.positive_x:
                # Swap min/max depth and make it positive.
                temp = grid_min[constants.INDEX_Y]
                grid_min[constants.INDEX_Y] = abs(grid_max[constants.INDEX_Y])
                grid_max[constants.INDEX_Y] = abs(temp)

                grid_min = common.swizzle(grid_min, "bac")
                grid_max = common.swizzle(grid_max, "bac")
            elif self.__properties.axis_blb_forward == constants.Axis.negative_x:
                # Swap min/max width and make it positive.
                temp = grid_min[constants.INDEX_X]
                grid_min[constants.INDEX_X] = abs(grid_max[constants.INDEX_X])
                grid_max[constants.INDEX_X] = abs(temp)

                grid_min = common.swizzle(grid_min, "bac")
                grid_max = common.swizzle(grid_max, "bac")
            elif self.__properties.axis_blb_forward == constants.Axis.negative_y:
                # Swap min/max depth and make it positive.
                temp = grid_min[constants.INDEX_Y]
                grid_min[constants.INDEX_Y] = abs(grid_max[constants.INDEX_Y])
                grid_max[constants.INDEX_Y] = abs(temp)

                # Swap min/max width and make it positive.
                temp = grid_min[constants.INDEX_X]
                grid_min[constants.INDEX_X] = abs(grid_max[constants.INDEX_X])
                grid_max[constants.INDEX_X] = abs(temp)
            # Else self.__properties.axis_blb_forward == constants.Axis.positive_y: do nothing

            grid_min = self.__force_to_int(grid_min)
            grid_max = self.__force_to_int(grid_max)

            zero_size = False

            # Check for zero size.
            for index, value in enumerate(grid_max):
                if (value - grid_min[index]) == 0:
                    zero_size = True
                    break

            if zero_size:
                logger.error("Brick grid definition object '{}' has zero size on at least one axis. Definition ignored.".format(obj.name))
                raise self.ZeroSizeException()
            else:
                # Return the index ranges as a tuple: ( (min_width, max_width), (min_depth, max_depth), (min_height, max_height) )
                return ((grid_min[constants.INDEX_X], grid_max[constants.INDEX_X]),
                        (grid_min[constants.INDEX_Y], grid_max[constants.INDEX_Y]),
                        (grid_min[constants.INDEX_Z], grid_max[constants.INDEX_Z]))
        else:
            if self.__bounds_data.name is None:
                logger.error("Brick grid definition object '{}' has vertices outside the calculated brick bounds. Definition ignored.".format(obj.name))
            else:
                logger.error("Brick grid definition object '{}' has vertices outside the bounds definition object '{}'. Definition ignored.".format(
                    obj.name, self.__bounds_data.name))
            raise self.OutOfBoundsException()

    def __get_object_sequence(self):
        """Returns the sequence of objects to be exported."""

        objects = []

        # Use selected objects?
        if self.__properties.use_selection:
            logger.info("Exporting selection to BLB.")
            objects = self.__context.selected_objects
            logger.info(logger.build_countable_message("Found ", len(objects), (" object", " objects"), "", "No objects selected."))

        # If user wants to export the whole scene.
        # Or if user wanted to export only the selected objects but nothing was selected.
        # Get all scene objects.
        if len(objects) == 0:
            logger.info("Exporting scene to BLB.")
            objects = self.__context.scene.objects
            logger.info(logger.build_countable_message("Found ", len(objects), (" object", " objects"), "", "Scene has no objects."))

        return objects

    def __process_bounds_object(self, obj):
        """Processes a manually defined bounds object and saves the data to the bounds data and definition data sequences."""

        # Store Blender object and vertex data for processing other definition objects, like collision.

        self.__bounds_data.name = obj.name
        # TODO: Figure out why I'm rounding the dimensions here but not below.
        self.__bounds_data.dimensions = self.__round_values(obj.dimensions)

        # Find the minimum and maximum world coordinates for the bounds object.
        bounds_min = Vector((float("+inf"), float("+inf"), float("+inf")))
        bounds_max = Vector((float("-inf"), float("-inf"), float("-inf")))
        self.__record_world_min_max(bounds_min, bounds_max, obj)

        self.__bounds_data.world_coords_min = self.__round_values(bounds_min)
        self.__bounds_data.world_coords_max = self.__round_values(bounds_max)

        # Store BLB data.

        # Get the dimensions of the Blender object and convert the height to plates.
        bounds_size = self.__sequence_z_to_plates(obj.dimensions)

        # Are the dimensions of the bounds object not integers?
        # TODO: Flip the boolean logic.
        if self.__are_not_ints(bounds_size):
            logger.warning("Defined bounds have a non-integer size {} {} {}, rounding to a precision of {}.".format(bounds_size[constants.INDEX_X],
                                                                                                                    bounds_size[constants.INDEX_Y],
                                                                                                                    bounds_size[constants.INDEX_Z],
                                                                                                                    self.__HUMAN_ERROR))
            for index, value in enumerate(bounds_size):
                # Round to the specified error amount.
                bounds_size[index] = round(self.__HUMAN_ERROR * round(value / self.__HUMAN_ERROR))

        # The value type must be int because you can't have partial plates. Returns a list.
        self.__blb_data.brick_size = self.__force_to_int(bounds_size)
        #self.__bounds_data["brick_size"] = self.__definition_data[constants.BOUNDS_NAME_PREFIX]

    def __calculate_bounds(self):
        """Gets the bounds data from calculated minimum and maximum vertex coordinates and saves the data to the bounds data and definition data sequences."""

        logger.warning("No 'bounds' object found. Automatically calculated brick size may be undesirable.")

        # Get the dimensions defined by the vectors.
        bounds_size = self.__round_values((self.__vec_bounding_box_max[constants.INDEX_X] - self.__vec_bounding_box_min[constants.INDEX_X],
                                           self.__vec_bounding_box_max[constants.INDEX_Y] - self.__vec_bounding_box_min[constants.INDEX_Y],
                                           (self.__vec_bounding_box_max[constants.INDEX_Z] - self.__vec_bounding_box_min[constants.INDEX_Z])))

        self.__bounds_data.name = None
        self.__bounds_data.dimensions = bounds_size

        # The minimum and maximum calculated world coordinates.
        self.__bounds_data.world_coords_min = self.__round_values(self.__vec_bounding_box_min)
        self.__bounds_data.world_coords_max = self.__round_values(self.__vec_bounding_box_max)

        # Convert height to plates.
        bounds_size = self.__sequence_z_to_plates(bounds_size)

        # Are the dimensions of the bounds object not integers?
        if self.__are_not_ints(bounds_size):
            logger.warning("Calculated bounds has a non-integer size {} {} {}, rounding up.".format(bounds_size[constants.INDEX_X],
                                                                                                    bounds_size[constants.INDEX_Y],
                                                                                                    bounds_size[constants.INDEX_Z]))

            # In case height conversion or rounding introduced floating point errors, round up to be on the safe side.
            for index, value in enumerate(bounds_size):
                bounds_size[index] = ceil(value)

        # The value type must be int because you can't have partial plates. Returns a list.
        self.__blb_data.brick_size = self.__force_to_int(bounds_size)
        #self.__bounds_data["brick_size"] = self.__definition_data[constants.BOUNDS_NAME_PREFIX]

    def __process_grid_definitions(self, definition_objects):
        """
        Note: This function requires that it is called after the bounds object has been defined.
        Processes the given brick grid definitions and saves the results to the definition data sequence.
        """

        grid_inside = "x"  # Disallow building inside brick.
        grid_outside = "-"  # Allow building in empty space.
        grid_up = "u"  # Allow placing bricks above this plate.
        grid_down = "d"  # Allow placing bricks below this plate.
        grid_both = "b"  # Allow placing bricks above and below this plate.

        # Brick grid definitions in reverse priority order.
        grid_definitions_priority = (grid_inside,
                                     grid_outside,
                                     grid_up,
                                     grid_down,
                                     grid_both)

        # Make one empty list for each brick grid definition.
        definition_volumes = [[] for i in range(len(constants.GRID_DEF_OBJ_PREFIX_PRIORITY))]
        processed = 0

        for grid_obj in definition_objects:
            try:
                # The first 5 characters of the Blender object name must be the grid definition prefix.
                # Get the index of the definition list.
                # And append the definition data to the list.
                index = constants.GRID_DEF_OBJ_PREFIX_PRIORITY.index(grid_obj.name.lower()[:5])
                definition_volumes[index].append(self.__grid_object_to_volume(grid_obj))
                processed += 1
            except self.OutOfBoundsException:
                # Do nothing, definition is ignored.
                pass
            except self.ZeroSizeException:
                # Do nothing, definition is ignored.
                pass

        # Log messages for brick grid definitions.
        if len(definition_objects) == 0:
            logger.warning("No brick grid definitions found. Automatically generated brick grid may be undesirable.")
        elif len(definition_objects) == 1:
            if processed == 0:
                logger.warning(
                    "{} brick grid definition found but was not processed. Automatically generated brick grid may be undesirable.".format(len(definition_objects)))
            else:
                logger.info("Processed {} of {} brick grid definition.".format(processed, len(definition_objects)))
        else:
            # Found more than one.
            if processed == 0:
                logger.warning(
                    "{} brick grid definitions found but were not processed. Automatically generated brick grid may be undesirable.".format(len(definition_objects)))
            else:
                logger.info("Processed {} of {} brick grid definitions.".format(processed, len(definition_objects)))

        # The brick grid is a special case where I do need to take the custom forward axis already into account when processing the data.
        if self.__properties.axis_blb_forward == constants.Axis.positive_x or self.__properties.axis_blb_forward == constants.Axis.negative_x:
            grid_width = self.__blb_data.brick_size[constants.INDEX_X]
            grid_depth = self.__blb_data.brick_size[constants.INDEX_Y]
        else:
            grid_width = self.__blb_data.brick_size[constants.INDEX_Y]
            grid_depth = self.__blb_data.brick_size[constants.INDEX_X]

        grid_height = self.__blb_data.brick_size[constants.INDEX_Z]

        # Initialize the brick grid with the empty symbol with the dimensions of the brick.
        brick_grid = [[[grid_outside for w in range(grid_width)] for h in range(grid_height)] for d in range(grid_depth)]

        if len(definition_objects) == 0:
            # Write the default brick grid.
            for d in range(grid_depth):
                for h in range(grid_height):
                    is_top = (h == 0)  # Current height is the top of the brick?
                    is_bottom = (h == grid_height - 1)  # Current height is the bottom of the brick?

                    if is_bottom and is_top:
                        symbol = grid_both
                    elif is_bottom:
                        symbol = grid_down
                    elif is_top:
                        symbol = grid_up
                    else:
                        symbol = grid_inside

                    # Create a new list of the width of the grid filled with the selected symbol.
                    # Assign it to the current height.
                    brick_grid[d][h] = [symbol] * grid_width
        else:
            # Write the calculated definition_volumes into the brick grid.
            for index, volumes in enumerate(definition_volumes):
                # Get the symbol for these volumes.
                symbol = grid_definitions_priority[index]
                for volume in volumes:
                    # Modify the grid by adding the symbol to the correct locations.
                    self.__modify_brick_grid(brick_grid, volume, symbol)

        self.__blb_data.brick_grid = brick_grid

    def __process_collision_definitions(self, definition_objects):
        """
        Note: This function requires that it is called after the bounds object has been defined.
        Processes the given collision definitions and saves the results to the definition data sequence.
        """

        processed = 0

        if len(definition_objects) > 10:
            logger.error("{} collision boxes defined but 10 is the maximum. Only the first 10 will be processed.".format(len(definition_objects)))

        for obj in definition_objects:
            # Break the loop as soon as 10 definitions have been processed.
            if processed > 9:
                break

            vert_count = len(obj.data.vertices)

            # At least two vertices are required for a valid bounding box.
            if vert_count < 2:
                logger.error("Collision definition object '{}' has less than 2 vertices. Definition ignored.".format(obj.name))
                # Skip the rest of the loop and return to the beginning.
                continue
            elif vert_count > 8:
                logger.warning(
                    "Collision definition object '{}' has more than 8 vertices suggesting a shape other than a cuboid. Bounding box of this mesh will be used.".format(obj.name))
                # The mesh is still valid.

            # Find the minimum and maximum coordinates for the collision object.
            col_min = Vector((float("+inf"), float("+inf"), float("+inf")))
            col_max = Vector((float("-inf"), float("-inf"), float("-inf")))
            self.__record_world_min_max(col_min, col_max, obj)

            # Recenter the coordinates to the bounds. (Also rounds the values.)
            col_min = self.__world_to_local(col_min)
            col_max = self.__world_to_local(col_max)

            if self.__all_within_bounds(col_min, self.__bounds_data.dimensions) and self.__all_within_bounds(col_max, self.__bounds_data.dimensions):
                zero_size = False

                # Check for zero size.
                for index, value in enumerate(col_max):
                    if (value - col_min[index]) == 0:
                        zero_size = True
                        break

                if zero_size:
                    logger.error("Collision definition object '{}' has zero size on at least one axis. Definition ignored.".format(obj.name))
                    # Skip the rest of the loop.
                    continue

                center = []
                dimensions = []

                # Find the center coordinates and dimensions of the cuboid.
                for index, value in enumerate(col_max):
                    center.append((value + col_min[index]) / Decimal("2.0"))
                    dimensions.append(value - col_min[index])

                processed += 1

                # Add the center and dimensions to the definition data as a tuple.
                # The coordinates and dimensions are in plates.
                self.__blb_data.collision.append((self.__sequence_z_to_plates(center), self.__sequence_z_to_plates(dimensions)))
            else:
                if self.__bounds_data.name is None:
                    logger.error("Collision definition object '{}' has vertices outside the calculated brick bounds. Definition ignored.".format(obj.name))
                else:
                    logger.error("Collision definition object '{}' has vertices outside the bounds definition object '{}'. Definition ignored.".format(
                        obj.name, self.__bounds_data.name))

        # Log messages for collision definitions.
        if len(definition_objects) == 0:
            logger.warning("No collision definitions found. Default generated collision may be undesirable.")
        elif len(definition_objects) == 1:
            if processed == 0:
                logger.warning(
                    "{} collision definition found but was not processed. Default generated collision may be undesirable.".format(len(definition_objects)))
            else:
                logger.info("Processed {} of {} collision definition.".format(processed, len(definition_objects)))
        else:
            # Found more than one.
            if processed == 0:
                logger.warning(
                    "{} collision definitions found but were not processed. Default generated collision may be undesirable.".format(len(definition_objects)))
            else:
                logger.info("Processed {} of {} collision definitions.".format(processed, len(definition_objects)))

    def __process_definition_objects(self, objects):
        """"Processes all definition objects that are not exported as a 3D model but will affect the brick properties.

        Processed definition objects:
            - bounds
            - brick grid
            - collision

        If no bounds object is found, the brick bounds will be automatically calculated using the minimum and maximum coordinates of the found mesh objects.

        Args:
            objects (sequence of Blender objects): The sequence of objects to be processed.

        Returns:
            A sequence of mesh objects that will be exported as visible 3D models.
        """

        brick_grid_objects = []
        collision_objects = []
        mesh_objects = []

        # Loop through all objects in the sequence.
        # The objects in the sequence are sorted so that the oldest created object is last.
        # Process the objects from oldest to newest.
        for obj in reversed(objects):
            # Ignore non-mesh objects
            if obj.type != "MESH":
                if obj.name.lower().startswith(constants.BOUNDS_NAME_PREFIX):
                    logger.warning("Object '{}' cannot be used to define bounds, must be a mesh.".format(obj.name))
                elif obj.name.lower().startswith(constants.GRID_DEF_OBJ_PREFIX_PRIORITY):
                    logger.warning("Object '{}' cannot be used to define brick grid, must be a mesh.".format(obj.name))
                elif obj.name.lower().startswith(constants.COLLISION_PREFIX):
                    logger.warning("Object '{}' cannot be used to define collision, must be a mesh.".format(obj.name))

                continue

            # Is the current object a bounds definition object?
            elif obj.name.lower().startswith(constants.BOUNDS_NAME_PREFIX):
                if self.__bounds_data.name is None:
                    self.__process_bounds_object(obj)
                    logger.info("Defined brick size in plates: {} wide {} deep {} tall".format(self.__blb_data.brick_size[constants.INDEX_X],
                                                                                               self.__blb_data.brick_size[constants.INDEX_Y],
                                                                                               self.__blb_data.brick_size[constants.INDEX_Z]))
                else:
                    logger.warning("Multiple bounds definitions found. '{}' definition ignored.".format(obj.name))
                    continue

            # Is the current object a brick grid definition object?
            elif obj.name.lower().startswith(constants.GRID_DEF_OBJ_PREFIX_PRIORITY):
                # Brick grid definition objects cannot be processed until after the bounds have been defined.
                brick_grid_objects.append(obj)

            # Is the current object a collision definition object?
            elif obj.name.lower().startswith(constants.COLLISION_PREFIX):
                # Collision definition objects cannot be processed until after the bounds have been defined.
                collision_objects.append(obj)

            # Else the object must be a regular mesh that is exported as a 3D model.
            else:
                # Record bounds for checking against the defined brick bounds or if none was specified, for calculating the bounds.
                self.__record_world_min_max(self.__vec_bounding_box_min, self.__vec_bounding_box_max, obj)
                mesh_objects.append(obj)

        # No manually created bounds object was found, calculate brick bounds based on the minimum and maximum recorded mesh vertex position.
        if self.__bounds_data.name is None:
            self.__calculate_bounds()
            logger.info("Calculated brick size in plates: {} wide {} deep {} tall".format(self.__blb_data.brick_size[constants.INDEX_X],
                                                                                          self.__blb_data.brick_size[constants.INDEX_Y],
                                                                                          self.__blb_data.brick_size[constants.INDEX_Z]))

        # Process brick grid and collision definitions now that a bounds definition exists.
        self.__process_grid_definitions(brick_grid_objects)
        self.__process_collision_definitions(collision_objects)

        # Return the meshes to be exported.
        return mesh_objects

    def __process_coverage(self):
        """Calculates the coverage data if the user has defined so in the properties.

        Returns:
            A sequence of BLB coverage data.
        """
        if self.__properties.calculate_coverage:
            calculate_side = common.BrickSides(self.__properties.coverage_top_calculate,
                                               self.__properties.coverage_bottom_calculate,
                                               self.__properties.coverage_north_calculate,
                                               self.__properties.coverage_east_calculate,
                                               self.__properties.coverage_south_calculate,
                                               self.__properties.coverage_west_calculate)

            hide_adjacent = common.BrickSides(self.__properties.coverage_top_hide,
                                              self.__properties.coverage_bottom_hide,
                                              self.__properties.coverage_north_hide,
                                              self.__properties.coverage_east_hide,
                                              self.__properties.coverage_south_hide,
                                              self.__properties.coverage_west_hide)

            return calculate_coverage(self.__blb_data.brick_size,
                                      calculate_side,
                                      hide_adjacent,
                                      self.__properties.axis_blb_forward)
        else:
            return calculate_coverage()

    def __process_mesh_data(self, meshes):
        """Returns a tuple of mesh data sorted into sections."""

        quads = []
        count_tris = 0
        count_ngon = 0

        for obj in meshes:
            logger.info("Exporting mesh: {}".format(obj.name))

            current_data = obj.data

            # UV layers exist?
            if current_data.uv_layers:
                if len(current_data.uv_layers) > 1:
                    logger.warning("Mesh '{}' has {} UV layers, using the 1st.".format(obj.name, len(current_data.uv_layers)))

                uv_data = current_data.uv_layers[0].data
            else:
                uv_data = None

            # Faces.
            for poly in current_data.polygons:
                # Vertex positions
                if poly.loop_total == 4:
                    # Quad.
                    loop_indices = tuple(poly.loop_indices)
                elif poly.loop_total == 3:
                    # Tri.
                    loop_indices = tuple(poly.loop_indices) + (poly.loop_start,)
                    count_tris += 1
                else:
                    # N-gon.
                    count_ngon += 1
                    continue

                positions = []

                # Reverse the loop_indices tuple. (Blender seems to keep opposite winding order.)
                for index in reversed(loop_indices):
                    # Get the world position from the index. (This rounds it and converts the height to plates.)
                    # Center the position to the current bounds object.
                    positions.append(self.__sequence_z_to_plates(self.__world_to_local(self.__index_to_position(obj, index))))

                # FIXME: Object rotation affects normals.

                # Normals.
                if poly.use_smooth:
                    # Smooth shading.
                    # For every vertex index in the loop_indices, calculate the vertex normal and add it to the list.
                    normals = [self.__vertex_index_to_normal(obj, index) for index in reversed(loop_indices)]
                else:
                    # No smooth shading, every vertex in this loop has the same normal.
                    normals = (poly.normal,) * 4

                # UVs
                if uv_data:
                    # Get the UV coordinate for every vertex in the face loop.
                    uvs = [uv_data[index].uv for index in reversed(loop_indices)]
                else:
                    # No UVs present, use the defaults.
                    # These UV coordinates with the SIDE texture lead to a blank textureless face.
                    uvs = (Vector((0.5, 0.5)),) * 4

                # Colors
                colors = None

                # Texture
                if current_data.materials and current_data.materials[poly.material_index] is not None:
                    texture = current_data.materials[poly.material_index].name.upper()
                else:
                    # If no texture is specified, use the SIDE texture as it allows for blank brick textures.
                    texture = "SIDE"

                quads.append((positions, normals, uvs, colors, texture))

        if count_tris > 0:
            logger.warning("{} triangles degenerated to quads.".format(count_tris))

        if count_ngon > 0:
            logger.warning("{} n-gons skipped.".format(count_ngon))

        # Create an empty list for each quad section.
        # This is my workaround to making a sort of dictionary where the keys are in insertion order.
        # The quads must be written in a specific order.
        sorted_quads = tuple([[] for i in range(len(constants.QUAD_SECTION_ORDER))])

        # Sort quads into sections.
        for quad in quads:
            # Calculate the section name the quad belongs to.
            # Get the index of that section name in the QUAD_SECTION_ORDER list.
            # Append the quad data to the list in the tuple at that index.
            sorted_quads[self.__sort_quad(quad)].append(quad)

        return sorted_quads

    def process(self):
        """Processes the Blender data specified when this processor was created.

        Performs the following actions:
            1. Determines which Blender objects will be processed.
            2. Processes the definition objects (collision, brick grid, and bounds) that will affect how the brick works but will not be visible.
            3. Calculates the coverage data based on the brick bounds.
            4. Processes the visible mesh data into the correct format for writing into a BLB file.

        Returns:
            - A tuple where the first element is the sorted quad data and the second is the BLB definitions.
            - None if there is no Blender data to export.
        """

        # Determine which objects to process.
        object_sequence = self.__get_object_sequence()

        if len(object_sequence) > 0:
            # Process the definition objects first and separate the visible meshes from the object sequence.
            # This is done in a single function because it is faster, no need to iterate over the same sequence twice.
            meshes = self.__process_definition_objects(object_sequence)

            self.__blb_data.coverage = self.__process_coverage()
            self.__blb_data.quads = self.__process_mesh_data(meshes)

            return self.__blb_data
        else:
            logger.error("Nothing to export.")
            return None
