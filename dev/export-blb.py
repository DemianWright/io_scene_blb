import bpy
import sys
 
argv = sys.argv
argv = argv[argv.index("--") + 1:] # get all args after "--"

blb_out = argv[0]
selection = argv[1].lower() == "true"
log = argv[2].lower() == "true"
log_warnings = argv[3].lower() == "true"
forward = argv[4].upper()
coverage = argv[5].lower() == "true"
 
bpy.ops.export_scene.blb(filepath=blb_out,
                         use_selection=selection,
                         write_log=log,
                         write_log_warnings=log_warnings,
                         axis_blb_forward=forward,
                         calculate_coverage=coverage,
                         coverage_top_calculate=coverage,
                         coverage_top_hide=coverage,
                         coverage_bottom_calculate=coverage,
                         coverage_bottom_hide=coverage,
                         coverage_north_calculate=coverage,
                         coverage_north_hide=coverage,
                         coverage_east_calculate=coverage,
                         coverage_east_hide=coverage,
                         coverage_south_calculate=coverage,
                         coverage_south_hide=coverage,
                         coverage_west_calculate=coverage,
                         coverage_west_hide=coverage)
