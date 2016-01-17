import bpy
import sys
 
argv = sys.argv
argv = argv[argv.index("--") + 1:] # get all args after "--"

blb_out = argv[0]
log = argv[1].lower() == "true"
log_warnings = argv[2].lower() == "true"
 
bpy.ops.export_scene.blb(filepath=blb_out,write_log=log,write_log_warnings=log_warnings)
