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

class Logger(object):
    """Logger class for printing messages to the console and optionally writing the messages to a log file."""
    __log_lines = []

    def __init__(self, write_file, warnings_only=True, logpath=""):
        """Initializes the logger with the specified options and an appropriate log path."""
        self.__write_file = write_file
        self.__warnings_only = warnings_only
        self.__logpath = logpath

    def log(self, message, is_warning=False):
        """Prints the given message to the console and additionally to a log file if so specified at object creation."""
        print(message)

        # Only write to a log if specified.
        if self.__write_file:
            if self.__warnings_only:
                # If only writing a log when a warning is encountered, ensure that current log message is a warning.
                if is_warning:
                    self.__log_lines.append(message)
            else:
                # Alternatively write to a log if writing all messages.
                self.__log_lines.append(message)

    def warning(self, message):
        """Shorthand for log(message, True) to improve clarity."""
        self.log(message, True)

    def error(self, message):
        """Shorthand for log(message, True) to improve clarity."""
        self.log(message, True)

    def write_log(self):
        """Writes a log file only if so specified at object creation."""
        # Write a log file? Anything to write?
        if self.__write_file and len(self.__log_lines) > 0:
            if self.__warnings_only:
                print("Writing log (warnings only) to:", self.__logpath)
            else:
                print("Writing log to:", self.__logpath)

            # Write the log file.
            with open(self.__logpath, "w") as file:
                for line in self.__log_lines:
                    file.write(line)
                    file.write("\n")

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

        print("\n____STARTING BLB EXPORT____")

        props = self.properties
        filepath = bpy.path.ensure_ext(self.filepath, self.filename_ext)
        logpath = bpy.path.ensure_ext(bpy.path.display_name_from_filepath(self.filepath), self.logfile_ext)

        logger = Logger(props.write_log, props.write_log_warnings, logpath)

        export_blb.export(context, props, logger, filepath)

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
