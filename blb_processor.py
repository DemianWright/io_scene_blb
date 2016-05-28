'''
A module for processing Blender data into the BLB file format for writing.

@author: Demian Wright
'''

from mathutils import Vector
from math import ceil
from decimal import Decimal, Context, setcontext, ROUND_HALF_UP

# Blender requires imports from ".".
from . import logger, common, constants

# Number of decimal places to round floating point numbers.
FLOATING_POINT_DECIMALS = 6
FLOATING_POINT_PRECISION = Decimal("0.000001")

# Set the Decimal number context: 6 decimal points and 0.5 is rounded up.
setcontext(Context(prec=FLOATING_POINT_DECIMALS, rounding=ROUND_HALF_UP))

class BLBProcessor(object):
    """A class that handles processing Blender data and preparing it for writing to a BLB file."""

    class OutOfBoundsException(Exception):
        """An exception thrown when a vertex position is outside of brick bounds."""
        pass

    class ZeroSizeException(Exception):
        """An exception thrown when a definition object has zero brick size on at least one axis."""
        pass

    # Error allowed for manually created definition objects. Used for rounding vertex positions to the brick grid.
    __HUMAN_ERROR = Decimal("0.1")

    __PLATE_HEIGHT = Decimal("0.4")  # A Blockland brick (plate) with dimensions 1 x 1 x 1 is equal to 1.0 x 1.0 x 0.4 Blender units (X,Y,Z)

    def __init__(self, context, properties):
        """Initializes the BLBProcessor with the specified properties."""
        self.__context = context
        self.__properties = properties

        self.__grid_inside = "x" # Disallow building inside brick.
        self.__grid_outside = "-"  # Allow building in empty space.
        self.__grid_up = "u" # Allow placing bricks above this plate.
        self.__grid_down = "d" # Allow placing bricks below this plate.
        self.__grid_both = "b" # Allow placing bricks above and below this plate.

        # Brick grid definition object name prefixes in reverse priority order.
        self.__grid_def_obj_prefix_priority = ("gridx",
                                               "grid-",
                                               "gridu",
                                               "gridd",
                                               "gridb")

        # Brick grid definitions in reverse priority order.
        self.__grid_definitions_priority = (self.__grid_inside,
                                            self.__grid_outside,
                                            self.__grid_up,
                                            self.__grid_down,
                                            self.__grid_both)

        self.__bounds_data = {"name": None,
                              "brick_size": [],
                              "dimensions": [],
                              "world_coords_min": [],
                              "world_coords_max": []}

        self.__definition_data = {constants.BOUNDS_NAME_PREFIX: [],
                                  constants.COLLISION_PREFIX: [],
                                  "brickgrid": [],
                                  "coverage": []}

        self.__vec_bounding_box_min = Vector((float("+inf"), float("+inf"), float("+inf")))
        self.__vec_bounding_box_max = Vector((float("-inf"), float("-inf"), float("-inf")))

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
            if val != int(val): # TODO: Fix OverflowError & crash where nothing is selected and exporting only selection.
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
    def __set_world_min_max(cls, sequence_min, sequence_max, obj):
        """Updates the given sequences by assigning the minimum and maximum world space coordinates of the given object to the minimum and maximum sequences respectively."""

        for vert in obj.data.vertices:
            coord = obj.matrix_world * vert.co

            sequence_min[constants.INDEX_X] = min(sequence_min[constants.INDEX_X], coord[constants.INDEX_X])
            sequence_min[constants.INDEX_Y] = min(sequence_min[constants.INDEX_Y], coord[constants.INDEX_Y])
            sequence_min[constants.INDEX_Z] = min(sequence_min[constants.INDEX_Z], coord[constants.INDEX_Z])

            sequence_max[constants.INDEX_X] = max(sequence_max[constants.INDEX_X], coord[constants.INDEX_X])
            sequence_max[constants.INDEX_Y] = max(sequence_max[constants.INDEX_Y], coord[constants.INDEX_Y])
            sequence_max[constants.INDEX_Z] = max(sequence_max[constants.INDEX_Z], coord[constants.INDEX_Z])

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
            bounds_min = self.__bounds_data["world_coords_min"]
            dimensions = self.__bounds_data["dimensions"]

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
            sequence[constants.INDEX_Z] /= self.__PLATE_HEIGHT
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
        if self.__is_even(brick_dimensions[constants.INDEX_Z] / self.__PLATE_HEIGHT):
            result.append(self.__round_value(coordinates[constants.INDEX_Z], self.__PLATE_HEIGHT))
        else:
            result.append(self.__round_value(coordinates[constants.INDEX_Z], (self.__PLATE_HEIGHT / Decimal("2.0"))))

        return result

    def __sort_quad(self, quad, bounds_data):
        """
        Calculates the section for the given quad within the given bounds.
        The quad section is determined by whether the quad is in the same plane as one the planes defined by the bounds.
        Returns the index of the section name in QUAD_SECTION_ORDER sequence.
        """

        # This function only handles quads so there are always exactly 4 position lists. (One for each vertex.)
        positions = quad[0]

        # Divide all dimension values by 2 to get the local bounding values.
        # The dimensions are in Blender units so Z height needs to be converted to plates.
        local_bounds = self.__sequence_z_to_plates([value / Decimal("2.0") for value in bounds_data["dimensions"]])

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

                # Assuming that forward axis is Blender +X ("POSITIVE_X").
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
        # The initial values are according to POSITIVE_X forward axis.
        if direction <= 1 or direction == 6 or self.__properties.axis_blb_forward == "POSITIVE_X":
            return direction

        # Rotate the direction according the defined forward axis.
        elif self.__properties.axis_blb_forward == "POSITIVE_Y":
            # [2] North -> [3] East: (2 - 2 + 1) % 4 + 2 = 3
            # [5] West -> [2] North: (5 - 2 + 1) % 4 + 2 = 2
            return (direction - 1) % 4 + 2
        elif self.__properties.axis_blb_forward == "NEGATIVE_X":
            # [2] North -> [4] South: (2 - 2 + 2) % 4 + 2 = 4
            # [4] South -> [2] North
            return direction % 4 + 2
        elif self.__properties.axis_blb_forward == "NEGATIVE_Y":
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

        halved_dimensions = [value / Decimal("2.0") for value in self.__bounds_data["dimensions"]]

        # Find the minimum and maximum coordinates for the brick grid object.
        grid_min = Vector((float("+inf"), float("+inf"), float("+inf")))
        grid_max = Vector((float("-inf"), float("-inf"), float("-inf")))
        self.__set_world_min_max(grid_min, grid_max, obj)

        # Recenter the coordinates to the bounds. (Also rounds the values.)
        grid_min = self.__world_to_local(grid_min)
        grid_max = self.__world_to_local(grid_max)

        # Round coordinates to the nearest plate.
        grid_min = self.__round_to_plate_coordinates(grid_min, self.__bounds_data["dimensions"])
        grid_max = self.__round_to_plate_coordinates(grid_max, self.__bounds_data["dimensions"])

        if self.__all_within_bounds(grid_min, self.__bounds_data["dimensions"]) and self.__all_within_bounds(grid_max, self.__bounds_data["dimensions"]):
            # Convert the coordinates into brick grid sequence indices.

            # Minimum indices.
            if self.__properties.axis_blb_forward == "NEGATIVE_X" or self.__properties.axis_blb_forward == "NEGATIVE_Y":
                # Translate coordinates to negative X axis.
                # NEGATIVE_X: Index 0 = front of the brick.
                # NEGATIVE_Y: Index 0 = left of the brick.
                grid_min[constants.INDEX_X] = grid_min[constants.INDEX_X] - halved_dimensions[constants.INDEX_X]
            else:
                # Translate coordinates to positive X axis.
                # POSITIVE_X: Index 0 = front of the brick.
                # POSITIVE_Y: Index 0 = left of the brick.
                grid_min[constants.INDEX_X] = grid_min[constants.INDEX_X] + halved_dimensions[constants.INDEX_X]

            if self.__properties.axis_blb_forward == "POSITIVE_X" or self.__properties.axis_blb_forward == "NEGATIVE_Y":
                # Translate coordinates to negative Y axis.
                # POSITIVE_X: Index 0 = left of the brick.
                # NEGATIVE_Y: Index 0 = front of the brick.
                grid_min[constants.INDEX_Y] = grid_min[constants.INDEX_Y] - halved_dimensions[constants.INDEX_Y]
            else:
                # Translate coordinates to positive Y axis.
                # POSITIVE_Y: Index 0 = front of the brick.
                # NEGATIVE_X: Index 0 = left of the brick.
                grid_min[constants.INDEX_Y] = grid_min[constants.INDEX_Y] + halved_dimensions[constants.INDEX_Y]

            grid_min[constants.INDEX_Z] = (grid_min[constants.INDEX_Z] - halved_dimensions[constants.INDEX_Z]) / self.__PLATE_HEIGHT  # Translate coordinates to negative Z axis, height to plates.

            # Maximum indices.
            if self.__properties.axis_blb_forward == "NEGATIVE_X" or self.__properties.axis_blb_forward == "NEGATIVE_Y":
                grid_max[constants.INDEX_X] = grid_max[constants.INDEX_X] - halved_dimensions[constants.INDEX_X]
            else:
                grid_max[constants.INDEX_X] = grid_max[constants.INDEX_X] + halved_dimensions[constants.INDEX_X]

            if self.__properties.axis_blb_forward == "POSITIVE_X" or self.__properties.axis_blb_forward == "NEGATIVE_Y":
                grid_max[constants.INDEX_Y] = grid_max[constants.INDEX_Y] - halved_dimensions[constants.INDEX_Y]
            else:
                grid_max[constants.INDEX_Y] = grid_max[constants.INDEX_Y] + halved_dimensions[constants.INDEX_Y]

            grid_max[constants.INDEX_Z] = (grid_max[constants.INDEX_Z] - halved_dimensions[constants.INDEX_Z]) / self.__PLATE_HEIGHT

            # Swap min/max Z index and make it positive. Index 0 = top of the brick.
            temp = grid_min[constants.INDEX_Z]
            grid_min[constants.INDEX_Z] = abs(grid_max[constants.INDEX_Z])
            grid_max[constants.INDEX_Z] = abs(temp)

            if self.__properties.axis_blb_forward == "POSITIVE_X":
                # Swap min/max depth and make it positive.
                temp = grid_min[constants.INDEX_Y]
                grid_min[constants.INDEX_Y] = abs(grid_max[constants.INDEX_Y])
                grid_max[constants.INDEX_Y] = abs(temp)

                grid_min = common.swizzle(grid_min, "bac")
                grid_max = common.swizzle(grid_max, "bac")
            elif self.__properties.axis_blb_forward == "NEGATIVE_X":
                # Swap min/max width and make it positive.
                temp = grid_min[constants.INDEX_X]
                grid_min[constants.INDEX_X] = abs(grid_max[constants.INDEX_X])
                grid_max[constants.INDEX_X] = abs(temp)

                grid_min = common.swizzle(grid_min, "bac")
                grid_max = common.swizzle(grid_max, "bac")
            elif self.__properties.axis_blb_forward == "NEGATIVE_Y":
                # Swap min/max depth and make it positive.
                temp = grid_min[constants.INDEX_Y]
                grid_min[constants.INDEX_Y] = abs(grid_max[constants.INDEX_Y])
                grid_max[constants.INDEX_Y] = abs(temp)

                # Swap min/max width and make it positive.
                temp = grid_min[constants.INDEX_X]
                grid_min[constants.INDEX_X] = abs(grid_max[constants.INDEX_X])
                grid_max[constants.INDEX_X] = abs(temp)
            # Else self.__properties.axis_blb_forward == "POSITIVE_Y": do nothing

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
            if self.__bounds_data["name"] is None:
                logger.error("Brick grid definition object '{}' has vertices outside the calculated brick bounds. Definition ignored.".format(obj.name))
            else:
                logger.error("Brick grid definition object '{}' has vertices outside the bounds definition object '{}'. Definition ignored.".format(obj.name, self.__bounds_data["name"]))
            raise self.OutOfBoundsException()

    def __get_object_sequence(self):
        """Returns the sequence of objects to use when exporting."""

        # Use selected objects?
        if self.__properties.use_selection:
            logger.info("Exporting selection to BLB.")
            objects = self.__context.selected_objects

            object_count = len(objects)

            if object_count == 0:
                logger.info("No objects selected.")
            else:
                if object_count == 1:
                    logger.info("Found {} object.".format(len(objects)))
                else:
                    logger.info("Found {} objects.".format(len(objects)))


        # Get all scene objects.
        if not self.__properties.use_selection or (self.__properties.use_selection and object_count == 0):
            logger.info("Exporting scene to BLB.")
            objects = self.__context.scene.objects

            object_count = len(objects)

            if object_count == 0:
                logger.info("No objects in the scene.")
            else:
                if object_count == 1:
                    logger.info("Found {} object.".format(len(objects)))
                else:
                    logger.info("Found {} objects.".format(len(objects)))

        return objects

    def __process_bounds_object(self, obj):
        """Processes a manually defined bounds object and saves the data to the bounds data and definition data sequences."""

        self.__bounds_data["name"] = obj.name
        self.__bounds_data["dimensions"] = self.__round_values(obj.dimensions)

        # Find the minimum and maximum world coordinates for the bounds object.
        bounds_min = Vector((float("+inf"), float("+inf"), float("+inf")))
        bounds_max = Vector((float("-inf"), float("-inf"), float("-inf")))
        self.__set_world_min_max(bounds_min, bounds_max, obj)

        self.__bounds_data["world_coords_min"] = self.__round_values(bounds_min)
        self.__bounds_data["world_coords_max"] = self.__round_values(bounds_max)

        # Get the dimensions of the Blender object and convert the height to plates.
        bounds_size = self.__sequence_z_to_plates(obj.dimensions)

        # Are the dimensions of the bounds object not integers?
        if self.__are_not_ints(bounds_size):
            logger.warning("Defined bounds has a non-integer size {} {} {}, rounding to a precision of {}.".format(bounds_size[constants.INDEX_X],
                                                                                                                   bounds_size[constants.INDEX_Y],
                                                                                                                   bounds_size[constants.INDEX_Z],
                                                                                                                   self.__HUMAN_ERROR))
            for index, value in enumerate(bounds_size):
                # Round to the specified error amount and force to int.
                bounds_size[index] = round(self.__HUMAN_ERROR * round(value / self.__HUMAN_ERROR))

        # The value type must be int because you can't have partial plates. Returns a list.
        self.__definition_data[constants.BOUNDS_NAME_PREFIX] = self.__force_to_int(bounds_size)
        self.__bounds_data["brick_size"] = self.__definition_data[constants.BOUNDS_NAME_PREFIX]

    def __calculate_bounds(self):
        """Gets the bounds data from calculated minimum and maximum vertex coordinates and saves the data to the bounds data and definition data sequences."""

        logger.warning("No 'bounds' object found. Automatically calculated brick size may be undesirable.")

        # Get the dimensions defined by the vectors.
        bounds_size = self.__round_values((self.__vec_bounding_box_max[constants.INDEX_X] - self.__vec_bounding_box_min[constants.INDEX_X],
                                           self.__vec_bounding_box_max[constants.INDEX_Y] - self.__vec_bounding_box_min[constants.INDEX_Y],
                                           (self.__vec_bounding_box_max[constants.INDEX_Z] - self.__vec_bounding_box_min[constants.INDEX_Z])))

        self.__bounds_data["name"] = None
        self.__bounds_data["dimensions"] = bounds_size

        # The minimum and maximum calculated world coordinates.
        self.__bounds_data["world_coords_min"] = self.__round_values(self.__vec_bounding_box_min)
        self.__bounds_data["world_coords_max"] = self.__round_values(self.__vec_bounding_box_max)

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
        self.__definition_data[constants.BOUNDS_NAME_PREFIX] = self.__force_to_int(bounds_size)
        self.__bounds_data["brick_size"] = self.__definition_data[constants.BOUNDS_NAME_PREFIX]

    def __process_grid_definitions(self, definition_objects):
        """
        Note: This function requires that it is called after the bounds object has been defined.
        Processes the given brick grid definitions and saves the results to the definition data sequence.
        """

        # Make one empty list for each brick grid definition.
        definition_volumes = [[] for i in range(len(self.__grid_def_obj_prefix_priority))]
        processed = 0

        for grid_obj in definition_objects:
            try:
                # The first 5 characters of the Blender object name must be the grid definition prefix.
                # Get the index of the definition list.
                # And append the definition data to the list.
                index = self.__grid_def_obj_prefix_priority.index(grid_obj.name.lower()[:5])
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
                logger.warning("{} brick grid definition found but was not processed. Automatically generated brick grid may be undesirable.".format(len(definition_objects)))
            else:
                logger.info("Processed {} of {} brick grid definition.".format(processed, len(definition_objects)))
        else:
            # Found more than one.
            if processed == 0:
                logger.warning("{} brick grid definitions found but were not processed. Automatically generated brick grid may be undesirable.".format(len(definition_objects)))
            else:
                logger.info("Processed {} of {} brick grid definitions.".format(processed, len(definition_objects)))

        # The brick grid is a special case where I do need to take the custom forward axis already into account when processing the data.
        if self.__properties.axis_blb_forward == "POSITIVE_X" or self.__properties.axis_blb_forward == "NEGATIVE_X":
            grid_width = self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_X]
            grid_depth = self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_Y]
        else:
            grid_width = self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_Y]
            grid_depth = self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_X]

        grid_height = self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_Z]

        # Initialize the brick grid with the empty symbol with the dimensions of the brick.
        brick_grid = [[[self.__grid_outside for w in range(grid_width)] for h in range(grid_height)] for d in range(grid_depth)]

        if len(definition_objects) == 0:
            # Write the default brick grid.
            for d in range(grid_depth):
                for h in range(grid_height):
                    is_top = (h == 0) # Current height is the top of the brick?
                    is_bottom = (h == grid_height - 1) # Current height is the bottom of the brick?

                    if is_bottom and is_top:
                        symbol = self.__grid_both
                    elif is_bottom:
                        symbol = self.__grid_down
                    elif is_top:
                        symbol = self.__grid_up
                    else:
                        symbol = self.__grid_inside

                    # Create a new list of the width of the grid filled with the selected symbol.
                    # Assign it to the current height.
                    brick_grid[d][h] = [symbol] * grid_width
        else:
            # Write the calculated definition_volumes into the brick grid.
            for index, volumes in enumerate(definition_volumes):
                # Get the symbol for these volumes.
                symbol = self.__grid_definitions_priority[index]
                for volume in volumes:
                    # Modify the grid by adding the symbol to the correct locations.
                    self.__modify_brick_grid(brick_grid, volume, symbol)

        self.__definition_data["brickgrid"] = brick_grid

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
                logger.warning("Collision definition object '{}' has more than 8 vertices suggesting a shape other than a cuboid. Bounding box of this mesh will be used.".format(obj.name))
                # The mesh is still valid.

            # Find the minimum and maximum coordinates for the collision object.
            col_min = Vector((float("+inf"), float("+inf"), float("+inf")))
            col_max = Vector((float("-inf"), float("-inf"), float("-inf")))
            self.__set_world_min_max(col_min, col_max, obj)

            # Recenter the coordinates to the bounds. (Also rounds the values.)
            col_min = self.__world_to_local(col_min)
            col_max = self.__world_to_local(col_max)

            if self.__all_within_bounds(col_min, self.__bounds_data["dimensions"]) and self.__all_within_bounds(col_max, self.__bounds_data["dimensions"]):
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
                self.__definition_data[constants.COLLISION_PREFIX].append((self.__sequence_z_to_plates(center), self.__sequence_z_to_plates(dimensions)))
            else:
                if self.__bounds_data["name"] is None:
                    logger.error("Collision definition object '{}' has vertices outside the calculated brick bounds. Definition ignored.".format(obj.name))
                else:
                    logger.error("Collision definition object '{}' has vertices outside the bounds definition object '{}'. Definition ignored.".format(obj.name, self.__bounds_data["name"]))

        # Log messages for collision definitions.
        if len(definition_objects) == 0:
            logger.warning("No collision definitions found. Default generated collision may be undesirable.")
        elif len(definition_objects) == 1:
            if processed == 0:
                logger.warning("{} collision definition found but was not processed. Default generated collision may be undesirable.".format(len(definition_objects)))
            else:
                logger.info("Processed {} of {} collision definition.".format(processed, len(definition_objects)))
        else:
            # Found more than one.
            if processed == 0:
                logger.warning("{} collision definitions found but were not processed. Default generated collision may be undesirable.".format(len(definition_objects)))
            else:
                logger.info("Processed {} of {} collision definitions.".format(processed, len(definition_objects)))

    def __process_definition_objects(self, objects):
        """"
        Processes all non-visible definition objects.
        Returns a sequence of meshes (non-definition objects) that will be exported as visible 3D models.
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
                continue

            # Is the current object the bounds definition object?
            elif obj.name.lower().startswith(constants.BOUNDS_NAME_PREFIX):
                if self.__bounds_data["name"] is None:
                    self.__process_bounds_object(obj)
                    logger.info("Defined brick size in plates: {} wide {} deep {} tall".format(self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_X],
                                                                                               self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_Y],
                                                                                               self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_Z]))
                else:
                    logger.warning("Multiple bounds definitions found. {} definition ignored.".format(obj.name))

            # Is the current object a brick grid definition object?
            elif obj.name.lower().startswith(self.__grid_def_obj_prefix_priority):
                # Brick grid definition objects cannot be processed until after the bounds have been defined.
                # Store for later use.
                brick_grid_objects.append(obj)

            # Is the current object a collision definition object?
            elif obj.name.lower().startswith(constants.COLLISION_PREFIX):
                # Collision definition objects cannot be processed until after the bounds have been defined.
                # Store for later use.
                collision_objects.append(obj)

            # Thus the object must be a regular mesh that is exported as a 3D model.
            else:
                # Record bounds.
                self.__set_world_min_max(self.__vec_bounding_box_min, self.__vec_bounding_box_max, obj)

                # And store for later use.
                mesh_objects.append(obj)

        # No manually created bounds object was found, calculate brick size according to the combined minimum and maximum vertex positions of all processed meshes.
        if len(self.__definition_data[constants.BOUNDS_NAME_PREFIX]) == 0:
            self.__calculate_bounds()
            logger.info("Calculated brick size in plates: {} wide {} deep {} tall".format(self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_X],
                                                                                          self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_Y],
                                                                                          self.__definition_data[constants.BOUNDS_NAME_PREFIX][constants.INDEX_Z]))
        # Process brick grid and collision definitions now that a bounds definition exists.
        self.__process_grid_definitions(brick_grid_objects)
        self.__process_collision_definitions(collision_objects)

        # Return the meshes to be exported to be processed elsewhere.
        return mesh_objects

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
            sorted_quads[self.__sort_quad(quad, self.__bounds_data)].append(quad)

        return sorted_quads

    def __calculate_coverage(self):
        """Calculates the coverage based on the properties and the brick bounds and saves the data to the definition data."""

        coverage = []

        # Calculate coverage?
        if self.__properties.calculate_coverage:
            # Get the brick bounds in plates.
            dimensions = self.__definition_data[constants.BOUNDS_NAME_PREFIX]

            # Assuming forward axis is +X.

            # Top: +Z
            if self.__properties.coverage_top_calculate:
                # Calculate the area of the top face.
                area = dimensions[constants.INDEX_X] * dimensions[constants.INDEX_Y]
            else:
                area = 9999

            # Hide adjacent face: True/False
            coverage.append((self.__properties.coverage_top_hide, area))

            # Bottom: -Z
            if self.__properties.coverage_bottom_calculate:
                area = dimensions[constants.INDEX_X] * dimensions[constants.INDEX_Y]
            else:
                area = 9999
            coverage.append((self.__properties.coverage_bottom_hide, area))

            # North: +X
            if self.__properties.coverage_north_calculate:
                area = dimensions[constants.INDEX_X] * dimensions[constants.INDEX_Z]
            else:
                area = 9999
            coverage.append((self.__properties.coverage_north_hide, area))

            # East: -Y
            if self.__properties.coverage_east_calculate:
                area = dimensions[constants.INDEX_Y] * dimensions[constants.INDEX_Z]
            else:
                area = 9999
            coverage.append((self.__properties.coverage_east_hide, area))

            # South: -X
            if self.__properties.coverage_south_calculate:
                area = dimensions[constants.INDEX_X] * dimensions[constants.INDEX_Z]
            else:
                area = 9999
            coverage.append((self.__properties.coverage_south_hide, area))

            # West: +Y
            if self.__properties.coverage_west_calculate:
                area = dimensions[constants.INDEX_Y] * dimensions[constants.INDEX_Z]
            else:
                area = 9999
            coverage.append((self.__properties.coverage_west_hide, area))

            # Swizzle the coverage values around according to the defined forward axis.
            # Coverage was calculated with forward axis at +X.
            # The order of the values in the coverage is:
            # 0 = a = +Z: Top
            # 1 = b = -Z: Bottom
            # 2 = c = +X: North
            # 3 = d = -Y: East
            # 4 = e = -X: South
            # 5 = f = +Y: West

            # Technically this is wrong as the order would be different for -Y forward, but since the bricks must be cuboidal in shape, they are symmetrical.
            if self.__properties.axis_blb_forward == "POSITIVE_Y" or self.__properties.axis_blb_forward == "NEGATIVE_Y":
                # New North: +Y
                # +X: New East
                coverage = common.swizzle(coverage, "abfcde")

            # Else self.__properties.axis_blb_forward == "POSITIVE_X" or self.__properties.axis_blb_forward == "POSITIVE_X":
            # No support for Z axis remapping yet.
        else:
            # Use the default coverage.
            # Do not hide adjacent face.
            # Hide this face if it is covered by 9999 plates.
            coverage = [(0, 9999)] * 6

        # Save the coverage data to the definitions.
        self.__definition_data["coverage"] = coverage

    def process(self):
        """
        Processes Blender data.
        Returns a tuple where the first element is the sorted quad data and the second is the BLB definitions.
        """

        # Determine which objects to export.
        object_sequence = self.__get_object_sequence()

        if len(object_sequence) > 0:
            # Process the definition objects first.
            meshes = self.__process_definition_objects(object_sequence)

            # Calculate the coverage data.
            self.__calculate_coverage()

            return (self.__process_mesh_data(meshes), self.__definition_data)
        else:
            logger.error("Nothing to export.")
