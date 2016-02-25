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
        self.write_file = write_file
        self.__warnings_only = warnings_only
        self.__logpath = logpath

    def log(self, message, is_warning=False):
        """Prints the given message to the console and additionally to a log file if so specified at object creation."""
        print(message)

        # Only write to a log if specified.
        if self.write_file:
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
        if self.write_file and len(self.__log_lines) > 0:
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

    # TODO: Scale.
    # TODO: Define North.

    # TODO: Change this to enum: Selection, Layer, Scene
    use_selection = BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=True,
        )

    calculate_coverage = BoolProperty(
        name="Coverage",
        description="Calculate brick coverage",
        default=False,
        )

    coverage_top_calculate = BoolProperty(
        name="",
        description="Hide the top faces of this brick when the entire top side of this brick is covered",
        default=False,
        )

    coverage_top_hide = BoolProperty(
        name="",
        description="Hide the faces of the adjacent bricks covering the top side of this brick",
        default=False,
        )

    coverage_bottom_calculate = BoolProperty(
        name="",
        description="Hide the bottom faces of this brick when the entire bottom side of this brick is covered",
        default=False,
        )

    coverage_bottom_hide = BoolProperty(
        name="",
        description="Hide the faces of the adjacent bricks covering the bottom side of this brick",
        default=False,
        )

    coverage_north_calculate = BoolProperty(
        name="",
        description="Hide the north faces of this brick when the entire north side of this brick is covered",
        default=False,
        )

    coverage_north_hide = BoolProperty(
        name="",
        description="Hide the faces of the adjacent bricks covering the north side of this brick",
        default=False,
        )

    coverage_east_calculate = BoolProperty(
        name="",
        description="Hide the east faces of this brick when the entire east side of this brick is covered",
        default=False,
        )

    coverage_east_hide = BoolProperty(
        name="",
        description="Hide the faces of the adjacent bricks covering the east side of this brick",
        default=False,
        )

    coverage_south_calculate = BoolProperty(
        name="",
        description="Hide the south faces of this brick when the entire south side of this brick is covered",
        default=False,
        )

    coverage_south_hide = BoolProperty(
        name="",
        description="Hide the faces of the adjacent bricks covering the south side of this brick",
        default=False,
        )

    coverage_west_calculate = BoolProperty(
        name="",
        description="Hide the west faces of this brick when the entire west side of this brick is covered",
        default=False,
        )

    coverage_west_hide = BoolProperty(
        name="",
        description="Hide the faces of the adjacent bricks covering the west side of this brick",
        default=False,
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
        """Draws the UI in the export menu."""

        # Property: Use Selection
        layout = self.layout
        layout.prop(self, "use_selection")

        # Properties: Coverage
        layout.prop(self, "calculate_coverage")

        if self.calculate_coverage:
            box = layout.box()
            box.active = self.calculate_coverage

            def draw_coverage_property(label_text, prop_name, prop_toggler):
                """A helper function for drawing the coverage properties."""

                row = box.row()

                split = row.split(percentage=0.3)
                col = split.column()
                col.label(label_text)

                split = split.split(percentage=0.3)
                col = split.column()
                col.prop(self, "coverage_{}_calculate".format(prop_name))

                split = split.split()
                col = split.column()
                col.active = prop_toggler
                col.prop(self, "coverage_{}_hide".format(prop_name))

            row = box.row()
            split = row.split(percentage=0.3)
            col = split.column()
            col.label("")
            col.label("Side")

            split = split.split(percentage=0.3)
            col = split.column()
            col.label("Hide")
            col.label("Self")

            split = split.split()
            col = split.column()
            col.label("Hide")
            col.label("Adjacent")

            draw_coverage_property("Top", "top", self.coverage_top_calculate)
            draw_coverage_property("Bottom", "bottom", self.coverage_bottom_calculate)
            draw_coverage_property("North", "north", self.coverage_north_calculate)
            draw_coverage_property("East", "east", self.coverage_east_calculate)
            draw_coverage_property("South", "south", self.coverage_east_calculate)
            draw_coverage_property("West", "west", self.coverage_west_calculate)

        # Property: Write Log
        row = layout.row()
        split = row.split(percentage=0.4)
        col = split.column()
        col.prop(self, "write_log")

        # Property: Write Log on Warnings
        # Only show when Write Log is checked.
        if self.write_log:
            split = split.split()
            # The "Only on Warnings" option is grayed out when "Write Log" is not enabled.
            split.active = self.write_log
            col = split.column()
            col.prop(self, "write_log_warnings")

def menu_export(self, context):
    """Adds the export option into the export menu."""
    self.layout.operator(ExportBLB.bl_idname, text="Blockland Brick (.blb)")

def register():
    """Registers this module into Blender."""
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_export)

def unregister():
    """Unregisters this module from Blender."""
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
