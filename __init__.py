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

bl_info = {
    "name": "Blockland Brick Format",
    "author": "Nick Smith (Port) & Demian Wright",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "File > Export > Blockland Brick (.blb)",
    "description": "Export Blockland Brick (.blb)",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export"}

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper

### EXPORT ###
class ExportBLB(bpy.types.Operator, ExportHelper):
    """Export Blockland brick data."""

    bl_idname = "export_scene.blb"
    bl_label = "Export BLB"

    filename_ext = ".blb"
    logfile_ext = ".log"
    filter_glob = StringProperty(default="*.blb", options={'HIDDEN'})

    use_selection = BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=True,
        )

    write_log = BoolProperty(
        name="Write Log",
        description="Write a log file after exporting",
        default=True,
        )

    write_log_warnings = BoolProperty(
        name="Only on Warnings",
        description="Only write a log file if warnings were generated",
        default=True,
        )

    def execute(self, context):
        """Export the scene."""

        from . import export_blb
        from . import logger

        print("\n____STARTING BLB EXPORT____")
        props = self.properties
        filepath = self.filepath
        filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
        logpath = bpy.path.ensure_ext(bpy.path.display_name_from_filepath(self.filepath), self.logfile_ext)

        logger = logger.Logger(props.write_log, props.write_log_warnings, logpath)

        export_blb.write(context, props, logger, filepath)

        logger.log("{}{}{}".format("Output file: ", bpy.path.abspath("//"), filepath))

        logger.write_log()

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "use_selection")

        layout.prop(self, "write_log")

        # There might be a better way of doing this but I don't know how to.
        row = layout.row()
        row.active = self.write_log
        row.prop(self, "write_log_warnings")

### REGISTER ###
def menu_export(self, context):
    """Add the export option into the export menu."""
    self.layout.operator(ExportBLB.bl_idname, text="Blockland Brick (.blb)")

def register():
    """Register this module into Blender."""
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_export)

def unregister():
    """Unregister this module from Blender."""
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
