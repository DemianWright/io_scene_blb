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
'''
Handles registering the add-on into Blender and drawing properties to the UI.

@author: Demian Wright
'''

bl_info = {
    "name": "Blockland Brick Format",
    "author": "Demian Wright & Nick Smith (Port)",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "File > Export > Blockland Brick (.blb)",
    "description": "Export Blockland Brick (.blb)",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export"}

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

# TODO: Rewrite all docstrings to follow the Google style guide or something.


class ExportBLB(bpy.types.Operator, ExportHelper):
    """Export Blockland brick data."""

    bl_idname = "export_scene.blb"
    bl_label = "Export BLB"

    filename_ext = ".blb"
    logfile_ext = ".log"
    filter_glob = StringProperty(default="*.blb", options={'HIDDEN'})

    # ==========
    # Properties
    # ==========

    # TODO: Scale.

    export_objects = EnumProperty(
        items=[("SELECTION", "Selection", "Export only selected objects"),
               ("LAYERS", "Layers", "Export all objects in the visible layers"),
               ("SCENE", "Scene", "Export all objects in the active scene")],
        name="Export Objects In:",
        description="Only export the specified objects",
        default="SELECTION"
    )

    # For whatever reason BLB coordinates are rotated 90 degrees counter-clockwise to Blender coordinates.
    # I.e. -X is facing you when the brick is planted and +X is the brick north instead of +Y which makes more sense to me.
    # TODO: Support Z axis remapping.
    axis_blb_forward = EnumProperty(
        items=[("POSITIVE_X", "+X", "The positive X axis"),
               ("POSITIVE_Y", "+Y", "The positive Y axis"),
               ("NEGATIVE_X", "-X", "The negative X axis"),
               ("NEGATIVE_Y", "-Y", "The negative Y axis")],
        name="Brick Forward Axis",
        description="Set the Blender axis that will point forwards in the game",
        default="POSITIVE_Y"
    )

    calculate_coverage = BoolProperty(
        name="Coverage",
        description="Calculate brick coverage",
        default=False,
    )

    coverage_top_calculate = BoolProperty(
        name="Hide Own Top Faces",
        description="Hide the top faces of this brick when the entire top side of this brick is covered",
        default=False,
    )

    coverage_top_hide = BoolProperty(
        name="Hide Adjacent Top Faces",
        description="Hide the faces of the adjacent bricks covering the top side of this brick",
        default=False,
    )

    coverage_bottom_calculate = BoolProperty(
        name="Hide Own Bottom Faces",
        description="Hide the bottom faces of this brick when the entire bottom side of this brick is covered",
        default=False,
    )

    coverage_bottom_hide = BoolProperty(
        name="Hide Adjacent Bottom Faces",
        description="Hide the faces of the adjacent bricks covering the bottom side of this brick",
        default=False,
    )

    coverage_north_calculate = BoolProperty(
        name="Hide Own North Faces",
        description="Hide the north faces of this brick when the entire north side of this brick is covered",
        default=False,
    )

    coverage_north_hide = BoolProperty(
        name="Hide Adjacent North Faces",
        description="Hide the faces of the adjacent bricks covering the north side of this brick",
        default=False,
    )

    coverage_east_calculate = BoolProperty(
        name="Hide Own East Faces",
        description="Hide the east faces of this brick when the entire east side of this brick is covered",
        default=False,
    )

    coverage_east_hide = BoolProperty(
        name="Hide Adjacent East Faces",
        description="Hide the faces of the adjacent bricks covering the east side of this brick",
        default=False,
    )

    coverage_south_calculate = BoolProperty(
        name="Hide Own South Faces",
        description="Hide the south faces of this brick when the entire south side of this brick is covered",
        default=False,
    )

    coverage_south_hide = BoolProperty(
        name="Hide Adjacent South Faces",
        description="Hide the faces of the adjacent bricks covering the south side of this brick",
        default=False,
    )

    coverage_west_calculate = BoolProperty(
        name="Hide Own West Faces",
        description="Hide the west faces of this brick when the entire west side of this brick is covered",
        default=False,
    )

    coverage_west_hide = BoolProperty(
        name="Hide Adjacent West Faces",
        description="Hide the faces of the adjacent bricks covering the west side of this brick",
        default=False,
    )

    terse_mode = BoolProperty(
        name="Terse Mode",
        description="Exclude optional text from the BLB file making it slightly smaller but harder to read",
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

    # ===============
    # Export Function
    # ===============

    def execute(self, context):
        """Export the scene."""

        # Blender requires that I import from "." so it can find the modules.
        from . import export_blb, logger

        print("\n____STARTING BLB EXPORT____")

        props = self.properties
        filepath = bpy.path.ensure_ext(self.filepath, self.filename_ext)

        # Remove the .BLB extension and change it to the log extension.
        logpath = bpy.path.ensure_ext(filepath[:-4], self.logfile_ext)

        logger.configure(props.write_log, props.write_log_warnings)

        if export_blb.export(context, props, filepath):
            # I'm not entirely sure what the bpy.path.abspath("//") does but it works like I want it to.
            logger.info("Output file: {}{}".format(bpy.path.abspath("//"), filepath))

        logger.write_log(logpath)

        return {'FINISHED'}

    # ==============
    # User Interface
    # ==============

    def draw(self, context):
        """Draws the UI in the export menu."""
        layout = self.layout

        # Property: Export Objects
        row = layout.row()
        split = row.split(percentage=0.21)
        row = split.row()
        row.label("Export:")

        split = split.split()
        row = split.row()
        row.prop(self, "export_objects", expand=True)

        # Property: BLB Forward Axis
        row = layout.row()
        split = row.split(percentage=0.4)
        row = split.row()
        row.label("Forward Axis:")

        split = split.split()
        row = split.row()
        row.prop(self, "axis_blb_forward", expand=True)

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
                col.prop(self, "coverage_{}_calculate".format(prop_name), "")

                split = split.split()
                col = split.column()
                col.active = prop_toggler
                col.prop(self, "coverage_{}_hide".format(prop_name), "")

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

        # Property: Terse Mode
        layout = self.layout
        layout.prop(self, "terse_mode")

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


# =============
# Blender Stuff
# =============

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
