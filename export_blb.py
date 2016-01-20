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

INDEX_X = 0
INDEX_Y = 1
INDEX_Z = 2

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

def set_min_max(vec_min, vec_max, obj):
    """Updates the given vectors assigning the minimum vertex coordinate of the given object to the minimum and maximum vertex coordinate to the maximum vector respectively."""

    for vert in obj.data.vertices:
        coord = obj.matrix_world * vert.co
        vec_min[INDEX_X] = min(vec_min[INDEX_X], coord[INDEX_X])
        vec_min[INDEX_Y] = min(vec_min[INDEX_Y], coord[INDEX_Y])
        vec_min[INDEX_Z] = min(vec_min[INDEX_Z], coord[INDEX_Z])
        vec_max[INDEX_X] = max(vec_max[INDEX_X], coord[INDEX_X])
        vec_max[INDEX_Y] = max(vec_max[INDEX_Y], coord[INDEX_Y])
        vec_max[INDEX_Z] = max(vec_max[INDEX_Z], coord[INDEX_Z])

def __write_file(filepath, brick_size, quads):
    """Write the BLB file."""

    # For clarity.
    size_x = brick_size[INDEX_X]
    size_y = brick_size[INDEX_Y]
    size_z = brick_size[INDEX_Z]

    # Brick grid constants.
    GRID_UP = "u"  # Allow placing bricks above this plate.
    GRID_INSIDE = "x"  # Disallow building inside brick.
    GRID_OUTSIDE = "-"  # Allow building in empty space.
    GRID_DOWN = "d"  # Allow placing bricks below this plate.
    GRID_BOTH = "b"  # Allow placing bricks above and below this plate.

    with open(filepath, "w") as file:
        # Write brick size.
        write_vector(file, brick_size)

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
            file.write("\n--{} QUADS--\n".format(section_name.upper()))  # Optional.

            # Write section length.
            file.write("{}\n".format(str(len(section_quads))))

            for (positions, normals, uvs, colors, texture) in section_quads:
                # Write face texture name.
                file.write("\nTEX:")  # Optional.
                file.write(texture)

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

    # Object name constants.
    BOUNDS_NAME_PREFIX = "bounds"
    COLLISION_PREFIX = "collision"
    GRID_U_PREFIX = "gridu"
    GRID_X_PREFIX = "gridx"
    GRID_D_PREFIX = "gridd"
    GRID_B_PREFIX = "gridb"
    
    # Numerical constants.
    PLATE_HEIGHT = 0.4 # (1, 1, 1) Blockland plate = (1.0, 1.0, 0.4) Blender units (X,Y,Z)

    special_objects = {BOUNDS_NAME_PREFIX: None,
                       COLLISION_PREFIX: None,
                       GRID_U_PREFIX: None,
                       GRID_X_PREFIX: None,
                       GRID_D_PREFIX: None,
                       GRID_B_PREFIX: None}

    vec_bounding_box_min = Vector((0, 0, 0))
    vec_bounding_box_max = Vector((0, 0, 0))

    a_quads = []
    n_tris = 0
    n_ngon = 0

    # TODO: Layer support.

    def vector_z_to_plates(xyz):
        """Returns a new tuple where the Z component of the given tuple is scaled to match Blockland plates.
        If the given Vector/tuple does not have three components (assumed format is (X, Y, Z)) the input is returned unchanged."""
        if len(xyz) > 2:
            return (xyz[INDEX_X], xyz[INDEX_Y], xyz[INDEX_Z] / PLATE_HEIGHT)
        else:
            return xyz

    # Use selected objects?
    if props.use_selection:
        logger.log("Exporting selection to BLB")
        objects = context.selected_objects

        object_count = len(objects)

        if object_count != 1:
            logger.log("Found {} objects".format(len(objects)))

            if object_count == 0:
                logger.log("No objects selected")
                props.use_selection = False
        else:
            logger.log("Found {} object".format(len(objects)))

    # Get all scene objects.
    if not props.use_selection:
        logger.log("Exporting scene to BLB")
        objects = context.scene.objects

        object_count = len(objects)

        if object_count != 1:
            logger.log("Found {} objects".format(len(objects)))

            if object_count == 0:
                logger.log("No objects in the scene.")
        else:
            logger.log("Found {} object".format(len(objects)))

    # Search for the bounds object.
    for obj in objects:
        # Manually created bounds object?
        if obj.name.lower().startswith(BOUNDS_NAME_PREFIX):
            if obj.type != "MESH":
                logger.warning("Warning: Object '{}' cannot be used as bounds, must be a mesh".format(obj.name))
                # Continue searching in case a mesh bounds is found.
            else:
                special_objects[BOUNDS_NAME_PREFIX] = obj

                # Get the dimensions of the Blender object, set the values into an array as they may change later, and convert height to plates.
                bounds_size = [obj.dimensions[INDEX_X],
                               obj.dimensions[INDEX_Y],
                               obj.dimensions[INDEX_Z] / PLATE_HEIGHT]

                # Are the dimensions of the bounds object integers?
                if bounds_size[INDEX_X] != int(bounds_size[INDEX_X]) or bounds_size[INDEX_Y] != int(bounds_size[INDEX_Y]) or bounds_size[INDEX_Z] != int(bounds_size[INDEX_Z]):
                    # The bounds object was made manually, allow for some error & floating point inaccuracy.
                    bounds_error = 0.1

                    logger.warning("Warning: Bounds has non-integer size {}, rounding to a precision of {}".format(bounds_size, bounds_error))

                    for index, value in enumerate(bounds_size):
                        # Round to the specified error amount and force to int.
                        bounds_size[index] = int(round(bounds_error * round(value / bounds_error)))

                # Bounds object found and processed, break the loop.
                manual_bounds = True
                break
    else:
        logger.warning("Warning: No 'bounds' object found. Automatically calculated brick size may be undesirable.")
        manual_bounds = False
        # Brick size calculation must be performed after all other objects are processed.

    # TODO: Check that every vertex is within manually defined bounds.

    for obj in objects:
        # Ignore all non-mesh objects and certain special objects.
        if obj.type != "MESH" or obj == special_objects[BOUNDS_NAME_PREFIX]:
            continue

        logger.log("Exporting mesh: {}".format(obj.name))

        # Current object is not the bounds object, record the minimum and maximum vertex coordinates.
        if not special_objects[BOUNDS_NAME_PREFIX]:
            set_min_max(vec_bounding_box_min, vec_bounding_box_max, obj)

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

    # Calculate brick size.
    if not manual_bounds:
        # Get the dimensions defined by the vectors and convert height to plates.
        bounds_size = [vec_bounding_box_max[INDEX_X] - vec_bounding_box_min[INDEX_X],
                       vec_bounding_box_max[INDEX_Y] - vec_bounding_box_min[INDEX_Y],
                       (vec_bounding_box_max[INDEX_Z] - vec_bounding_box_min[INDEX_Z]) / PLATE_HEIGHT]

        # Are the dimensions of the bounds object integers?
        if bounds_size[INDEX_X] != int(bounds_size[INDEX_X]) or bounds_size[INDEX_Y] != int(bounds_size[INDEX_Y]) or bounds_size[INDEX_Z] != int(bounds_size[INDEX_Z]):
            logger.warning("Warning: Bounds has non-integer size {}, rounding up".format(bounds_size))

            # In case height conversion or rounding introduced floating point errors, round up to be on the safe side.
            bounds_size = [ceil(bounds_size[INDEX_X]),
                           ceil(bounds_size[INDEX_Y]),
                           ceil(bounds_size[INDEX_Z])]

        # The number type must be int because you can't have partial plates.
        bounds_size = [int(bounds_size[INDEX_X]),
                       int(bounds_size[INDEX_Y]),
                       int(bounds_size[INDEX_Z])]

    logger.log("Brick size: {}".format(bounds_size))

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
    __write_file(filepath, bounds_size, quads_with_sections)
