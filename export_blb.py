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
        vec_min[0] = min(vec_min[0], coord[0])
        vec_min[1] = min(vec_min[1], coord[1])
        vec_min[2] = min(vec_min[2], coord[2])
        vec_max[0] = max(vec_max[0], coord[0])
        vec_max[1] = max(vec_max[1], coord[1])
        vec_max[2] = max(vec_max[2], coord[2])

def write(context, props, logger, filepath=""):
    """Write a BLB file."""

    special_objects = {"bounds": None,
                       "collision": None,
                       "grid_u": None,
                       "grid_x": None,
                       "grid_b": None}

    vec_bounds_min = Vector((0, 0, 0))
    vec_bounds_max = Vector((0, 0, 0))

    a_quads = []

    n_tris = 0
    n_ngon = 0

    # TODO: Layer support.

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

    # Search for special objects.
    for obj in objects:
        # Bounds object
        if obj.name.lower() == "bounds":
            if obj.type == "MESH":
                special_objects["bounds"] = obj
                set_min_max(vec_bounds_min, vec_bounds_max, obj)
                break
            else:
                logger.warning("Warning: Object '{}' cannot be used as bounds, must be a mesh".format(obj.name))
    else:
        logger.warning("Warning: No 'bounds' object found. Dimensions may be incorrect.")

    for obj in objects:
        # Ignore all non-mesh objects and certain special objects.
        if obj.type != "MESH" or obj == special_objects["bounds"]:
            continue

        logger.log("Exporting mesh: {}".format(obj.name))

        if not special_objects["bounds"]:
            set_min_max(vec_bounds_min, vec_bounds_max, obj)

        current_data = obj.data

        # UVs
        if current_data.uv_layers:
            if len(current_data.uv_layers) > 1:
                logger.warning("Warning: Mesh '{}' has {} UV layers, using the 1st.".format(obj.name, len(current_data.uv_layers)))

            uv_data = current_data.uv_layers[0].data
        else:
            uv_data = None

        def index_to_position(index):
            vec = obj.matrix_world * current_data.vertices[current_data.loops[index].vertex_index].co
            vec[2] /= 0.4  # Scale plates
            return vec

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
                uvs = tuple(map(lambda i: uv_data[i].uv, loop_indices))
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

    # More plate adjustment
    vec_bounds_min[2] /= 0.4
    vec_bounds_max[2] /= 0.4

    # Group a_quads into sections
    quads_with_sections = tuple(map(lambda q: (q, calc_quad_section(q, vec_bounds_min, vec_bounds_max)), a_quads))

    # Compute brick dimensions
    size_x = vec_bounds_max[0] - vec_bounds_min[0]
    size_y = vec_bounds_max[1] - vec_bounds_min[1]
    size_z = vec_bounds_max[2] - vec_bounds_min[2]

    if size_x != int(size_x) or size_y != int(size_y) or size_z != int(size_z):
        logger.warning("Warning: Brick has non-even size ({} {} {}), rounding up".format(size_x, size_y, size_z))

    size_x = int(ceil(size_x))
    size_y = int(ceil(size_y))
    size_z = int(ceil(size_z))

    logger.log("Brick size: {} {} {}".format(size_x, size_y, size_z))

    # Write the BLB file.
    with open(filepath, "w") as file:
        # Write brick size.
        write_vector(file, (size_x, size_y, size_z))

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
        collision_cubes = (
            ((0, 0, 0), (size_x, size_y, size_z)),
        )

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
            section_quads = tuple(map(lambda t: t[0], filter(lambda t: t[1] == section_name, quads_with_sections)))

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

    if n_tris:
        logger.warning("Warning: {} triangles degenerated to a_quads.".format(n_tris))

    if n_ngon:
        logger.warning("Warning: {} n-gons skipped.".format(n_ngon))
