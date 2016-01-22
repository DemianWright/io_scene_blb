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

from mathutils import Vector
from math import ceil
from decimal import Decimal, Context, setcontext, ROUND_HALF_UP

INDEX_X = 0
INDEX_Y = 1
INDEX_Z = 2

FLOATING_POINT_DECIMALS = 6

# Error allowed for manually created definition objects. Used for rounding vertex coordinates to the brick grid.
HUMAN_ERROR = 0.1

# Object name constants.
BOUNDS_NAME_PREFIX = "bounds"
COLLISION_PREFIX = "collision"
GRID_X_PREFIX = "gridx"
GRID_B_PREFIX = "gridb"
GRID_D_PREFIX = "gridd"
GRID_U_PREFIX = "gridu"

# Grid definition object names in priority order.
BRICK_GRID_DEFINITIONS_PRIORITY = (GRID_X_PREFIX, GRID_B_PREFIX, GRID_D_PREFIX, GRID_U_PREFIX)

# Set the Decimal number context: 6 decimal points and 0.5 is rounded up.
setcontext(Context(prec=FLOATING_POINT_DECIMALS, rounding=ROUND_HALF_UP))

# TODO: Move logger to this file.

def to_decimal(f, decimals=FLOATING_POINT_DECIMALS):
    """Converts the given float to a Decimal value with up to 6 decimal places of precision."""
    if decimals > 6:
        decimals = 6

    # First convert float to string with n decimal digits and then make a Decimal out of it.
    return Decimal(("{0:." + str(decimals) + "f}").format(f))

def round_vector_to_list(vector, decimals=FLOATING_POINT_DECIMALS):
    """Returns a new list of Decimal values with the values of the given vector rounded to the specified number of decimal places."""
    result = []

    for value in vector:
        result.append(to_decimal(value, decimals))

    return result

def write_vector(file, vec, new_line=True):
    """
    Writes the values of the given vector separated with spaces into the given file.
    An optional new line character is printed at the end of the line by default.
    """

    for i, dim in enumerate(vec):
        if i:
            file.write(" ")
        if dim == 0:
            file.write("0")
        elif dim == int(dim):
            file.write(str(int(dim)))
        else:
            file.write(str(dim))
    if new_line:
        file.write("\n")

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
    """Returns a new Vector(X,Y,Z) of the minimum world space vertex coordinates of the given object."""

    vec_min = Vector((float("+inf"), float("+inf"), float("+inf")))

    for vert in obj.data.vertices:
        coord = obj.matrix_world * vert.co

        vec_min[INDEX_X] = min(vec_min[INDEX_X], coord[INDEX_X])
        vec_min[INDEX_Y] = min(vec_min[INDEX_Y], coord[INDEX_Y])
        vec_min[INDEX_Z] = min(vec_min[INDEX_Z], coord[INDEX_Z])

    return vec_min

def set_world_min_max(vec_min, vec_max, obj):
    """Updates the given vectors by assigning the minimum and maximum world space vertex coordinates of the given object to the minimum and maximum vectors respectively."""

    for vert in obj.data.vertices:
        coord = obj.matrix_world * vert.co

        vec_min[INDEX_X] = min(vec_min[INDEX_X], coord[INDEX_X])
        vec_min[INDEX_Y] = min(vec_min[INDEX_Y], coord[INDEX_Y])
        vec_min[INDEX_Z] = min(vec_min[INDEX_Z], coord[INDEX_Z])

        vec_max[INDEX_X] = max(vec_max[INDEX_X], coord[INDEX_X])
        vec_max[INDEX_Y] = max(vec_max[INDEX_Y], coord[INDEX_Y])
        vec_max[INDEX_Z] = max(vec_max[INDEX_Z], coord[INDEX_Z])

def recenter(world_vector, local_bounds_object):
    """Returns a new Vector(X,Y,Z) where the coordinates of the given world space vector/array of coordinates have been translated so they are relative to the geometric center of the given local space bounds."""
    bounds_min = get_world_min(local_bounds_object)

    local_center = Vector((bounds_min[INDEX_X] + (local_bounds_object.dimensions[INDEX_X] / 2),
                           bounds_min[INDEX_Y] + (local_bounds_object.dimensions[INDEX_Y] / 2),
                           bounds_min[INDEX_Z] + (local_bounds_object.dimensions[INDEX_Z] / 2)))

    return Vector((world_vector[INDEX_X] - local_center[INDEX_X],
                   world_vector[INDEX_Y] - local_center[INDEX_Y],
                   world_vector[INDEX_Z] - local_center[INDEX_Z]))

def __write_file(filepath, quads, definitions):
    """Write the BLB file."""

    # For clarity.
    size_x = definitions[BOUNDS_NAME_PREFIX][INDEX_X]
    size_y = definitions[BOUNDS_NAME_PREFIX][INDEX_Y]
    size_z = definitions[BOUNDS_NAME_PREFIX][INDEX_Z]

    # Brick grid constants.
    GRID_INSIDE = "x"  # Disallow building inside brick.
    GRID_BOTH = "b"  # Allow placing bricks above and below this plate.
    GRID_DOWN = "d"  # Allow placing bricks below this plate.
    GRID_UP = "u"  # Allow placing bricks above this plate.
    GRID_OUTSIDE = "-"  # Allow building in empty space.

    with open(filepath, "w") as file:
        # Write brick size.
        write_vector(file, definitions[BOUNDS_NAME_PREFIX])

        # Write brick type.
        file.write("SPECIAL\n\n")

        # Write brick grid.
        for y_coord in range(size_y):
            for z_coord in range(size_z):
                is_top = z_coord == 0
                is_bot = z_coord == size_z - 1

                if is_bot and is_top:
                    mode = "b"
                elif is_bot:
                    mode = "d"
                elif is_top:
                    mode = "u"
                else:
                    mode = "X"

                file.write(mode * size_x)
                file.write("\n")

            file.write("\n")

        # Write collisions.
        collision_cubes = (((0, 0, 0), (size_x, size_y, size_z)),)

        file.write(str(len(collision_cubes)))
        file.write("\n")

        for (center, size) in collision_cubes:
            file.write("\n")
            write_vector(file, center)
            write_vector(file, size)

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
                    write_vector(file, position)

                # Write face UV coordinates.
                file.write("UV COORDS:\n")  # Optional.
                for uv_vector in uvs:
                    write_vector(file, uv_vector)

                # Write vertex normals.
                file.write("NORMALS:\n")  # Optional.
                for normal in normals:
                    write_vector(file, normal)

                # Write vertex colors if any.
                if colors is not None:
                    file.write("COLORS:\n")  # Optional.
                    for color in colors:
                        write_vector(file, color)

def export(context, props, logger, filepath=""):
    """Processes the data from the scene and writes it to a BLB file."""

    # TODO: Exporting multiple bricks from a single file.

    # Numerical constants.
    PLATE_HEIGHT = 0.4  # (1, 1, 1) Blockland plate = (1.0, 1.0, 0.4) Blender units (X,Y,Z)

    definition_data = {BOUNDS_NAME_PREFIX: None,
                       COLLISION_PREFIX: None,
                       GRID_U_PREFIX: [],
                       GRID_X_PREFIX: [],
                       GRID_D_PREFIX: [],
                       GRID_B_PREFIX: []}

    vec_bounding_box_min = Vector((float("+inf"), float("+inf"), float("+inf")))
    vec_bounding_box_max = Vector((float("-inf"), float("-inf"), float("-inf")))

    a_quads = []
    n_tris = 0
    n_ngon = 0
    bounds_object = None

    # TODO: Layer support.

    def vector_z_to_plates(vec_xyz):
        """Returns a new Vector(X,Y,Z) where the Z component of the given vector is scaled to match Blockland plates.
        If the given vector does not have exactly three components (assumed format is (X, Y, Z)) the input is returned unchanged."""
        if len(vec_xyz) == 3:
            return Vector((vec_xyz[INDEX_X], vec_xyz[INDEX_Y], vec_xyz[INDEX_Z] / PLATE_HEIGHT))
        else:
            return vec_xyz

    def force_to_int(vector):
        """Returns a new list of vector values casted to integers."""
        result = []

        for value in vector:
            result.append(int(value))

        return result

    def brick_grid_obj_to_index_ranges(obj, bounds_object):
        """
        Calculates the brick grid definition index range (inclusive) for each axis from the vertex coordinates of the given object.
        The indices represent a three dimensional volume in the local space of the given bounds object.
        Returns a tuple in the following format: ( (min_x, max_x), (min_y, max_y), (min_z, max_z) )
        """

        # Find the minimum and maximum coordinates for the brick grid object.
        grid_min = Vector((float("+inf"), float("+inf"), float("+inf")))
        grid_max = Vector((float("-inf"), float("-inf"), float("-inf")))
        set_world_min_max(grid_min, grid_max, obj)

        # Recenter the coordinates to the bounding box.
        grid_min = recenter(grid_min, bounds_object)
        grid_max = recenter(grid_max, bounds_object)

        dimensions = bounds_object.dimensions

        # Convert the coordinates into brick grid array indices. (Floating point error still present.)
        grid_min.x = grid_min.x + (dimensions.x / 2)
        grid_min.y = grid_min.y + (dimensions.y / 2)
        grid_min.z = (grid_min.z - (dimensions.z / 2)) / PLATE_HEIGHT

        grid_max.x = grid_max.x + (dimensions.x / 2)
        grid_max.y = grid_max.y + (dimensions.y / 2)
        grid_max.z = (grid_max.z - (dimensions.z / 2)) / PLATE_HEIGHT

        # Swap around min/max Z index and make it positive. Index 0 = top of the brick.
        temp = grid_min.z
        grid_min.z = abs(grid_max.z)
        grid_max.z = abs(temp)

        # Floating point error eliminated.
        grid_min = round_vector_to_list(grid_min)
        grid_max = round_vector_to_list(grid_max)

        non_int = False

        # Are the minimum and maximum indices of the grid object integers?
        for value in grid_min:
            if value != int(value):
                non_int = True
                break
        else:
            for value in grid_max:
                if value != int(value):
                    non_int = True
                    break

        if non_int:
            logger.warning("Warning: '{}' has a non-integer size {} {} {}, rounding to a precision of {}.".format(obj.name,
                                                                                                                  grid_max[INDEX_X] - grid_min[INDEX_X],
                                                                                                                  grid_max[INDEX_Y] - grid_min[INDEX_Y],
                                                                                                                  grid_max[INDEX_Z] - grid_min[INDEX_Z],
                                                                                                                  HUMAN_ERROR))
            # FIXME: Temporarily making a Decimal out of the human error value. Fix later when bounds calculation and detection has been converted to use Decimals as well.

            # Round indices up the nearest integer. (Floating point error fixed.)
            for index, value in enumerate(grid_min):
                grid_min[index] = round(HUMAN_ERROR * round(value / Decimal(HUMAN_ERROR)))

            for index, value in enumerate(grid_max):
                grid_max[index] = round(HUMAN_ERROR * round(value / Decimal(HUMAN_ERROR)))

        # The value type must be int because you can't have partial plates. Returns a list.
        grid_min = force_to_int(grid_min)

        # grid_max values are indices. Subtract one to prevent the index from going out of bounds.
        for index, value in enumerate(grid_max):
            grid_max[index] = int(value) - 1

        # Return the index ranges as a tuple: ( (min_x, max_x), (min_y, max_y), (min_z, max_z) )
        return ( (grid_min[INDEX_X], grid_max[INDEX_X]),
                 (grid_min[INDEX_Y], grid_max[INDEX_Y]),
                 (grid_min[INDEX_Z], grid_max[INDEX_Z]) )

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
        # Manually created bounds object?
        if obj.name.lower().startswith(BOUNDS_NAME_PREFIX):
            if obj.type != "MESH":
                logger.warning("Warning: Object '{}' cannot be used to define bounds, must be a mesh.".format(obj.name))
                # Continue searching in case a mesh bounds is found.
            else:
                bounds_object = obj

                # Get the dimensions of the Blender object and convert the height to plates.
                bounds_size = Vector((obj.dimensions[INDEX_X],
                                      obj.dimensions[INDEX_Y],
                                      obj.dimensions[INDEX_Z] / PLATE_HEIGHT))

                # Are the dimensions of the bounds object integers?
                if bounds_size[INDEX_X] != int(bounds_size[INDEX_X]) or bounds_size[INDEX_Y] != int(bounds_size[INDEX_Y]) or bounds_size[INDEX_Z] != int(bounds_size[INDEX_Z]):
                    logger.warning("Warning: Defined bounds has a non-integer size {} {} {}, rounding to a precision of {}.".format(bounds_size.x,
                                                                                                                                    bounds_size.y,
                                                                                                                                    bounds_size.z,
                                                                                                                                    HUMAN_ERROR))
                    for index, value in enumerate(bounds_size):
                        # Round to the specified error amount and force to int.
                        bounds_size[index] = round(HUMAN_ERROR * round(value / HUMAN_ERROR))

                # The value type must be int because you can't have partial plates. Returns a list.
                definition_data[BOUNDS_NAME_PREFIX] = force_to_int(bounds_size)

                # Bounds object found and processed, break the loop.
                break
    else:
        logger.warning("Warning: No 'bounds' object found. Automatically calculated brick size may be undesirable.")
        # Brick size calculation must be performed after all other objects are processed.

    # TODO: Check that every vertex is within manually defined bounds.
    # TODO: Check that grid objects are within bounds.

    brick_grid_objects = 0

    for obj in objects:
        # Ignore all non-mesh objects and certain special objects.
        if obj.type != "MESH" or obj.name.lower().startswith(BOUNDS_NAME_PREFIX):
            continue
        elif obj.name.lower().startswith(BRICK_GRID_DEFINITIONS_PRIORITY):
            # TODO: Make this work without a bounds object.

            # All brick grid definition object names are exactly 5 characters long and lower case.
            definition_data[obj.name.lower()[:5]].append(brick_grid_obj_to_index_ranges(obj, bounds_object))

            brick_grid_objects += 1

            # Skip the rest of the loop as definition objects are not to be exported as models.
            continue

        logger.log("Exporting mesh: {}".format(obj.name))

        # Current object is not the bounds object, record the minimum and maximum vertex coordinates.
        if not definition_data[BOUNDS_NAME_PREFIX]:
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
            vec = obj.matrix_world * current_data.vertices[current_data.loops[index].vertex_index].co
            return vector_z_to_plates(vec)

        def index_to_normal(index):
            return (obj.matrix_world.to_3x3() * current_data.vertices[current_data.loops[index].vertex_index].normal).normalized()

        # Faces.
        for poly in current_data.polygons:
            # Vertex positions
            if poly.loop_total == 4:
                loop_indices = tuple(poly.loop_indices)
            elif poly.loop_total == 3:
                loop_indices = tuple(poly.loop_indices) + (poly.loop_start,)
                n_tris += 1
            else:
                n_ngon += 1
                continue

            positions = tuple(map(index_to_position, loop_indices))
            # Blender seems to keep opposite winding order
            positions = tuple(reversed(positions))

            # Smooth shading
            if poly.use_smooth:
                normals = tuple(map(index_to_normal, loop_indices))
            else:
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

    if brick_grid_objects == 0:
        logger.warning("Warning: No brick grid definitions found. Default brick grid may be undesirable.")
    else:
        logger.log("Processed {} brick grid definitions.".format(brick_grid_objects))

    # No manually created bounds object was found, calculate brick size according to the minimum and maximum vertex coordinates.
    if definition_data[BOUNDS_NAME_PREFIX] is None:
        # Get the dimensions defined by the vectors and convert height to plates.
        bounds_size = Vector((vec_bounding_box_max[INDEX_X] - vec_bounding_box_min[INDEX_X],
                              vec_bounding_box_max[INDEX_Y] - vec_bounding_box_min[INDEX_Y],
                              (vec_bounding_box_max[INDEX_Z] - vec_bounding_box_min[INDEX_Z]) / PLATE_HEIGHT))

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
    vec_bounding_box_min = vector_z_to_plates(vec_bounding_box_min)
    vec_bounding_box_max = vector_z_to_plates(vec_bounding_box_max)

    # Group quads into sections.
    quads_with_sections = tuple(map(lambda q: (q, calc_quad_section(q, vec_bounding_box_min, vec_bounding_box_max)), a_quads))

    if n_tris:
        logger.warning("Warning: {} triangles degenerated to quads.".format(n_tris))

    if n_ngon:
        logger.warning("Warning: {} n-gons skipped.".format(n_ngon))

    # Write the data to a file.
    __write_file(filepath, quads_with_sections, definition_data)
