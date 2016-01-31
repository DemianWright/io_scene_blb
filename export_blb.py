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

class OutOfBoundsException(Exception):
    """An exception thrown when a vertex position is outside of brick bounds."""
    pass

class ZeroSizeException(Exception):
    """An exception thrown when a definition object has zero brick size on at least one axis."""
    pass

from mathutils import Vector
from math import ceil
from decimal import Decimal, Context, setcontext, ROUND_HALF_UP

# Number of decimal places to round floating point numbers.
FLOATING_POINT_DECIMALS = 6
FLOATING_POINT_PRECISION = Decimal("0.000001")

# Set the Decimal number context: 6 decimal points and 0.5 is rounded up.
setcontext(Context(prec=FLOATING_POINT_DECIMALS, rounding=ROUND_HALF_UP))

def is_even(value):
    """Returns True if given value is divisible by 2."""
    return value % 2 == 0

def to_decimal(value, decimals=FLOATING_POINT_DECIMALS):
    """Converts the given value to a Decimal value with up to 6 decimal places of precision."""

    if decimals > FLOATING_POINT_DECIMALS:
        decimals = FLOATING_POINT_DECIMALS

    # First convert float to string with n decimal digits and then make a Decimal out of it.
    return Decimal(("{0:." + str(decimals) + "f}").format(value))

def round_value(value, precision=1.0, decimals=FLOATING_POINT_DECIMALS):
    """Returns the given value as Decimal rounded to the given precision (default 1.0) and decimal places (default FLOATING_POINT_DECIMALS)."""

    # Creating decimals through strings is more accurate than floating point numbers.
    fraction = Decimal("1.0") / to_decimal(precision, decimals)
    # I'm not entirely sure what the Decimal("1.0") bit does but it works.
    return to_decimal((value * fraction).quantize(Decimal("1")) / fraction)

def round_values(values, precision=None, decimals=FLOATING_POINT_DECIMALS):
    """Returns a new list of Decimal values with the values of the given array rounded to the given precision (default no rounding) and decimal places (default FLOATING_POINT_DECIMALS)."""

    result = []

    if precision is None:
        for val in values:
            result.append(to_decimal(val, decimals))
    else:
        for val in values:
            result.append(round_value(val, precision, decimals))

    return result

def force_to_int(values):
    """Returns a new list of array values casted to integers."""
    result = []

    for val in values:
        result.append(int(val))

    return result

def are_not_ints(values):
    """
    Returns True if at least one value in the given list is not numerically equal to its integer counterparts.
    '1.000' is numerically equal to '1' while '1.001' is not.
    """

    for val in values:
        if val != int(val):
            return True

### EXPORT FUNCTION ###

def export(context, props, logger, filepath=""):
    """Processes the data from the scene and writes it to a BLB file."""

    # Constants.

    INDEX_X = 0
    INDEX_Y = 1
    INDEX_Z = 2

    # Error allowed for manually created definition objects. Used for rounding vertex positions to the brick grid.
    HUMAN_ERROR = Decimal("0.1")

    # Numerical constants.
    PLATE_HEIGHT = Decimal("0.4")  # A Blockland brick (plate) with dimensions 1 x 1 x 1 is equal to 1.0 x 1.0 x 0.4 Blender units (X,Y,Z)

    # Object name constants.
    BOUNDS_NAME_PREFIX = "bounds"
    COLLISION_PREFIX = "collision"
    GRID_X_PREFIX = "gridx"
    GRID_DASH_PREFIX = "grid-"
    GRID_U_PREFIX = "gridu"
    GRID_D_PREFIX = "gridd"
    GRID_B_PREFIX = "gridb"

    # Brick grid constants.
    GRID_INSIDE = 'x'  # Disallow building inside brick.
    GRID_OUTSIDE = '-'  # Allow building in empty space.
    GRID_UP = 'u'  # Allow placing bricks above this plate.
    GRID_DOWN = 'd'  # Allow placing bricks below this plate.
    GRID_BOTH = 'b'  # Allow placing bricks above and below this plate.

    # Brick grid definition object names in priority order.
    BRICK_GRID_DEFINITIONS_PRIORITY = (GRID_X_PREFIX, GRID_DASH_PREFIX, GRID_U_PREFIX, GRID_D_PREFIX, GRID_B_PREFIX)

    BRICK_GRID_DEFINITIONS = { GRID_X_PREFIX: GRID_INSIDE,
                               GRID_DASH_PREFIX: GRID_OUTSIDE,
                               GRID_U_PREFIX: GRID_UP,
                               GRID_D_PREFIX: GRID_DOWN,
                               GRID_B_PREFIX: GRID_BOTH }

    # Bounds object data needed in several functions.
    bounds_data = { "name": None,
                    "brick_size": [],
                    "dimensions": [],
                    "world_coords_min": [],
                    "world_coords_max": [] }

    ### BEGIN EXPORT FUNCTION NESTED FUNCTIONS ###

    def calc_quad_section(quad, bounds_min, bounds_max):
        if all(map(lambda q: q[2] == bounds_max[2], quad[0])):
            return "top"
        if all(map(lambda q: q[2] == bounds_min[2], quad[0])):
            return "bottom"
        if all(map(lambda q: q[1] == bounds_max[1], quad[0])):
            return "north"
        if all(map(lambda q: q[1] == bounds_min[1], quad[0])):
            return "south"
        if all(map(lambda q: q[0] == bounds_max[0], quad[0])):
            return "east"
        if all(map(lambda q: q[0] == bounds_min[0], quad[0])):
            return "west"

        return "omni"

    def get_world_min(obj):
        """Returns a new Vector(X,Y,Z) of the minimum world space coordinates of the given object."""

        vec_min = Vector((float("+inf"), float("+inf"), float("+inf")))

        for vert in obj.data.vertices:
            # Local coordinates to world space.
            coord = obj.matrix_world * vert.co

            vec_min[INDEX_X] = min(vec_min[INDEX_X], coord[INDEX_X])
            vec_min[INDEX_Y] = min(vec_min[INDEX_Y], coord[INDEX_Y])
            vec_min[INDEX_Z] = min(vec_min[INDEX_Z], coord[INDEX_Z])

        return vec_min

    def set_world_min_max(array_min, array_max, obj):
        """Updates the given arrays by assigning the minimum and maximum world space coordinates of the given object to the minimum and maximum arrays respectively."""

        for vert in obj.data.vertices:
            coord = obj.matrix_world * vert.co

            array_min[INDEX_X] = min(array_min[INDEX_X], coord[INDEX_X])
            array_min[INDEX_Y] = min(array_min[INDEX_Y], coord[INDEX_Y])
            array_min[INDEX_Z] = min(array_min[INDEX_Z], coord[INDEX_Z])

            array_max[INDEX_X] = max(array_max[INDEX_X], coord[INDEX_X])
            array_max[INDEX_Y] = max(array_max[INDEX_Y], coord[INDEX_Y])
            array_max[INDEX_Z] = max(array_max[INDEX_Z], coord[INDEX_Z])

    def world_to_local(world_position, local_bounds_object=None):
        """
        Translates the given world space position so it is relative to the geometric center of the given local space bounds.
        If no local_bounds_object is defined, data from bounds_data is used.
        Returns a list of rounded Decimal type local coordinates.
        """

        if local_bounds_object is not None:
            bounds_min = get_world_min(local_bounds_object)
            dimensions = local_bounds_object.dimensions
        else:
            # Use the bounds object data.
            bounds_min = bounds_data["world_coords_min"]
            dimensions = bounds_data["dimensions"]

        local_center = round_values((bounds_min[INDEX_X] + (dimensions[INDEX_X] / 2),
                                     bounds_min[INDEX_Y] + (dimensions[INDEX_Y] / 2),
                                     bounds_min[INDEX_Z] + (dimensions[INDEX_Z] / 2)))

        # If given position is in Decimals do nothing.
        if isinstance(world_position[0], Decimal):
            world = world_position
        else:
            # Otherwise convert to Decimal.
            world = round_values(world_position)

        local = []

        for index, value in enumerate(world):
            local.append(value - local_center[index])

        return round_values(local)

    def array_z_to_plates(xyz):
        """
        Performs round_values(array) on the given array and scales the Z component to match Blockland plates.
        If the given array does not have exactly three components (assumed format is (X, Y, Z)) the input is returned unchanged.
        """

        if len(xyz) == 3:
            array = round_values(xyz)
            array[INDEX_Z] /= PLATE_HEIGHT
            return array
        else:
            return xyz

    def round_to_plate_coordinates(coordinates, brick_dimensions):
        """
        Rounds the given array of XYZ coordinates to the nearest valid plate coordinates in a brick with the specified dimensions.
        Returns a list of rounded Decimal values.
        """

        result = []
        # 1 plate is 1.0 Blender units wide and deep.
        # Plates can only be 1.0 units long on the X and Y axes.
        # Valid plate positions exist every 0.5 units on odd sized bricks and every 1.0 units on even sized bricks.
        if is_even(brick_dimensions[INDEX_X]):
            result.append(round_value(coordinates[INDEX_X], 1.0))
        else:
            result.append(round_value(coordinates[INDEX_X], 0.5))

        if is_even(brick_dimensions[INDEX_Y]):
            result.append(round_value(coordinates[INDEX_Y], 1.0))
        else:
            result.append(round_value(coordinates[INDEX_Y], 0.5))

        # Round to the nearest full plate height. (Half is rounded up)
        if is_even(brick_dimensions[INDEX_Z] / PLATE_HEIGHT):
            result.append(round_value(coordinates[INDEX_Z], PLATE_HEIGHT))
        else:
            result.append(round_value(coordinates[INDEX_Z], (PLATE_HEIGHT / Decimal("2.0"))))

        return result

    def brick_grid_obj_to_index_ranges(obj):
        """
        Note: This function assumes that it is called after the bounds object has been defined.
        Calculates the brick grid definition index range [min, max[ for each axis from the vertex coordinates of the given object.
        The indices represent a three dimensional volume in the local space of the bounds object.
        Returns a tuple in the following format: ( (min_x, max_x), (min_y, max_y), (min_z, max_z) )
        Can raise OutOfBoundsException and ZeroSizeException.
        """

        out_of_bounds = False

        halved_dimensions = [value / 2 for value in bounds_data["dimensions"]]

        # Find the minimum and maximum coordinates for the brick grid object.
        grid_min = Vector((float("+inf"), float("+inf"), float("+inf")))
        grid_max = Vector((float("-inf"), float("-inf"), float("-inf")))
        set_world_min_max(grid_min, grid_max, obj)

        # Recenter the coordinates to the bounds. (Also rounds the values.)
        grid_min = world_to_local(grid_min)
        grid_max = world_to_local(grid_max)

        # Round coordinates to the nearest plate.
        grid_min = round_to_plate_coordinates(grid_min, bounds_data["dimensions"])
        grid_max = round_to_plate_coordinates(grid_max, bounds_data["dimensions"])

        # Check if any coordinates are beyond the local brick bounds.
        # Local brick bounds can be calculated from the bounds dimensions:
        # dimension / 2 = local max coordinate
        # -dimension / 2 = local min coordinate
        for index, value in enumerate(grid_min):
            if value < -(halved_dimensions[index]):
                out_of_bounds = True
                break

        if not out_of_bounds:
            for index, value in enumerate(grid_max):
                if value > halved_dimensions[index]:
                    out_of_bounds = True
                    break

        if out_of_bounds:
            logger.error("Error: Brick grid definition object '{}' has vertices outside the bounds definition object '{}'. Definition ignored.".format(obj.name, bounds_data["name"]))
            raise OutOfBoundsException()
        else:
            # Convert the coordinates into brick grid array indices.
            grid_min[INDEX_X] = grid_min[INDEX_X] + halved_dimensions[INDEX_X]  # Translate coordinates to positive X axis.
            grid_min[INDEX_Y] = grid_min[INDEX_Y] - halved_dimensions[INDEX_Y]  # Translate coordinates to negative Y axis.
            grid_min[INDEX_Z] = (grid_min[INDEX_Z] - halved_dimensions[INDEX_Z]) / PLATE_HEIGHT  # Translate coordinates to negative Z axis, height to plates.

            grid_max[INDEX_X] = grid_max[INDEX_X] + halved_dimensions[INDEX_X]
            grid_max[INDEX_Y] = grid_max[INDEX_Y] - halved_dimensions[INDEX_Y]
            grid_max[INDEX_Z] = (grid_max[INDEX_Z] - halved_dimensions[INDEX_Z]) / PLATE_HEIGHT

            # Swap min/max Z index and make it positive. Index 0 = top of the brick.
            temp = grid_min[INDEX_Z]
            grid_min[INDEX_Z] = abs(grid_max[INDEX_Z])
            grid_max[INDEX_Z] = abs(temp)

            # Swap min/max Y index and make it positive. Index 0 = back of the brick.
            temp = grid_min[INDEX_Y]
            grid_min[INDEX_Y] = abs(grid_max[INDEX_Y])
            grid_max[INDEX_Y] = abs(temp)

            grid_min = force_to_int(grid_min)
            grid_max = force_to_int(grid_max)

            zero_size = False

            # Convert min/max ranges to size.
            for index, value in enumerate(grid_max):
                size = (value - grid_min[index])

                if size == 0:
                    zero_size = True
                    break

            if zero_size:
                logger.error("Error: Brick grid definition object '{}' has zero size on at least one axis. Definition ignored.".format(obj.name))
                raise ZeroSizeException()
            else:
                # Return the index ranges as a tuple: ( (min_x, max_x), (min_y, max_y), (min_z, max_z) )
                return ((grid_min[INDEX_X], grid_max[INDEX_X]),
                        (grid_min[INDEX_Y], grid_max[INDEX_Y]),
                        (grid_min[INDEX_Z], grid_max[INDEX_Z]))

    def write_file(filepath, quads, definitions):
        """Write the BLB file."""

        # For clarity.
        size_x = definitions[BOUNDS_NAME_PREFIX][INDEX_X]
        size_y = definitions[BOUNDS_NAME_PREFIX][INDEX_Y]
        size_z = definitions[BOUNDS_NAME_PREFIX][INDEX_Z]

        ### BEGIN WRITE_FILE FUNCTION NESTED FUNCTIONS ###

        def write_array(file, array, new_line=True):
            """
            Writes the values of the given array separated with spaces into the given file.
            An optional new line character is printed at the end of the line by default.
            """

            for index, value in enumerate(array):
                if index != 0:
                    # Write a space before each value except the first one.
                    file.write(" ")
                if value == 0:
                    # Handle zeros.
                    file.write("0")
                else:
                    # Format the value into string, remove all zeros from the end, then remove all periods.
                    file.write("{}".format(value).rstrip('0').rstrip('.'))
            if new_line:
                # Write a new line after all values.
                file.write("\n")

        def write_brick_grid(grid=None):
            """Writes the given brick grid to the file or if no parameter is given, writes the default brick grid according to the size of the brick."""

            if grid is not None:
                for y_slice in grid:
                    for x_row in y_slice:
                        # Join each X row of data without a separator.
                        file.write("".join(x_row))
                        file.write("\n")

                    # A new line after each Y slice.
                    file.write("\n")
            else:
                for y in range(size_y):
                    for z in range(size_z):
                        # Current Z index is 0 which is the top of the brick?
                        is_top = (z == 0)

                        # Current Z index is Z size - 1 which is the bottom of the brick?
                        is_bottom = (z == size_z - 1)

                        if is_bottom and is_top:
                            symbol = GRID_BOTH
                        elif is_bottom:
                            symbol = GRID_DOWN
                        elif is_top:
                            symbol = GRID_UP
                        else:
                            symbol = GRID_INSIDE

                        # Write the symbol X size times.
                        file.write(symbol * size_x)
                        file.write("\n")

                    # A new line after each Y slice.
                    file.write("\n")

        def modify_brick_grid(brick_grid, volume, symbol):
            """Modifies the given brick grid by adding the given symbol to every grid slot specified by the volume."""

            x_range = volume[INDEX_X]
            y_range = volume[INDEX_Y]
            z_range = volume[INDEX_Z]

            # y_index is the index of list of X row data.
            for y_index in range(y_range[0], y_range[1]):
                # z_index is the index of the X row data in y_index list.
                for z_index in range(z_range[0], z_range[1]):
                    # x_index is the index of the character in the X row data.
                    for x_index in range(x_range[0], x_range[1]):
                        # From this Y slice.
                        # Select the appropriate Z row.
                        # And for every X index, assign the correct symbol.
                        brick_grid[y_index][z_index][x_index] = symbol

        ### END WRITE_FILE FUNCTION NESTED FUNCTIONS ###

        ### BEGIN WRITE_FILE FUNCTION ###

        with open(filepath, "w") as file:
            # Write brick size.
            write_array(file, definitions[BOUNDS_NAME_PREFIX])

            # Write brick type.
            file.write("SPECIAL\n\n")

            # Write brick grid.
            if len(definitions[GRID_B_PREFIX]) == 0 and len(definitions[GRID_D_PREFIX]) == 0 and len(definitions[GRID_U_PREFIX]) == 0 and len(definitions[GRID_X_PREFIX]) == 0:
                # No brick grid definitions, write default grid.
                write_brick_grid()
            else:
                # Initialize the brick grid with the empty symbol with the dimensions of the brick.
                brick_grid = [[[GRID_OUTSIDE for x in range(size_x)] for z in range(size_z)] for y in range(size_y)]

                for name_prefix in BRICK_GRID_DEFINITIONS_PRIORITY:
                    if len(definitions[name_prefix]) > 0:
                        for volume in definitions[name_prefix]:
                            modify_brick_grid(brick_grid, volume, BRICK_GRID_DEFINITIONS.get(name_prefix))

                write_brick_grid(brick_grid)

            # Write collisions.
            collision_cubes = (((0, 0, 0), (size_x, size_y, size_z)),)

            file.write(str(len(collision_cubes)))
            file.write("\n")

            for (center, size) in collision_cubes:
                file.write("\n")
                write_array(file, center)
                write_array(file, size)

            # Write coverage.
            file.write("COVERAGE:\n")

            # TBNESW
            for i in range(6):
                file.write("0 : 999\n")

            # Write quad data.
            # Section names must be in lower case for some reason.
            for section_name in ("top", "bottom", "north", "east", "south", "west", "omni"):
                section_quads = tuple(map(lambda t: t[0], filter(lambda t: t[1] == section_name, quads)))

                # TODO: Terse mode where optional stuff is excluded.

                # Write section name.
                file.write("--{} QUADS--\n".format(section_name.upper()))  # Optional.

                # Write section length.
                file.write("{}\n".format(str(len(section_quads))))

                for (positions, normals, uvs, colors, texture) in section_quads:
                    # Write face texture name.
                    file.write("\nTEX:")  # Optional.
                    file.write(texture)

                    # TODO: Fix incorrect model rotation. -Y in Blender is +X in-game.

                    # Write vertex positions.
                    file.write("\nPOSITION:\n")  # Optional.
                    for position in positions:
                        write_array(file, position)

                    # Write face UV coordinates.
                    file.write("UV COORDS:\n")  # Optional.
                    for uv_vector in uvs:
                        write_array(file, uv_vector)

                    # Write vertex normals.
                    file.write("NORMALS:\n")  # Optional.
                    for normal in normals:
                        write_array(file, normal)

                    # Write vertex colors if any.
                    if colors is not None:
                        file.write("COLORS:\n")  # Optional.
                        for color in colors:
                            write_array(file, color)

    ### END EXPORT FUNTION NESTED FUNCTIONS ###

    ### EXPORT FUNCTION BEGIN ###

    definition_data = {BOUNDS_NAME_PREFIX: None,
                       COLLISION_PREFIX: None,
                       GRID_X_PREFIX: [],
                       GRID_DASH_PREFIX: [],
                       GRID_U_PREFIX: [],
                       GRID_D_PREFIX: [],
                       GRID_B_PREFIX: []}

    vec_bounding_box_min = Vector((float("+inf"), float("+inf"), float("+inf")))
    vec_bounding_box_max = Vector((float("-inf"), float("-inf"), float("-inf")))

    a_quads = []
    n_tris = 0
    n_ngon = 0
    bounds_object = None

    # TODO: Layer support.
    # TODO: Exporting multiple bricks from a single file.

    # Use selected objects?
    if props.use_selection:
        logger.log("Exporting selection to BLB.")
        objects = context.selected_objects

        object_count = len(objects)

        if object_count != 1:
            logger.log("Found {} objects".format(len(objects)))

            if object_count == 0:
                logger.log("No objects selected.")
                props.use_selection = False
        else:
            logger.log("Found {} object.".format(len(objects)))

    # Get all scene objects.
    if not props.use_selection:
        logger.log("Exporting scene to BLB.")
        objects = context.scene.objects

        object_count = len(objects)

        if object_count != 1:
            logger.log("Found {} objects.".format(len(objects)))

            if object_count == 0:
                logger.log("No objects in the scene.")
        else:
            logger.log("Found {} object.".format(len(objects)))

    # Search for the bounds object.
    for obj in objects:
        # Object name starts with the bounds object definition name?
        if obj.name.lower().startswith(BOUNDS_NAME_PREFIX):
            if obj.type != "MESH":
                logger.warning("Warning: Object '{}' cannot be used to define bounds, must be a mesh.".format(obj.name))
                # Continue searching in case mesh bounds is found.
            else:
                bounds_object = obj
                bounds_data["name"] = obj.name
                bounds_data["dimensions"] = round_values(obj.dimensions)

                # Find the minimum and maximum world coordinates for the bounds object.
                bounds_min = Vector((float("+inf"), float("+inf"), float("+inf")))
                bounds_max = Vector((float("-inf"), float("-inf"), float("-inf")))
                set_world_min_max(bounds_min, bounds_max, bounds_object)

                bounds_data["world_coords_min"] = round_values(bounds_min)
                bounds_data["world_coords_max"] = round_values(bounds_max)

                # Get the dimensions of the Blender object and convert the height to plates.
                bounds_size = array_z_to_plates(obj.dimensions)

                # Are the dimensions of the bounds object integers?
                if are_not_ints(bounds_size):
                    logger.warning("Warning: Defined bounds has a non-integer size {} {} {}, rounding to a precision of {}.".format(bounds_size[INDEX_X],
                                                                                                                                    bounds_size[INDEX_Y],
                                                                                                                                    bounds_size[INDEX_Z],
                                                                                                                                    HUMAN_ERROR))
                    for index, value in enumerate(bounds_size):
                        # Round to the specified error amount and force to int.
                        bounds_size[index] = round(HUMAN_ERROR * round(value / HUMAN_ERROR))

                # The value type must be int because you can't have partial plates. Returns a list.
                definition_data[BOUNDS_NAME_PREFIX] = force_to_int(bounds_size)
                bounds_data["brick_size"] = definition_data[BOUNDS_NAME_PREFIX]

                # Bounds object found and processed, break the loop.
                break
    else:
        logger.warning("Warning: No 'bounds' object found. Automatically calculated brick size and brick grid may be undesirable.")
        # Brick size calculation must be performed after all other objects are processed.

    # TODO: Check that every vertex is within manually defined bounds.

    brick_grid_objects_found = 0
    brick_grid_objects_processed = 0

    for obj in objects:
        # Ignore all non-mesh objects and the bounds object.
        if obj.type != "MESH" or obj == bounds_object:
            continue
        elif obj.name.lower().startswith(BRICK_GRID_DEFINITIONS_PRIORITY):
            # Object name starts with one of the brick grid definition object name prefixes.
            brick_grid_objects_found += 1

            # Brick grid can only be defined if the brick bounds have been defined.
            if bounds_object is not None:
                try:
                    # All brick grid definition object names are exactly 5 characters long and lower case.
                    definition_data[obj.name.lower()[:5]].append(brick_grid_obj_to_index_ranges(obj))
                    brick_grid_objects_processed += 1
                except OutOfBoundsException:
                    # Do nothing, definition is ignored.
                    pass
                except ZeroSizeException:
                    # Do nothing, definition is ignored.
                    pass

            # Skip the rest of the loop as definition objects are not to be exported as models.
            continue

        logger.log("Exporting mesh: {}".format(obj.name))

        # Record the minimum and maximum vertex coordinates only if no bounds was defined.
        if bounds_object is None:
            set_world_min_max(vec_bounding_box_min, vec_bounding_box_max, obj)

        current_data = obj.data

        # UV layers exist.
        if current_data.uv_layers:
            if len(current_data.uv_layers) > 1:
                logger.warning("Warning: Mesh '{}' has {} UV layers, using the 1st.".format(obj.name, len(current_data.uv_layers)))

            uv_data = current_data.uv_layers[0].data
        else:
            uv_data = None

        def index_to_position(index):
            """
            Returns the world coordinates for the vertex whose index was given in the current polygon loop.
            Additionally rounds the coordinates to Decimal and converts the height to plates with array_z_to_plates(array).
            """
            return array_z_to_plates(obj.matrix_world * current_data.vertices[current_data.loops[index].vertex_index].co)

        def index_to_normal(index):
            return (obj.matrix_world.to_3x3() * current_data.vertices[current_data.loops[index].vertex_index].normal).normalized()

        # Faces.
        for poly in current_data.polygons:
            # Vertex positions
            if poly.loop_total == 4:
                # Quad.
                loop_indices = tuple(poly.loop_indices)
            elif poly.loop_total == 3:
                # Tri.
                loop_indices = tuple(poly.loop_indices) + (poly.loop_start,)
                n_tris += 1
            else:
                # N-gon.
                n_ngon += 1
                continue

            positions = []

            # Reverse the loop_indices tuple. (Blender seems to keep opposite winding order.)
            for index in reversed(loop_indices):
                # Get the world position from the index. (This rounds it and converts the height to plates.)
                # Center the position to the current bounds object.
                positions.append(world_to_local(index_to_position(index)))

            # FIXME: Object rotation affects normals.

            # Normals.
            # They are kept as floats for maximum accuracy.
            # Use smooth shading?
            if poly.use_smooth:
                # For every element in the loop_indices tuple.
                # Run it through the index_to_normal(index) function. (This rounds it and converts the height to plates.)
                # And assign the result to the normals tuple.
                normals = tuple(map(index_to_normal, loop_indices))
            else:
                # No smooth shading, every vertex in this loop has the same normal.
                normals = (poly.normal,) * 4

            # UVs
            if uv_data:
                uvs = tuple(map(lambda index: uv_data[index].uv, loop_indices))
            else:
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

            a_quads.append((positions, normals, uvs, colors, texture))

    # Log messages for brick grid definitions.
    if brick_grid_objects_found == 0:
        logger.warning("Warning: No brick grid definitions found. Default brick grid may be undesirable.")
    else:
        if bounds_object is not None:
            if brick_grid_objects_found == 1:
                if brick_grid_objects_processed == 0:
                    logger.warning("Warning: {} brick grid definition found but was not processed.".format(brick_grid_objects_found))
            else:
                if brick_grid_objects_processed == 0:
                    logger.warning("Warning: {} brick grid definitions found but were not processed.".format(brick_grid_objects_found))
            if brick_grid_objects_found == 1:
                logger.log("Processed {} of {} brick grid definition.".format(brick_grid_objects_processed, brick_grid_objects_found))
            else:
                logger.log("Processed {} of {}  brick grid definitions.".format(brick_grid_objects_processed, brick_grid_objects_found))
        elif brick_grid_objects_found == 1:
            logger.warning("Warning: {} brick grid definition found but was not processed because bounds definition was missing.".format(brick_grid_objects_found))
        else:
            logger.warning("Warning: {} brick grid definitions found but were not processed because bounds definition was missing.".format(brick_grid_objects_found))

    # No manually created bounds object was found, calculate brick size according to the combined minimum and maximum vertex positions of all processed meshes.
    if bounds_object is None:
        # Get the dimensions defined by the vectors and convert height to plates.
        bounds_size = round_values((vec_bounding_box_max[INDEX_X] - vec_bounding_box_min[INDEX_X],
                                    vec_bounding_box_max[INDEX_Y] - vec_bounding_box_min[INDEX_Y],
                                    (vec_bounding_box_max[INDEX_Z] - vec_bounding_box_min[INDEX_Z])))
        bounds_size = array_z_to_plates(bounds_size)

        # Are the dimensions of the bounds object integers?
        if bounds_size[INDEX_X] != int(bounds_size[INDEX_X]) or bounds_size[INDEX_Y] != int(bounds_size[INDEX_Y]) or bounds_size[INDEX_Z] != int(bounds_size[INDEX_Z]):
            logger.warning("Warning: Defined bounds has a non-integer size {} {} {}, rounding up.".format(bounds_size[INDEX_X],
                                                                                                          bounds_size[INDEX_Y],
                                                                                                          bounds_size[INDEX_Z]))
            # In case height conversion or rounding introduced floating point errors, round up to be on the safe side.
            for index, value in enumerate(bounds_size):
                bounds_size[index] = ceil(value)

        # The value type must be int because you can't have partial plates. Returns a list.
        definition_data[BOUNDS_NAME_PREFIX] = force_to_int(bounds_size)

    logger.log("Brick size: {} {} {}".format(definition_data[BOUNDS_NAME_PREFIX][INDEX_X],
                                             definition_data[BOUNDS_NAME_PREFIX][INDEX_Y],
                                             definition_data[BOUNDS_NAME_PREFIX][INDEX_Z]))

    # Plate adjustment.
    vec_bounding_box_min = array_z_to_plates(vec_bounding_box_min)
    vec_bounding_box_max = array_z_to_plates(vec_bounding_box_max)

    # Group quads into sections.
    quads_with_sections = tuple(map(lambda q: (q, calc_quad_section(q, vec_bounding_box_min, vec_bounding_box_max)), a_quads))

    if n_tris:
        logger.warning("Warning: {} triangles degenerated to quads.".format(n_tris))

    if n_ngon:
        logger.warning("Warning: {} n-gons skipped.".format(n_ngon))

    # Write the data to a file.
    write_file(filepath, quads_with_sections, definition_data)
