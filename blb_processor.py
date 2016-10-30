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

# TODO: Remove all implicit rounding.

from decimal import Decimal, Context, setcontext, ROUND_HALF_UP
from math import ceil, isnan
from mathutils import Vector

# Blender requires imports from ".".
from . import logger, common, const

# Set the Decimal number context for operations: 0.5 is rounded up. (Precision can be whatever.)
# NOTE: prec=n limits the number of digits for the whole number.
# E.g. 1234.56 has a precision of 6, not 2.
setcontext(Context(rounding=ROUND_HALF_UP))


# =================
# BrickBounds Class
# =================


class BrickBounds(object):
    """A class for storing the Blender data of brick bounds.

    Stores the following data:
        - Blender object name,
        - object dimensions,
        - object's location in world coordinates,
        - minimum vertex world coordinate,
        - and maximum vertex world coordinate.
    """

    def __init__(self):
        # The name of the Blender object.
        self.name = None

        # The dimensions are stored separately even though it is trivial to calculate them from the coordinates because they are used often.
        self.dimensions = []

        # The object center coordinates are stored separately for convenience.
        self.world_center = []

        self.world_coords_min = []
        self.world_coords_max = []

    def __repr__(self):
        return "<BrickBounds name:{} dimensions:{} world_center:{} world_coords_min:{} world_coords_max:{}>".format(self.name, self.dimensions, self.world_center, self.world_coords_min, self.world_coords_max)


# =============
# BLBData Class
# =============


class BLBData(object):
    """A class for storing the brick data to be written to a BLB file.

    Stores the following data:
        - size (dimensions) in plates,
        - brick grid,
        - collision objects,
        - coverage,
        - and sorted quads.
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

        # Sorted quad data sequences.
        self.quads = []

# ==============
# Math Functions
# ==============


def __is_even(value):
    """Checks if the specified value is even.

    Args:
        value (number): A numerical value to check.

    Returns:
        True if the specified value is exactly divisible by 2.
    """
    return value % 2 == 0


def __to_decimal(value, quantize=const.CALCULATION_FP_PRECISION_STR):
    """Creates a Decimal number of the specified value and rounds it to the closest specified quantize value.
    The number of decimal digits in the quantize value will determine the number of decimal digits in the returned value.

    Args:
        value (number): A numerical value to create a Decimal out of.
        quantize (string or Decimal): The optional value to round the specified number to.
                                      The value may be given as a string or a Decimal number.
                                      If no value is specified, the default floating point precision will be used.

    Returns:
        A Decimal representation of the specified value as the closest multiple of the quantize value, with half rounded up.
    """
    # Make a Decimal out of the quantize value if it already isn't.
    if isinstance(quantize, str):
        quantize = Decimal(quantize)
    elif isinstance(quantize, Decimal):
        pass
    else:
        raise ValueError("quantize must be a string or a Decimal, was {}".format(type(quantize)))

    # Calculate the fraction that will be used to do the rounding to an arbitrary number.
    fraction = Decimal("1.0") / quantize

    # If the value is not a Decimal, convert the value to string and create a Decimal out of the formatted string.
    # Using strings is the only way to create Decimals accurately from numbers as the Decimal representation of
    # the input will be identical to that of the string.
    # I.e. I'm pushing the issue of accurate floating point representation to whatever is the default formatting.
    if not isinstance(value, Decimal):
        value = Decimal("{}".format(value))

    # Multiply the Decimal value with the Decimal fraction.
    # Round to the nearest integer with quantize.
    # Divide with the Decimal fraction.
    # Quantize the result to get the correct number of decimal digits.
    # Result: value is rounded to the nearest value of quantize (half rounded up)
    return ((value * fraction).quantize(Decimal("1")) / fraction).quantize(quantize)


def __to_decimals(values, quantize=const.CALCULATION_FP_PRECISION_STR):
    """Creates Decimal numbers out of the values in the specified sequence and rounds them to the specified round_to_value.
    The number of decimal digits in the quantize value will determine the number of decimal digits in the returned values.

    Args:
        values (sequence of numbers): A sequence of numerical values to create Decimals out of.
        quantize (string or Decimal): The optional value to round the specified numbers to.
                                      The value may be given as a string or a Decimal number.
                                      If no value is specified, the default floating point precision will be used.

    Returns:
        A list of Decimal representations of the specified values as the closest multiple of the quantize value, with half rounded up.
    """
    result = []

    for val in values:
        result.append(__to_decimal(val, quantize))

    return result


def __force_to_int(values):
    """Casts all values in the specified sequence to ints.

    Args:
        values (sequence of numbers): A sequence of numerical values to be casted to ints.

    Returns:
        A list of the sequence values casted to integers.
    """
    return [int(val) for val in values]


def __are_ints(values):
    """Checks if all values in the specified sequence are ints.

    Args:
        values (sequence of numbers): A sequence of numerical values.

    Returns:
        True if all values in the specified sequence are numerically equal to their integer counterparts.
    """
    for value in values:
        if value != int(value):
            return False

    return True


def __get_world_min(obj):
    """Gets the world space coordinates of the vertex in the specified object that is the closest to the world origin.

    Args:
        obj (Blender object): A Blender mesh.

    Returns:
        A new Vector of the minimum world space coordinates of the specified object.
    """
    # This function deals with Vectors instead of Decimals because it works with Blender object data, which uses Vectors.
    vec_min = Vector((float("+inf"), float("+inf"), float("+inf")))

    for vert in obj.data.vertices:
        # Local coordinates to world space.
        coord = obj.matrix_world * vert.co

        for i in range(3):
            vec_min[i] = min(vec_min[i], coord[i])

    return vec_min


def __record_world_min_max(sequence_min, sequence_max, obj):
    """Checks if the specified Blender object's vertices' world space coordinates are smaller or greater than the coordinates stored in their respective
    minimum and maximum sequences and updates the values in those sequences with the object's coordinates if they are smaller or greater.

    Args:
        sequence_min (Vector): The Vector of smallest XYZ world space coordinates found so far.
        sequence_max (Vector): The Vector of largest XYZ world space coordinates found so far.
        obj (Blender object): The Blender object whose vertex coordinates to check against the current minimum and maximum coordinates.
    """
    for vert in obj.data.vertices:
        coordinates = obj.matrix_world * vert.co

        for i in range(3):
            sequence_min[i] = min(sequence_min[i], coordinates[i])
            sequence_max[i] = max(sequence_max[i], coordinates[i])


def __vert_index_to_world_coord(obj, index):
    """Calculates the world coordinates for the vertex at the specified index in the specified Blender object.

    Args:
        obj (Blender object): The Blender object where the vertex is stored.
        index (int): The index of the vertex in the specified object's vertex data sequence.

    Returns:
        A Vector of the world coordinates of the vertex.
    """
    return obj.matrix_world * obj.data.vertices[index].co


def __vert_index_to_normal_vector(obj, index):
    """Calculates the normalized vertex normal vector for the vertex at the specified index in the specified Blender object.

    Args:
        obj (Blender object): The Blender object where the vertex is stored.
        index (int): The index of the vertex in the specified object's vertex data sequence.

    Returns:
        A normalized normal vector of the specified vertex.
    """
    return (obj.matrix_world.to_3x3() * obj.data.vertices[obj.data.loops[index].vertex_index].normal).normalized()


def __all_within_bounds(local_coordinates, bounding_dimensions):
    """Checks if all the values in the specified local coordinates are within the specified bounding box dimensions.
    Assumes that both sequences have the same number of elements.

    Args:
        local_coordinates (sequence of numbers): A sequence of local space coordinates.
        bounding_dimensions (sequence of numbers): A sequence of dimensions of a bounding box centered at the origin.

    Returns:
        True if all values are within the bounding dimensions.
    """
    # Divide all dimension values by 2.
    halved_dimensions = [value / Decimal("2.0") for value in bounding_dimensions]

    # Check if any values in the given local_coordinates are beyond the given bounding_dimensions.
    # bounding_dimensions / 2 = max value
    # -bounding_dimensions / 2 = min value

    for index, value in enumerate(local_coordinates):
        if value > halved_dimensions[index]:
            return False

    for index, value in enumerate(local_coordinates):
        if value < -(halved_dimensions[index]):
            return False

    return True


def __sequence_z_to_plates(xyz):
    """
    Performs __to_decimals(sequence) on the given sequence and scales the Z component to match Blockland plates.
    If the given sequence does not have exactly three components (assumed format is (X, Y, Z)) the input is returned unchanged.
    """
    if len(xyz) == 3:
        sequence = __to_decimals(xyz)
        sequence[const.Z] /= const.PLATE_HEIGHT
        return sequence
    else:
        return xyz


def __round_to_plate_coordinates(local_coordinates, brick_dimensions):
    """Rounds the specified sequence of local space XYZ coordinates to the nearest valid plate coordinates in a brick with the specified dimensions.

    Args:
        local_coordinates (sequence of numbers): A sequence of local space coordinates.
        brick_dimensions (sequence of numbers): A sequence of dimensions of the brick.

    Returns:
        A list of rounded local space coordinates as Decimal values.
    """
    result = []

    # 1 plate is 1.0 Blender units wide and deep.
    # Plates can only be 1.0 units long on the X and Y axes.
    # Valid plate positions exist every 0.5 units on odd sized bricks and every 1.0 units on even sized bricks.
    if __is_even(brick_dimensions[const.X]):
        result.append(__to_decimal(local_coordinates[const.X], "1.0"))
    else:
        result.append(__to_decimal(local_coordinates[const.X], "0.5"))

    if __is_even(brick_dimensions[const.Y]):
        result.append(__to_decimal(local_coordinates[const.Y], "1.0"))
    else:
        result.append(__to_decimal(local_coordinates[const.Y], "0.5"))

    # Round to the nearest full plate height. (Half is rounded up)
    if __is_even(brick_dimensions[const.Z] / const.PLATE_HEIGHT):
        result.append(__to_decimal(local_coordinates[const.Z], const.PLATE_HEIGHT))
    else:
        result.append(__to_decimal(local_coordinates[const.Z], (const.PLATE_HEIGHT / Decimal("2.0"))))

    return result


def __calculate_center(object_minimum_coordinates, object_dimensions):
    """Calculates the coordinates of the center of a 3D object.

    Args:
        object_minimum_coordinates (sequence of numbers): A sequence of minimum XYZ coordinates of the object.
                                                          This function is only useful is these are world space coordinates.
                                                          If local space coordinates are given, (0, 0, 0) will always be returned as the center regardless of the specified dimensions.
        object_dimensions (sequence of numbers): The dimensions of the object.

    Returns:
        A tuple of Decimal type XYZ coordinates.
    """
    return (object_minimum_coordinates[const.X] + (object_dimensions[const.X] / Decimal("2.0")),
            object_minimum_coordinates[const.Y] + (object_dimensions[const.Y] / Decimal("2.0")),
            object_minimum_coordinates[const.Z] + (object_dimensions[const.Z] / Decimal("2.0")))


def __world_to_local(coordinates, new_origin):
    """Translates the specified coordinates to be relative to the specified new origin coordinates.

    Commonly used to translate coordinates from world space (centered on (0, 0, 0)) to local space (arbitrary center).

    Args:
        coordinates (sequence of numbers): The sequence of XYZ coordinates to be translated.
        new_origin (sequence of numbers): The new origin point as a sequence of XYZ coordinates in the same space as the specified coordinates.

    Returns:
        A list of Decimal type coordinates relative to the specified new origin coordinates.
    """
    # Make the coordinates Decimals if all of them are not.
    if not all(isinstance(coord, Decimal) for coord in coordinates):
        coordinates = __to_decimals(coordinates)

    # Make the new origin Decimals if all of them are not.
    if not all(isinstance(coord, Decimal) for coord in new_origin):
        new_origin = __to_decimals(new_origin)

    return [old_coord - new_origin[index] for index, old_coord in enumerate(coordinates)]


def __mirror(xyz, forward_axis):
    """Mirrors the given XYZ sequence according to the specified forward axis.

    Args:
        xyz (sequence): A sequence of elements to be mirrored.
        forward_axis (string): The name of the Blender axis (enum value as string) that will point forwards in-game.

    Returns:
        A new list of XYZ values.
    """
    mirrored = xyz

    if forward_axis == "POSITIVE_X" or forward_axis == "NEGATIVE_X":
        mirrored[const.Y] = -mirrored[const.Y]
    else:
        mirrored[const.X] = -mirrored[const.X]

    return mirrored


def __to_float_or_none(value):
    """Converts the specified value to a float if it is numerical, or None if it is not.

    Args:
        value (object): Object to be converted to a float.

    Returns:
        A float representing the object or None if the object was not numerical.
    """
    try:
        num = float(value)

        if isnan(num):
            return None
        return num
    except ValueError:
        return None

# =================================
# Blender Data Processing Functions
# =================================


class OutOfBoundsException(Exception):
    """An exception thrown when a vertex position is outside of brick bounds."""
    pass


class ZeroSizeException(Exception):
    """An exception thrown when a definition object has zero brick size on at least one axis."""
    pass


def __modify_brick_grid(brick_grid, volume, symbol):
    """Modifies the specified brick grid by adding the specified symbol to every grid slot specified by the volume.

    Will crash if specified volume extends beyond the 3D space defined by the brick grid.

    Args:
        brick_grid (3D array): A pre-initialized three dimensional array representing every plate of a brick.
        volume (sequence of numerical ranges): A sequence of three (XYZ) sequences representing the dimensions of a 3D volume.
                                               Each element contains a sequence of two numbers representing a range of indices ([min, max[) in the brick grid.
        symbol (string): A valid brick grid symbol to place in the elements specified by the volume.
    """
    # Ranges are exclusive [min, max[ index ranges.
    width_range = volume[const.X]
    depth_range = volume[const.Y]
    height_range = volume[const.Z]

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


def __calculate_coverage(brick_size=None, calculate_side=None, hide_adjacent=None, forward_axis=None):
    """Calculates the BLB coverage data for a brick.

    Args:
        brick_size (sequence of integers): An optional sequence of the sizes of the brick on each of the XYZ axes.
                                           If not defined, default coverage will be used.
        calculate_side (sequence of booleans): An optional sequence of boolean values where the values must in the same order as const.QUAD_SECTION_ORDER.
                                               A value of true means that coverage will be calculated for that side of the brick according the specified size of the brick.
                                               A value of false means that the default coverage value will be used for that side.
                                               Must be defined if brick_size is defined.
        hide_adjacent (sequence of booleans): An optional sequence of boolean values where the values must in the same order as const.QUAD_SECTION_ORDER.
                                              A value of true means that faces of adjacent bricks covering this side of this brick will be hidden.
                                              A value of false means that adjacent brick faces will not be hidden.
                                              Must be defined if brick_size is defined.
        forward_axis (Axis): The optional user-defined BLB forward axis.
                             Must be defined if brick_size is defined.

    Returns:
        A sequence of BLB coverage data.
    """
    coverage = []

    # Does the user want to calculate coverage in the first place?
    if calculate_side is not None:
        # Initially assume that forward axis is +X, data will be swizzled later.
        for index, side in enumerate(calculate_side):
            if side:
                # Calculate the area of side.
                if index == const.QUAD_SECTION_IDX_TOP or index == const.QUAD_SECTION_IDX_BOTTOM:
                    area = brick_size[const.X] * brick_size[const.Y]
                if index == const.QUAD_SECTION_IDX_NORTH or index == const.QUAD_SECTION_IDX_SOUTH:
                    area = brick_size[const.X] * brick_size[const.Z]
                if index == const.QUAD_SECTION_IDX_EAST or index == const.QUAD_SECTION_IDX_WEST:
                    area = brick_size[const.Y] * brick_size[const.Z]
            else:
                area = const.DEFAULT_COVERAGE

            # Hide adjacent face?
            coverage.append((hide_adjacent[index], area))

        # Swizzle the coverage values around according to the defined forward axis.
        # Coverage was calculated with forward axis at +X.

        # ===========================================
        # The order of the values in the coverage is:
        # 0 = a = +Z: Top
        # 1 = b = -Z: Bottom
        # 2 = c = +X: North
        # 3 = d = -Y: East
        # 4 = e = -X: South
        # 5 = f = +Y: West
        # ===========================================

        # Technically this is wrong as the order would be different for -Y forward, but since the bricks must be cuboid in shape, they are symmetrical.
        if forward_axis == "POSITIVE_Y" or forward_axis == "NEGATIVE_Y":
            # New North will be +Y.
            # Old North (+X) will be the new East
            coverage = common.swizzle(coverage, "abfcde")

        # Else forward_axis is +X or -X: no need to do anything, the calculation was done with +X.

        # No support for Z axis remapping yet.
    else:
        # Use the default coverage.
        # Do not hide adjacent face.
        # Hide this face if it is covered by const.DEFAULT_COVERAGE plates.
        coverage = [(0, const.DEFAULT_COVERAGE)] * 6

    return coverage


def __sort_quad(quad, bounds_dimensions, forward_axis):
    """Calculates the section (brick side) for the specified quad within the specified bounds dimensions.

    The section is determined by whether all vertices of the quad are in the same plane as one of the planes (brick sides) defined by the (cuboid) brick bounds.
    The quad's section is needed for brick coverage.

    Args:
        quad (sequence): A sequence of various data that defines the quad.
        bounds_dimensions (sequence of Decimals): The dimensions of the brick bounds.
        forward_axis (string): The name of the user-defined BLB forward axis.

    Returns:
        The index of the section name in const.QUAD_SECTION_ORDER sequence.
    """
    # This function only handles quads so there are always exactly 4 position lists. (One for each vertex.)
    positions = quad[0]

    # Divide all dimension values by 2 to get the local bounding plane values.
    # The dimensions are in Blender units so Z height needs to be converted to plates.
    local_bounds = __sequence_z_to_plates([value / Decimal("2.0") for value in bounds_dimensions])

    # Assume omni direction until otherwise proven.
    direction = 6

    # Each position list has exactly 3 values.
    # 0 = X
    # 1 = Y
    # 2 = Z
    for axis in range(3):
        # If the vertex coordinate is the same on an axis for all 4 vertices, this face is parallel to the plane perpendicular to that axis.
        if positions[0][axis] == positions[1][axis] == positions[2][axis] == positions[3][axis]:
            # If the common value is equal to one of the bounding values the quad is on the same plane as one of the edges of the brick.
            # Stop searching as soon as the first plane is found because it is impossible for the quad to be on multiple planes at the same time.
            # If the vertex coordinates are equal on more than one axis, it means that the quad is either a line (2 axes) or a point (3 axes).

            # Assuming that forward axis is Blender +X ("POSITIVE_X").
            # Then in-game the brick north is to the left of the player, which is +Y in Blender.
            # I know it makes no sense.

            # All vertex coordinates are the same on this axis, only the first one needs to be checked.

            # Positive values.
            if positions[0][axis] == local_bounds[axis]:
                # +X = East
                if axis == const.X:
                    direction = const.QUAD_SECTION_IDX_EAST
                    break
                # +Y = North
                elif axis == const.Y:
                    direction = const.QUAD_SECTION_IDX_NORTH
                    break
                # +Z = Top
                else:
                    direction = const.QUAD_SECTION_IDX_TOP
                    break

            # Negative values.
            elif positions[0][axis] == -local_bounds[axis]:
                # -X = West
                if axis == const.X:
                    direction = const.QUAD_SECTION_IDX_WEST
                    break
                # -Y = South
                elif axis == const.Y:
                    direction = const.QUAD_SECTION_IDX_SOUTH
                    break
                # -Z = Bottom
                else:
                    direction = const.QUAD_SECTION_IDX_BOTTOM
                    break
            # Else the quad is not on the same plane with one of the bounding planes = Omni
        # Else the quad is not planar = Omni

    # ===========================
    # QUAD_SECTION_IDX_TOP    = 0
    # QUAD_SECTION_IDX_BOTTOM = 1
    # QUAD_SECTION_IDX_NORTH  = 2
    # QUAD_SECTION_IDX_EAST   = 3
    # QUAD_SECTION_IDX_SOUTH  = 4
    # QUAD_SECTION_IDX_WEST   = 5
    # QUAD_SECTION_IDX_OMNI   = 6
    # ===========================

    # Top and bottom always the same and do not need to be rotated because Z axis remapping is not yet supported.
    # Omni is not planar and does not need to be rotated.
    # The initial values are calculated according to +X forward axis.
    if direction <= const.QUAD_SECTION_IDX_BOTTOM or direction == const.QUAD_SECTION_IDX_OMNI or forward_axis == "POSITIVE_X":
        return direction

    # ========================================================================
    # Rotate the direction according the defined forward axis.
    # 0. direction is in the range [2, 5].
    # 1. Subtract 2 to put direction in the range [0, 3]: dir - 2
    # 2. Add the rotation constant:                       dir - 2 + R
    # 3. Use modulo make direction wrap around 3 -> 0:    dir - 2 + R % 4
    # 4. Add 2 to get back to the correct range [2, 5]:   dir - 2 + R % 4 + 2
    # ========================================================================
    elif forward_axis == "POSITIVE_Y":
        # 90 degrees clockwise.
        # [2] North -> [3] East:  (2 - 2 + 1) % 4 + 2 = 3
        # [5] West  -> [2] North: (5 - 2 + 1) % 4 + 2 = 2
        return (direction - 1) % 4 + 2
    elif forward_axis == "NEGATIVE_X":
        # 180 degrees clockwise.
        # [2] North -> [4] South: (2 - 2 + 2) % 4 + 2 = 4
        # [4] South -> [2] North
        return direction % 4 + 2
    elif forward_axis == "NEGATIVE_Y":
        # 270 degrees clockwise.
        # [2] North -> [5] West:  (2 - 2 + 3) % 4 + 2 = 5
        # [5] West  -> [4] South
        return (direction + 1) % 4 + 2


def __get_object_sequence(context, properties):
    """Determines the sequence of Blender objects to be processed.

    Args:
        context (Blender context object): A Blender object containing scene data.
        properties (Blender properties object): A Blender object containing user preferences.

    Returns:
        The sequence of Blender objects from the specified Blender context to be exported according to the specified user preferences.
    """
    objects = []

    # Use selected objects?
    if properties.export_objects == "SELECTION":
        logger.info("Exporting selected objects to BLB.")
        objects = context.selected_objects
        logger.info(logger.build_countable_message("  Found ", len(objects), (" object.", " objects."), "", "  No objects selected."))

    # Use objects in visible layers?
    if properties.export_objects == "LAYERS":
        logger.info("Exporting objects in visible layers to BLB.")
        print(context.scene.layers)
        # objects = [obj for obj in context.scene.objects for index in range(
        #    len(context.scene.layers)) if True == obj.layers[index] == context.scene.layers[index]]
        # For every object in the scene.
        for obj in context.scene.objects:
            # For every layer in the scene.
            for index in range(len(context.scene.layers)):
                # If this layer is visible.
                # And this object is in the layer.
                if True == obj.layers[index] == context.scene.layers[index]:
                    # Append to the list of objects.
                    objects.append(obj)

        logger.info(logger.build_countable_message("  Found ", len(objects), (" object.", " objects."), "", "  No objects in visible layers."))

    # If user wants to export the whole scene.
    # Or if user wanted to export only the selected objects or layers but they contained nothing.
    # Get all scene objects.
    if properties.export_objects == "SCENE" or len(objects) == 0:
        logger.info("Exporting scene to BLB.")
        objects = context.scene.objects
        logger.info(logger.build_countable_message("  Found ", len(objects), (" object.", " objects."), "", "  Scene has no objects."))

    return objects


def __record_defined_bounds(blb_data, obj):
    """Adds the brick bounds data to the specified BLB data object.

    Args:
        blb_data (BLBData): A BLBData object containing all the necessary data for writing a BLB file.
        obj (Blender object): The Blender object defining the bounds of the brick that the user created.

    Returns:
        The modified blb_data object containing the bounds data.
    """
    # Get the dimensions of the Blender object and convert the height to plates.
    bounds_size = __sequence_z_to_plates(obj.dimensions)

    # Are the dimensions of the bounds object not integers?
    if not __are_ints(bounds_size):
        logger.warning("Defined bounds have a non-integer size {} {} {}, rounding to a precision of {}.".format(bounds_size[const.X],
                                                                                                                bounds_size[const.Y],
                                                                                                                bounds_size[const.Z],
                                                                                                                const.HUMAN_ERROR))
        for index, value in enumerate(bounds_size):
            # Round to the specified error amount.
            bounds_size[index] = round(const.HUMAN_ERROR * round(value / const.HUMAN_ERROR))

    # The value type must be int because you can't have partial plates. Returns a list.
    blb_data.brick_size = __force_to_int(bounds_size)

    return blb_data


def __record_calculated_bounds(blb_data, bounds_data):
    """Adds the brick bounds data to the specified BLB data object.

    Args:
        blb_data (BLBData): A BLBData object containing all the necessary data for writing a BLB file.
        bounds_data (BrickBounds): A BrickBounds object containing the bounds data that was automatically calculated.

    Returns:
        The modified blb_data object containing the bounds data.
    """
    # Convert height to plates.
    bounds_size = __sequence_z_to_plates(bounds_data.dimensions)

    # Are the dimensions of the bounds object not integers?
    if not __are_ints(bounds_size):
        logger.warning("Calculated bounds has a non-integer size {} {} {}, rounding up.".format(bounds_size[const.X],
                                                                                                bounds_size[const.Y],
                                                                                                bounds_size[const.Z]))

        # In case height conversion or rounding introduced floating point errors, round up to be on the safe side.
        for index, value in enumerate(bounds_size):
            bounds_size[index] = ceil(value)

    # The value type must be int because you can't have partial plates. Returns a list.
    blb_data.brick_size = __force_to_int(bounds_size)

    return blb_data


def __calculate_bounds(min_world_coordinates, max_world_coordinates):
    """Calculates the brick bounds data from the recorded minimum and maximum vertex world coordinates.

    Args:
        min_world_coordinates (sequence of numbers): A sequence containing the minimum world coordinates of the brick to be exported.
        max_world_coordinates (sequence of numbers): A sequence containing the maximum world coordinates of the brick to be exported.

    Returns:
        A BrickBounds object containg the brick bounds data.
    """
    logger.warning("No '" + const.BOUNDS_NAME_PREFIX + "' definition found. Automatically calculated brick size may be undesirable.")

    bounds_data = BrickBounds()

    # Get the dimensions defined by the vectors.
    # ROUND & CAST: calculated bounds object dimensions into Decimals for accuracy.
    bounds_size = __to_decimals((max_world_coordinates[const.X] - min_world_coordinates[const.X],
                                 max_world_coordinates[const.Y] - min_world_coordinates[const.Y],
                                 (max_world_coordinates[const.Z] - min_world_coordinates[const.Z])))

    bounds_data.name = None
    bounds_data.dimensions = bounds_size

    # The minimum and maximum calculated world coordinates.
    bounds_data.world_coords_min = __to_decimals(min_world_coordinates)
    bounds_data.world_coords_max = __to_decimals(max_world_coordinates)

    bounds_data.world_center = __calculate_center(bounds_data.world_coords_min, bounds_data.dimensions)

    return bounds_data


def __process_bounds_object(obj):
    """Processes a manually defined bounds Blender object.

    Args:
        obj (Blender object): The Blender object defining the bounds of the brick that the user created.

    Returns:
        A BrickBounds object.
    """
    # TODO: Make use of __calculate_bounds to reduce duplicate code.
    bounds_data = BrickBounds()

    # Store the name for logging.
    bounds_data.name = obj.name

    # ROUND & CAST: defined bounds object dimensions into Decimals for accuracy.
    bounds_data.dimensions = __to_decimals(obj.dimensions)

    # Find the minimum and maximum world coordinates for the bounds object.
    bounds_min = Vector((float("+inf"), float("+inf"), float("+inf")))
    bounds_max = Vector((float("-inf"), float("-inf"), float("-inf")))
    __record_world_min_max(bounds_min, bounds_max, obj)

    # ROUND & CAST: defined bounds object min/max world coordinates into Decimals for accuracy.
    bounds_data.world_coords_min = __to_decimals(bounds_min)
    bounds_data.world_coords_max = __to_decimals(bounds_max)

    bounds_data.world_center = __calculate_center(bounds_data.world_coords_min, bounds_data.dimensions)

    return bounds_data


def __process_coverage(properties, blb_data):
    """Calculates the coverage data if the user has defined so in the properties.
    If user does not want coverage, default coverage data will be used.

    Args:
        properties (Blender properties object): A Blender object containing user preferences.
        blb_data (BLBData): A BLBData object containing all the necessary data for writing a BLB file.

    Returns:
        A sequence of BLB coverage data.
    """
    if properties.calculate_coverage:
        calculate_side = ((properties.coverage_top_calculate,
                           properties.coverage_bottom_calculate,
                           properties.coverage_north_calculate,
                           properties.coverage_east_calculate,
                           properties.coverage_south_calculate,
                           properties.coverage_west_calculate))

        hide_adjacent = ((properties.coverage_top_hide,
                          properties.coverage_bottom_hide,
                          properties.coverage_north_hide,
                          properties.coverage_east_hide,
                          properties.coverage_south_hide,
                          properties.coverage_west_hide))

        return __calculate_coverage(blb_data.brick_size,
                                    calculate_side,
                                    hide_adjacent,
                                    properties.axis_blb_forward)
    else:
        return __calculate_coverage()


def __grid_object_to_volume(properties, bounds_data, grid_obj):
    """Calculates the brick grid definition index range [min, max[ for each axis from the vertex coordinates of the specified object.
    The indices represent a three dimensional volume in the local space of the bounds object where the origin is in the -X +Y +Z corner.
    Can raise OutOfBoundsException and ZeroSizeException.

    Args:
        properties (Blender properties object): A Blender object containing user preferences.
        bounds_data (BrickBounds): A BrickBounds object containing the bounds data.
        grid_obj (Blender object): A Blender object representing a brick grid definition.

    Returns:
        A tuple in the following format: ( (min_width, max_width), (min_depth, max_depth), (min_height, max_height) )
    """
    halved_dimensions = [value / Decimal("2.0") for value in bounds_data.dimensions]

    # Find the minimum and maximum coordinates for the brick grid object.
    grid_min = Vector((float("+inf"), float("+inf"), float("+inf")))
    grid_max = Vector((float("-inf"), float("-inf"), float("-inf")))
    __record_world_min_max(grid_min, grid_max, grid_obj)

    # Recenter the coordinates to the bounds. (Also rounds the values.)
    grid_min = __world_to_local(grid_min, bounds_data.world_center)
    grid_max = __world_to_local(grid_max, bounds_data.world_center)

    # Round coordinates to the nearest plate.
    grid_min = __round_to_plate_coordinates(grid_min, bounds_data.dimensions)
    grid_max = __round_to_plate_coordinates(grid_max, bounds_data.dimensions)

    if __all_within_bounds(grid_min, bounds_data.dimensions) and __all_within_bounds(grid_max, bounds_data.dimensions):
        # Convert the coordinates into brick grid sequence indices.

        # Minimum indices.
        if properties.axis_blb_forward == "NEGATIVE_X" or properties.axis_blb_forward == "NEGATIVE_Y":
            # Translate coordinates to negative X axis.
            # -X: Index 0 = front of the brick.
            # -Y: Index 0 = left of the brick.
            grid_min[const.X] = grid_min[const.X] - halved_dimensions[const.X]
        else:
            # Translate coordinates to positive X axis.
            # +X: Index 0 = front of the brick.
            # +Y: Index 0 = left of the brick.
            grid_min[const.X] = grid_min[const.X] + halved_dimensions[const.X]

        if properties.axis_blb_forward == "POSITIVE_X" or properties.axis_blb_forward == "NEGATIVE_Y":
            # Translate coordinates to negative Y axis.
            # +X: Index 0 = left of the brick.
            # -Y: Index 0 = front of the brick.
            grid_min[const.Y] = grid_min[const.Y] - halved_dimensions[const.Y]
        else:
            # Translate coordinates to positive Y axis.
            # +Y: Index 0 = front of the brick.
            # -X: Index 0 = left of the brick.
            grid_min[const.Y] = grid_min[const.Y] + halved_dimensions[const.Y]

        # Translate coordinates to negative Z axis, height to plates.
        grid_min[const.Z] = (grid_min[const.Z] - halved_dimensions[const.Z]) / const.PLATE_HEIGHT

        # Maximum indices.
        if properties.axis_blb_forward == "NEGATIVE_X" or properties.axis_blb_forward == "NEGATIVE_Y":
            grid_max[const.X] = grid_max[const.X] - halved_dimensions[const.X]
        else:
            grid_max[const.X] = grid_max[const.X] + halved_dimensions[const.X]

        if properties.axis_blb_forward == "POSITIVE_X" or properties.axis_blb_forward == "NEGATIVE_Y":
            grid_max[const.Y] = grid_max[const.Y] - halved_dimensions[const.Y]
        else:
            grid_max[const.Y] = grid_max[const.Y] + halved_dimensions[const.Y]

        grid_max[const.Z] = (grid_max[const.Z] - halved_dimensions[const.Z]) / const.PLATE_HEIGHT

        # Swap min/max Z index and make it positive. Index 0 = top of the brick.
        temp = grid_min[const.Z]
        grid_min[const.Z] = abs(grid_max[const.Z])
        grid_max[const.Z] = abs(temp)

        if properties.axis_blb_forward == "POSITIVE_X":
            # Swap min/max depth and make it positive.
            temp = grid_min[const.Y]
            grid_min[const.Y] = abs(grid_max[const.Y])
            grid_max[const.Y] = abs(temp)

            grid_min = common.swizzle(grid_min, "bac")
            grid_max = common.swizzle(grid_max, "bac")
        elif properties.axis_blb_forward == "NEGATIVE_X":
            # Swap min/max width and make it positive.
            temp = grid_min[const.X]
            grid_min[const.X] = abs(grid_max[const.X])
            grid_max[const.X] = abs(temp)

            grid_min = common.swizzle(grid_min, "bac")
            grid_max = common.swizzle(grid_max, "bac")
        elif properties.axis_blb_forward == "NEGATIVE_Y":
            # Swap min/max depth and make it positive.
            temp = grid_min[const.Y]
            grid_min[const.Y] = abs(grid_max[const.Y])
            grid_max[const.Y] = abs(temp)

            # Swap min/max width and make it positive.
            temp = grid_min[const.X]
            grid_min[const.X] = abs(grid_max[const.X])
            grid_max[const.X] = abs(temp)
        # Else properties.axis_blb_forward == "POSITIVE_Y": do nothing

        grid_min = __force_to_int(grid_min)
        grid_max = __force_to_int(grid_max)

        zero_size = False

        # Check for zero size.
        for index, value in enumerate(grid_max):
            if (value - grid_min[index]) == 0:
                zero_size = True
                break

        if zero_size:
            logger.error("Brick grid definition object '{}' has zero size on at least one axis. Definition ignored.".format(grid_obj.name))
            raise ZeroSizeException()
        else:
            # Return the index ranges as a tuple: ( (min_width, max_width), (min_depth, max_depth), (min_height, max_height) )
            return ((grid_min[const.X], grid_max[const.X]),
                    (grid_min[const.Y], grid_max[const.Y]),
                    (grid_min[const.Z], grid_max[const.Z]))
    else:
        if bounds_data.name is None:
            logger.error("Brick grid definition object '{}' has vertices outside the calculated brick bounds. Definition ignored.".format(grid_obj.name))
        else:
            logger.error("Brick grid definition object '{}' has vertices outside the bounds definition object '{}'. Definition ignored.".format(
                grid_obj.name, bounds_data.name))
        raise OutOfBoundsException()


def __process_grid_definitions(properties, blb_data, bounds_data, definition_objects):
    """Processes the specified brick grid definitions.

    Args:
        properties (Blender properties object): A Blender object containing user preferences.
        blb_data (BLBData): A BLBData object containing all the necessary data for writing a BLB file.
        bounds_data (BrickBounds): A BrickBounds object containing the bounds data.
        definition_objects (a sequence of Blender object): A sequence of Blender objects representing brick grid definitions.

    Returns:
        A three dimensional array of brick grid symbols, ready for writing to a file.
    """
    # Make one empty list for each brick grid definition.
    definition_volumes = [[] for i in range(len(const.GRID_DEF_OBJ_PREFIX_PRIORITY))]
    processed = 0

    for grid_obj in definition_objects:
        try:
            # The first 5 characters of the Blender object name must be the grid definition prefix.
            # Get the index of the definition list.
            # And append the definition data to the list.
            index = const.GRID_DEF_OBJ_PREFIX_PRIORITY.index(grid_obj.name.lower()[:5])
            definition_volumes[index].append(__grid_object_to_volume(properties, bounds_data, grid_obj))
            processed += 1
        except OutOfBoundsException:
            # Do nothing, definition is ignored.
            pass
        except ZeroSizeException:
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
    if properties.axis_blb_forward == "POSITIVE_X" or properties.axis_blb_forward == "NEGATIVE_X":
        grid_width = blb_data.brick_size[const.X]
        grid_depth = blb_data.brick_size[const.Y]
    else:
        grid_width = blb_data.brick_size[const.Y]
        grid_depth = blb_data.brick_size[const.X]

    grid_height = blb_data.brick_size[const.Z]

    # Initialize the brick grid with the empty symbol with the dimensions of the brick.
    brick_grid = [[[const.GRID_OUTSIDE for w in range(grid_width)] for h in range(grid_height)] for d in range(grid_depth)]

    if len(definition_objects) == 0:
        # Write the default brick grid.
        for d in range(grid_depth):
            for h in range(grid_height):
                is_top = (h == 0)  # Current height is the top of the brick?
                is_bottom = (h == grid_height - 1)  # Current height is the bottom of the brick?

                if is_bottom and is_top:
                    symbol = const.GRID_BOTH
                elif is_bottom:
                    symbol = const.GRID_DOWN
                elif is_top:
                    symbol = const.GRID_UP
                else:
                    symbol = const.GRID_INSIDE

                # Create a new list of the width of the grid filled with the selected symbol.
                # Assign it to the current height.
                brick_grid[d][h] = [symbol] * grid_width
    else:
        # Write the calculated definition_volumes into the brick grid.
        for index, volumes in enumerate(definition_volumes):
            # Get the symbol for these volumes.
            symbol = const.GRID_DEFINITIONS_PRIORITY[index]
            for volume in volumes:
                # Modify the grid by adding the symbol to the correct locations.
                __modify_brick_grid(brick_grid, volume, symbol)

    return brick_grid


def __process_collision_definitions(bounds_data, definition_objects):
    """Processes the specified collision definitions.

    Args:
        bounds_data (BrickBounds): A BrickBounds object containing the bounds data.
        definition_objects (a sequence of Blender object): A sequence of Blender objects representing collision definitions.

    Returns:
        A sequence of tuples : [ (center coordinates in the local space of the brick, collision cuboid dimensions), ]
    """
    collisions = []
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
        __record_world_min_max(col_min, col_max, obj)

        # Recenter the coordinates to the bounds. (Also rounds the values.)
        col_min = __world_to_local(col_min, bounds_data.world_center)
        col_max = __world_to_local(col_max, bounds_data.world_center)

        if __all_within_bounds(col_min, bounds_data.dimensions) and __all_within_bounds(col_max, bounds_data.dimensions):
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
            collisions.append((__sequence_z_to_plates(center), __sequence_z_to_plates(dimensions)))
        else:
            if bounds_data.name is None:
                logger.error("Collision definition object '{}' has vertices outside the calculated brick bounds. Definition ignored.".format(obj.name))
            else:
                logger.error("Collision definition object '{}' has vertices outside the bounds definition object '{}'. Definition ignored.".format(
                    obj.name, bounds_data.name))

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

    return collisions


def __process_definition_objects(properties, objects):
    """"Processes all definition objects that are not exported as a 3D model but will affect the brick properties.

    Processed definition objects:
        - bounds
        - brick grid
        - collision

    If no bounds object is found, the brick bounds will be automatically calculated using the minimum and maximum coordinates of the vertices in the visible mesh objects.

    Args:
        properties (Blender properties object): A Blender object containing user preferences.
        objects (sequence of Blender objects): The sequence of objects to be processed.

    Returns:
        A tuple containing:
            0. A BLBData object containing the bounds, brick grid, and collision data.
            1. A BrickBounds object containing the brick bounds data.
            2. A sequence of mesh objects that will be exported as visible 3D models.
    """
    blb_data = BLBData()
    bounds_data = None
    brick_grid_objects = []
    collision_objects = []
    mesh_objects = []

    # These are vectors because Blender vertex coordinates are stored as vectors.
    # They are used for recording the minimum and maximum vertex world
    # coordinates of all visible meshes so that the brick bounds can be
    # calculated, if they are not defined manually.
    min_world_coordinates = Vector((float("+inf"), float("+inf"), float("+inf")))
    max_world_coordinates = Vector((float("-inf"), float("-inf"), float("-inf")))

    # Loop through all objects in the sequence.
    # The objects in the sequence are sorted so that the oldest created object is last.
    # Process the objects in reverse: from oldest to newest.
    for obj in reversed(objects):
        obj_name = obj.name.lower()

        # Ignore non-mesh objects
        if obj.type != "MESH":
            if obj_name.startswith(const.BOUNDS_NAME_PREFIX):
                logger.warning("Object '{}' cannot be used to define bounds, must be a mesh.".format(obj.name))
            elif obj_name.startswith(const.GRID_DEF_OBJ_PREFIX_PRIORITY):
                logger.warning("Object '{}' cannot be used to define brick grid, must be a mesh.".format(obj.name))
            elif obj_name.startswith(const.COLLISION_PREFIX):
                logger.warning("Object '{}' cannot be used to define collision, must be a mesh.".format(obj.name))

            continue

        # Is the current object a bounds definition object?
        elif obj_name.startswith(const.BOUNDS_NAME_PREFIX):
            if bounds_data is None:
                bounds_data = __process_bounds_object(obj)
                blb_data = __record_defined_bounds(blb_data, obj)

                logger.info("Defined brick size in plates: {} wide {} deep {} tall".format(blb_data.brick_size[const.X],
                                                                                           blb_data.brick_size[const.Y],
                                                                                           blb_data.brick_size[const.Z]))
            else:
                logger.warning("Multiple bounds definitions found. '{}' definition ignored.".format(obj.name))
                continue

        # Is the current object a brick grid definition object?
        elif obj_name.startswith(const.GRID_DEF_OBJ_PREFIX_PRIORITY):
            # Brick grid definition objects cannot be processed until after the bounds have been defined.
            brick_grid_objects.append(obj)

        # Is the current object a collision definition object?
        elif obj_name.startswith(const.COLLISION_PREFIX):
            # Collision definition objects cannot be processed until after the bounds have been defined.
            collision_objects.append(obj)

        # Else the object must be a regular mesh that is exported as a 3D model.
        else:
            mesh_objects.append(obj)

            # If no bounds object has been defined.
            if bounds_data is None:
                # Record min/max world coordinates for calculating the bounds.
                __record_world_min_max(min_world_coordinates, max_world_coordinates, obj)
            # Else a bounds object has been defined, recording the min/max coordinates is pointless.

    # No manually created bounds object was found, calculate brick bounds based on the minimum and maximum recorded mesh vertex positions.
    if bounds_data is None:
        bounds_data = __calculate_bounds(min_world_coordinates, max_world_coordinates)
        blb_data = __record_calculated_bounds(blb_data, bounds_data)

        logger.info("Calculated brick size in plates: {} wide {} deep {} tall".format(blb_data.brick_size[const.X],
                                                                                      blb_data.brick_size[const.Y],
                                                                                      blb_data.brick_size[const.Z]))

    # Process brick grid and collision definitions now that a bounds definition exists.
    blb_data.brick_grid = __process_grid_definitions(properties, blb_data, bounds_data, brick_grid_objects)
    blb_data.collision = __process_collision_definitions(bounds_data, collision_objects)

    # Return the data.
    return (blb_data, bounds_data, mesh_objects)


def __process_mesh_data(properties, bounds_data, meshes):
    """Gets all the necessary data from the specified Blender objects and sorts all the quads of the meshes into sections for brick coverage to work.

    Args:
        properties (Blender properties object): A Blender object containing user preferences.
        bounds_data (BrickBounds): A BrickBounds object containing the bounds data.
        meshes (sequence of Blender objects): Meshes to be processed.

    Returns:
        A sequence of mesh data sorted into sections.
    """
    quads = []
    count_tris = 0
    count_ngon = 0

    for obj in meshes:
        object_name = obj.name
        logger.info("Exporting mesh: {}".format(object_name))

        current_data = obj.data

        # Do UV layers exist?
        if current_data.uv_layers:
            # Is there more than one UV layer?
            if len(current_data.uv_layers) > 1:
                logger.warning("  Object '{}' has {} UV layers, only using the first.".format(object_name, len(current_data.uv_layers)))

            uv_data = current_data.uv_layers[0].data
        else:
            uv_data = None

        # =============
        # Object Colors
        # =============
        colors = None
        name = object_name.lower()

        # If the fourth last character of the name is a period, remove the last four characters.
        # Blender adds .### to the end of objects with duplicate names which can be confused for a floating point value.
        if len(name) > 3 and name[-4] == '.':
            name = name[:-4]

        # TODO: Document this feature in UI.
        # Replace commas with dots because the decimals in object names must be defined using a comma.
        # Split object name at whitespaces.
        values = name.replace(',', '.').split()

        # Does the object name begin with the letter C and a whitespace character signifying that it defines the object's color?
        if values[0] == "c":
            # Convert all elements to floats and ignore elements that would be None.
            # It does do the function twice but I doubt the object names will be so long that this will be an issue plus the function is simple.
            floats = [__to_float_or_none(val) for val in values if __to_float_or_none(val) is not None]
            size = len(floats)

            # Are all four values defined?
            if size >= 4:
                if size > 4:
                    logger.info("  More than 4 colors defined for colored object '{}', only the first four values were used.".format(object_name))

                    # We're only interested in the first 4 values: R G B A
                    floats = floats[:4]

                # Add the RGBA values to the colors, 4 vertices per quad.
                colors = ([tuple(floats)] * 4)
            elif size > 0:
                logger.info(
                    "  Object '{}' is named as if it were colored but it was ignored because all 4 values (red green blue alpha) were not defined.".format(object_name))

        # Process quad data.
        for poly in current_data.polygons:
            # ===================
            # Vertex loop indices
            # ===================
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
                # Cannot process n-gons, skip.
                continue

            # ================
            # Vertex positions
            # ================
            positions = []

            # Reverse the loop_indices tuple. (Blender seems to keep opposite winding order.)
            for loop_index in reversed(loop_indices):
                # Get the vertex index in the object from the loop.
                vert_index = obj.data.loops[loop_index].vertex_index

                # Get the vertex world position from the vertex index.
                # Center the position to the current bounds object: coordinates are now in local object space.
                # TODO: Why on earth am I rounding the vertex coordinates to the closest
                # plate height? This needs to be a property, not something done automatically!
                positions.append(__sequence_z_to_plates(__world_to_local(__vert_index_to_world_coord(obj, vert_index), bounds_data.world_center)))

            # =======
            # Normals
            # =======
            # FIXME: Object rotation affects normals.

            if poly.use_smooth:
                # Smooth shading.
                # For every vertex index in the loop_indices, calculate the vertex normal and add it to the list.
                normals = [__vert_index_to_normal_vector(obj, index) for index in reversed(loop_indices)]
            else:
                # Flat shading: every vertex in this loop has the same normal.
                # A tuple cannot be used because the values are changed afterwards when the brick is rotated.
                normals = [poly.normal, ] * 4

            # ===
            # UVs
            # ===
            if uv_data:
                # Get the UV coordinate for every vertex in the face loop.
                uvs = [uv_data[index].uv for index in reversed(loop_indices)]
            else:
                # No UVs present, use the defaults.
                # These UV coordinates with the SIDE texture lead to a blank textureless face.
                uvs = (Vector((0.5, 0.5)),) * 4

            # =============
            # Vertex Colors
            # =============
            # Object colors override vertex colors since they are easier to use.
            if colors is None:
                # A vertex color layer exists.
                if len(current_data.vertex_colors) != 0:
                    colors = []
                    # Vertex winding order is reversed compared to Blockland.
                    for index in reversed(loop_indices):
                        if len(current_data.vertex_colors) > 1:
                            logger.warning("  Object '{}' has {} vertex color layers, only using the first.".format(
                                object_name, len(current_data.vertex_colors)))

                        # Only use the first color layer.
                        loop_color = current_data.vertex_colors[0].data[index]

                        # TODO: Document this feature in UI.
                        # Use the color layer name as the value for alpha, if it is numerical.
                        # This does limit the alpha to be per-face but Blockland does not support per-vertex alpha anyway.
                        # Well actually the game can render per-vertex alpha but it doesn't seem to stick for longer than a second for whatever reason.
                        name = __to_float_or_none(current_data.vertex_colors[0].name)

                        if name is None:
                            alpha = 1.0
                        else:
                            alpha = name

                        # color_layer.data[index] may contain more than 4 values.
                        # Blockland only supports four colors per quad so only the first four values are stored.
                        colors.append((loop_color.color.r, loop_color.color.g, loop_color.color.b, alpha))

            # ================
            # BLB texture name
            # ================
            if current_data.materials and current_data.materials[poly.material_index] is not None:
                texture = current_data.materials[poly.material_index].name.upper()
            else:
                # If no texture is specified, use the SIDE texture as it allows for blank brick textures.
                texture = "SIDE"

            # A tuple cannot be used because the values are changed afterwards when the brick is rotated.
            quads.append([positions, normals, uvs, colors, texture])

    if count_tris > 0:
        logger.warning("  {} triangles degenerated to quads.".format(count_tris))

    if count_ngon > 0:
        logger.warning("  {} n-gons skipped.".format(count_ngon))

    # Create an empty list for each quad section.
    # This is my workaround to making a sort of dictionary where the keys are in insertion order.
    # The quads must be written in a specific order.
    # A tuple cannot be used because the values are changed afterwards when the brick is rotated.
    # TODO: Consider using a standard dictionary and worrying about the order when writing.
    sorted_quads = [[] for i in range(len(const.QUAD_SECTION_ORDER))]

    # Sort quads into sections.
    for quad in quads:
        # Calculate the section name the quad belongs to.
        # Get the index of that section name in the QUAD_SECTION_ORDER list.
        # Append the quad data to the list in the tuple at that index.
        sorted_quads[__sort_quad(quad, bounds_data.dimensions, properties.axis_blb_forward)].append(quad)

    return sorted_quads


def __format_blb_data(forward_axis, blb_data):
    """Formats the specified BLB data into the format required by the game and rotates the brick according to the specified forward axis.

    Args:
        forward_axis (string): The name of the Blender axis (enum value as string) that will point forwards in-game.
        blb_data (BLBData): A BLBData object containing the data to be written.

    Returns:
        The formatted and rotated BLB data ready for writing.
    """
    # Size

    # Swizzle the values according to the forward axis.
    if forward_axis == "POSITIVE_Y" or forward_axis == "NEGATIVE_Y":
        blb_data.brick_size = common.swizzle(blb_data.brick_size, "bac")
    # Else: Do nothing.

    # Collision

    for index, (center, dimensions) in enumerate(blb_data.collision):
        # Mirror center according to the forward axis. No idea why, but it works.
        # Swizzle the values according to the forward axis.
        if forward_axis == "POSITIVE_Y" or forward_axis == "NEGATIVE_Y":
            blb_data.collision[index] = (common.swizzle(__mirror(center, forward_axis), "bac"), common.swizzle(dimensions, "bac"))
        else:
            blb_data.collision[index] = (__mirror(center, forward_axis), dimensions)

    # Quads

    for section in blb_data.quads:
        for quad_data in section:
            # 0: positions
            # 1: normals
            # 2: uvs
            # 3: colors
            # 4: texture

            # Rotate the quads according to the defined forward axis to visually rotate the brick.
            for index, position in enumerate(quad_data[0]):
                quad_data[0][index] = common.rotate(position, forward_axis)

            # Normals also need to rotated.
            for index, normal in enumerate(quad_data[1]):
                quad_data[1][index] = common.rotate(normal, forward_axis)

    return blb_data


def process_blender_data(context, properties):
    """Processes the specified Blender data into a format that can be written in a BLB file.

    Args:
        context (Blender context object): A Blender object containing scene data.
        properties (Blender properties object): A Blender object containing user preferences.

    Returns:
        A BLBData object containing all the necessary information in the correct format for writing directly into a BLB file or None if there is no Blender data to export.
    """
    # Determine which objects to process.
    object_sequence = __get_object_sequence(context, properties)

    if len(object_sequence) > 0:
        # Process the definition objects (collision, brick grid, and bounds) first and separate the visible meshes from the object sequence.
        # This is done in a single function because it is faster: no need to iterate over the same sequence twice.
        result = __process_definition_objects(properties, object_sequence)
        blb_data = result[0]
        bounds_data = result[1]
        meshes = result[2]

        # Calculate the coverage data based on the brick size.
        blb_data.coverage = __process_coverage(properties, blb_data)

        # Processes the visible mesh data into the correct format for writing into a BLB file.
        blb_data.quads = __process_mesh_data(properties, bounds_data, meshes)

        # Format and return the data for writing.
        return __format_blb_data(properties.axis_blb_forward, blb_data)
    else:
        logger.error("Nothing to export.")
        return None
