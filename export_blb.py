def write_vec(fd, vec):
    for i, dim in enumerate(vec):
        if i:
            fd.write(" ")
        if dim == 0:
            fd.write("0")
        elif dim == int(dim):
            fd.write(str(int(dim)))
        else:
            fd.write(str(dim))

def calc_quad_section(quad, bounds_min, bounds_max):
    if all(map(lambda q: q[2] == bounds_max[2], quad[0])): return "top"
    if all(map(lambda q: q[2] == bounds_min[2], quad[0])): return "bottom"
    if all(map(lambda q: q[1] == bounds_max[1], quad[0])): return "north"
    if all(map(lambda q: q[1] == bounds_min[1], quad[0])): return "south"
    if all(map(lambda q: q[0] == bounds_max[0], quad[0])): return "east"
    if all(map(lambda q: q[0] == bounds_min[0], quad[0])): return "west"

    return "omni"

def update_min_max(vec_min, vec_max, ob):
    for vert in ob.data.vertices:
        co = ob.matrix_world * vert.co
        vec_min[0] = min(vec_min[0], co[0])
        vec_min[1] = min(vec_min[1], co[1])
        vec_min[2] = min(vec_min[2], co[2])
        vec_max[0] = max(vec_max[0], co[0])
        vec_max[1] = max(vec_max[1], co[1])
        vec_max[2] = max(vec_max[2], co[2])

def save(operator, context, filepath="",
         use_selection=True
         ):
    print("Exporting scene to BLB")

    if use_selection:
        objects = context.selection
    else:
        objects = context.scene.objects

    bounds_min = Vector((0, 0, 0))
    bounds_max = Vector((0, 0, 0))

    for ob in context.scene.objects:
        if ob.name.lower() == "bounds":
            if ob.type == "MESH":
                bounds_ob = ob
                update_min_max(bounds_min, bounds_max, ob)
                break
            else:
                print("Warning: Object '{}' cannot be used as bounds, must be a mesh".format(ob.name))
    else:
        bounds_ob = None
        print("Warning: No 'bounds' object found. Dimensions may be incorrect.")

    quads = []

    n_tris = 0
    n_ngon = 0

    for ob in objects:
        if ob.type != "MESH" or ob == bounds_ob:
            continue

        print("Exporting mesh", ob.name)

        if not bounds_ob:
            update_min_max(bounds_min, bounds_max, ob)

        me = ob.data

        if me.uv_layers:
            if len(me.uv_layers) > 1:
                print("Warning: Mesh '{}' has {} UV layers, using 1st.".format(ob.name, len(me.uv_layers)))

            uv_data = me.uv_layers[0].data
        else:
            uv_data = None

        def index_to_position(i):
            v = ob.matrix_world * me.vertices[me.loops[i].vertex_index].co
            v[2] /= 0.4 # Scale plates
            return v

        def index_to_normal(i):
            return (ob.matrix_world.to_3x3() * me.vertices[me.loops[i].vertex_index].normal).normalized()

        for poly in me.polygons:
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

            if poly.use_smooth:
                normals = tuple(map(index_to_normal, loop_indices))
            else:
                normals = (poly.normal,) * 4

            if uv_data:
                uvs = tuple(map(lambda i: uv_data[i].uv, loop_indices))
            else:
                uvs = (Vector((0.5, 0.5)),) * 4

            colors = None

            if me.materials and me.materials[poly.material_index] is not None:
                tex = me.materials[poly.material_index].name.upper()
            else:
                tex = "SIDE"

            quads.append((positions, normals, uvs, colors, tex))

    # More plate adjustment
    bounds_min[2] /= 0.4
    bounds_max[2] /= 0.4

    # Group quads into sections
    quads_with_sections = tuple(map(lambda q: (q, calc_quad_section(q, bounds_min, bounds_max)), quads))

    # Compute brick dimensions
    size_x =  bounds_max[0] - bounds_min[0]
    size_y =  bounds_max[1] - bounds_min[1]
    size_z =  bounds_max[2] - bounds_min[2]

    if size_x != int(size_x) or size_y != int(size_y) or size_z != int(size_z):
        print("Warning: Brick has non-even size ({} {} {}), rounding up".format(size_x, size_y, size_z))

    size_x = int(ceil(size_x))
    size_y = int(ceil(size_y))
    size_z = int(ceil(size_z))

    print("Brick size: {} {} {}".format(size_x, size_y, size_z))

    with open(filepath, "w") as fd:
        write_vec(fd, (size_x, size_y, size_z))
        fd.write("\nSPECIAL\n\n")

        for y in range(size_y):
            for z in range(size_z):
                is_top = z == 0
                is_bot = z == size_z - 1

                if is_bot and is_top: mode = "b"
                elif is_bot: mode = "d"
                elif is_top: mode = "u"
                else: mode = "X"

                fd.write(mode * size_x)
                fd.write("\n")

            fd.write("\n")

        collision_cubes = (
            ((0, 0, 0), (size_x, size_y, size_z)),
        )

        fd.write(str(len(collision_cubes)))
        fd.write("\n")

        for (center, size) in collision_cubes:
            fd.write("\n")
            write_vec(fd, center)
            fd.write("\n")
            write_vec(fd, size)
            fd.write("\n")

        # TBNESW
        fd.write("COVERAGE:\n")

        for i in range(6):
            fd.write("0 : 999\n")

        for section_name in ("top", "bottom", "north", "east", "south", "west", "omni"):
            section_quads = tuple(map(lambda t: t[0], filter(lambda t: t[1] == section_name, quads_with_sections)))

            fd.write("\n")
            fd.write(str(len(section_quads)))
            fd.write("\n")

            for (positions, normals, uvs, colors, tex) in section_quads:
                fd.write("\nTEX:")
                fd.write(tex)
                fd.write("\n\n") # POSITION:
                for position in positions:
                    write_vec(fd, position)
                    fd.write("\n")
                fd.write("\n") # UV COORDS:
                for uv in uvs:
                    write_vec(fd, uv)
                    fd.write("\n")
                fd.write("\n") # NORMALS:
                for normal in normals:
                    write_vec(fd, normal)
                    fd.write("\n")
                if colors is not None:
                    fd.write("COLORS:\n")
                    for color in colors:
                        write_vec(fd, color)
                        fd.write("\n")

    if n_tris:
        print("Note: {} triangles degenerated to quads.".format(n_tris))

    if n_ngon:
        print("Warning: {} n-gons skipped.".format(n_ngon))

    return {'FINISHED'}