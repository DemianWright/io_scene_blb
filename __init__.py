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
    "name": "Export: Blockland Brick (.blb)",
    "author": "Demian Wright & Nick Smith",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "File > Export > Blockland Brick (.blb)",
    "description": "Export Blockland brick format",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export"}

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty, IntProperty, FloatProperty
from bpy_extras.io_utils import ExportHelper

# TODO: Rewrite all docstrings to follow the Google style guide or something.


class ExportBLB(bpy.types.Operator, ExportHelper):
    """Export Blockland brick data."""
    from . import const

    bl_idname = "export_scene.blb"
    bl_label = "Export BLB"

    filename_ext = const.BLB_EXT
    logfile_ext = const.LOG_EXT
    filter_glob = StringProperty(default="*" + const.BLB_EXT, options={'HIDDEN'})

    # ==========
    # Properties
    # ==========

    # ==========
    # Processing
    # ==========

    # ----------
    # Brick Name
    # ----------

    brick_name_source = EnumProperty(
        items=[("FILE", "File", "Brick name is the same as this .blend file name"),
               ("BOUNDS", "Bounds", "Brick name is in the name of the bounds object, after the bounds definition, separated with a space")],
        name="Brick Name From:",
        description="Where to get the name of the exported brick by default (can be changed manually in the file dialog)",
        default="FILE"
    )

    # -------
    # Objects
    # -------

    export_objects = EnumProperty(
        items=[("SELECTION", "Selection", "Export only selected objects"),
               ("LAYERS", "Layers", "Export all objects in the visible layers"),
               ("SCENE", "Scene", "Export all objects in the active scene")],
        name="Export Objects In:",
        description="Only export the specified objects",
        default="SELECTION"
    )

    # --------
    # Rotation
    # --------

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

    # -----
    # Scale
    # -----

    export_scale = FloatProperty(
        name="Scale",
        description="The scale to export the brick at",
        subtype='PERCENTAGE',
        precision=3,
        step=1.0,
        default=100.0,
        min=0.001,
        soft_max=400.0,
    )

    # --------
    # Coverage
    # --------

    calculate_coverage = BoolProperty(
        name="Coverage",
        description="Calculate brick coverage. Coverage relies on the quad section data to be of any use. The coverage system intelligently hides (non-omni) quads on the side of the brick when it is covered by other bricks.",
        default=False,
    )

    coverage_top_calculate = BoolProperty(
        name="Hide Own Top Faces",
        description="Hide the top faces of this brick when the entire top side of this brick is covered",
        default=False,
    )

    coverage_top_hide = BoolProperty(
        name="Hide Adjacent Top Faces",
        description="Hide the bottom faces of the adjacent brick(s) covering the top side of this brick",
        default=False,
    )

    coverage_bottom_calculate = BoolProperty(
        name="Hide Own Bottom Faces",
        description="Hide the bottom faces of this brick when the entire bottom side of this brick is covered",
        default=False,
    )

    coverage_bottom_hide = BoolProperty(
        name="Hide Adjacent Bottom Faces",
        description="Hide the top faces of the adjacent brick(s) covering the bottom side of this brick",
        default=False,
    )

    coverage_north_calculate = BoolProperty(
        name="Hide Own North Faces",
        description="Hide the north faces of this brick when the entire north side of this brick is covered",
        default=False,
    )

    coverage_north_hide = BoolProperty(
        name="Hide Adjacent North Faces",
        description="Hide the adjacent side faces of the adjacent brick(s) covering the north side of this brick",
        default=False,
    )

    coverage_east_calculate = BoolProperty(
        name="Hide Own East Faces",
        description="Hide the east faces of this brick when the entire east side of this brick is covered",
        default=False,
    )

    coverage_east_hide = BoolProperty(
        name="Hide Adjacent East Faces",
        description="Hide the adjacent side faces of the adjacent brick(s) covering the east side of this brick",
        default=False,
    )

    coverage_south_calculate = BoolProperty(
        name="Hide Own South Faces",
        description="Hide the south faces of this brick when the entire south side of this brick is covered",
        default=False,
    )

    coverage_south_hide = BoolProperty(
        name="Hide Adjacent South Faces",
        description="Hide the adjacent side faces of the adjacent brick(s) covering the south side of this brick",
        default=False,
    )

    coverage_west_calculate = BoolProperty(
        name="Hide Own West Faces",
        description="Hide the west faces of this brick when the entire west side of this brick is covered",
        default=False,
    )

    coverage_west_hide = BoolProperty(
        name="Hide Adjacent West Faces",
        description="Hide the adjacent side faces of the adjacent brick(s) covering the west side of this brick",
        default=False,
    )

    # -------
    # Sorting
    # -------

    auto_sort_quads = BoolProperty(
        name="Automatic Quad Sorting",
        description="Automatically sorts the quads of the meshes into the 7 sections. Coverage must be enabled for this to be of any use.",
        default=False,
    )

    # -----------
    # Definitions
    # -----------

    custom_definitions = BoolProperty(
        name="Custom Definition Object Prefixes",
        description="Change the object name prefixes for definition objects (prefixes are case insensitive)",
        default=False,
    )

    defprefix_bounds = StringProperty(
        name="Brick Bounds",
        description="Prefix for objects that define brick bounds",
        default="bounds",
    )

    defprefix_collision = StringProperty(
        name="Collision Cuboid",
        description="Prefix for objects that define collision cuboids",
        default="collision",
    )

    defprefix_color = StringProperty(
        name="Object Color",
        description="Prefix for specifying a color for an object. Prefix must be followed by 4 values (red green blue alpha) separated with spaces using a comma (,) as decimal separator. Vertex colors are overridden by colors defined in object names.",
        default="c",
    )

    # Sections

    defprefix_quad_sort_top = StringProperty(
        name="Section, Top",
        description="Prefix for specifying that the object's vertices belong to the top section of the brick (used in brick coverage for hiding faces to improve performance)",
        default="st",
    )

    defprefix_quad_sort_bottom = StringProperty(
        name="Section, Bottom",
        description="Prefix for specifying that the object's vertices belong to the bottom section of the brick (used in brick coverage for hiding faces to improve performance)",
        default="sb",
    )

    defprefix_quad_sort_north = StringProperty(
        name="Section, North",
        description="Prefix for specifying that the object's vertices belong to the north section of the brick (used in brick coverage for hiding faces to improve performance)",
        default="sn",
    )

    defprefix_quad_sort_east = StringProperty(
        name="Section, East",
        description="Prefix for specifying that the object's vertices belong to the east section of the brick (used in brick coverage for hiding faces to improve performance)",
        default="se",
    )

    defprefix_quad_sort_south = StringProperty(
        name="Section, South",
        description="Prefix for specifying that the object's vertices belong to the south section of the brick (used in brick coverage for hiding faces to improve performance)",
        default="ss",
    )

    defprefix_quad_sort_west = StringProperty(
        name="Section, West",
        description="Prefix for specifying that the object's vertices belong to the west section of the brick (used in brick coverage for hiding faces to improve performance)",
        default="sw",
    )

    defprefix_quad_sort_omni = StringProperty(
        name="Section, Omni",
        description="Prefix for specifying that the object's vertices belong to the omni section of the brick, these vertices will never be hidden",
        default="so",
    )

    # Brick Grid

    defprefix_gridx = StringProperty(
        name="Brick Grid x",
        description="Prefix for objects that define a volume within the brick bounds that will be filled with the 'x' symbol in the brick grid signifying that other bricks cannot be placed there",
        default="gridx",
    )

    defprefix_griddash = StringProperty(
        name="Brick Grid -",
        description="Prefix for objects that define a volume within the brick bounds that will be filled with the '-' symbol in the brick grid signifying empty space",
        default="grid-",
    )

    defprefix_gridu = StringProperty(
        name="Brick Grid u",
        description="Prefix for objects that define a volume within the brick bounds that will be filled with the 'u' symbol in the brick grid signifying that other bricks may be planted above",
        default="gridu",
    )

    defprefix_gridd = StringProperty(
        name="Brick Grid d",
        description="Prefix for objects that define a volume within the brick bounds that will be filled with the 'd' symbol in the brick grid signifying that other bricks may be planted below",
        default="gridd",
    )

    defprefix_gridb = StringProperty(
        name="Brick Grid b",
        description="Prefix for objects that define a volume within the brick bounds that will be filled with the 'b' symbol in the brick grid signifying that other bricks may be planted above or below",
        default="gridb",
    )

    defprefix_gridx_priority = IntProperty(
        name="Grid X Symbol Priority",
        description="Priority of the 'x' symbol definition, higher priority definition override any overlapping definitions with lower priority (two or more symbols must not have the same priority)",
        default=0,
        min=0,
        max=4,
    )

    defprefix_griddash_priority = IntProperty(
        name="Grid - Symbol Priority",
        description="Priority of the '-' symbol definition, higher priority definition override any overlapping definitions with lower priority (two or more symbols must not have the same priority)",
        default=1,
        min=0,
        max=4,
    )

    defprefix_gridu_priority = IntProperty(
        name="Grid U Symbol Priority",
        description="Priority of the 'u' symbol definition, higher priority definition override any overlapping definitions with lower priority (two or more symbols must not have the same priority)",
        default=2,
        min=0,
        max=4,
    )

    defprefix_gridd_priority = IntProperty(
        name="Grid D Symbol Priority",
        description="Priority of the 'd' symbol definition, higher priority definition override any overlapping definitions with lower priority (two or more symbols must not have the same priority)",
        default=3,
        min=0,
        max=4,
    )

    defprefix_gridb_priority = IntProperty(
        name="Grid B Symbol Priority",
        description="Priority of the 'b' symbol definition, higher priority definition override any overlapping definitions with lower priority (two or more symbols must not have the same priority)",
        default=4,
        min=0,
        max=4,
    )

    # =======
    # Writing
    # =======

    # ----------
    # Terse Mode
    # ----------
    terse_mode = BoolProperty(
        name="Terse Mode",
        description="Exclude optional text from the BLB file making it slightly smaller and harder to read (not recommended, size difference is negligible)",
        default=False,
    )

    # ---
    # Log
    # ---

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
        from . import export_blb

        print("\n____STARTING BLB EXPORT____")

        props = self.properties

        # Get the current filepath which may or may not be the absolute path to the currently open .blend file.
        # Get only the name of the file from the filepath.
        # Add in the BLB extension.
        file_name = bpy.path.ensure_ext(bpy.path.display_name_from_filepath(self.filepath), self.filename_ext)

        # The absolute path to the directory where the currently open file is in.
        export_dir = bpy.path.abspath("//")

        # The name of the BLB file to export.
        if props.brick_name_source == 'FILE':
            export_file = file_name
        else:
            export_file = None

        message = export_blb.export(context, props, export_dir, export_file, file_name)

        if isinstance(message, str):
            self.report({'ERROR'}, message)
        # Else: No error message, everything is OK.

        return {'FINISHED'}

    # ==============
    # User Interface
    # ==============

    def draw(self, context):
        """Draws the UI in the export menu."""
        layout = self.layout

        # ==========
        # Processing
        # ==========

        # Property: Brick Name
        row = layout.row()
        split = row.split(percentage=0.49)
        row = split.row()
        row.label("Brick Name From:")

        split = split.split()
        row = split.row()
        row.prop(self, "brick_name_source", expand=True)

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

        # Property: Export Scale
        layout.prop(self, "export_scale")

        # Properties: Coverage
        layout.prop(self, "calculate_coverage")

        if self.calculate_coverage:
            box = layout.box()
            box.label("Coverage Options", icon="GROUP")
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

        # Properties: Quad Sorting
        layout.prop(self, "auto_sort_quads")

        # Properties: Custom Definition Prefixes
        layout.prop(self, "custom_definitions")

        if self.custom_definitions:
            box = layout.box()
            box.label("Definition Object Prefixes", icon="EDIT_VEC")
            box.active = self.custom_definitions

            def draw_definition_property(label_text, prop_name):
                """A helper function for drawing the definition properties."""
                row = box.row()

                split = row.split(percentage=0.6)
                col = split.column()
                col.label("{}:".format(label_text))

                split = split.split()
                col = split.column()
                col.prop(self, prop_name, "")

            def draw_grid_definition_property(symbol, prop_name):
                """A helper function for drawing the definition properties."""
                row = box.row()

                split = row.split(percentage=0.35)
                col = split.column()
                col.label("{}".format(symbol))

                split = split.split(percentage=0.6)
                col = split.column()
                col.prop(self, prop_name, "")

                split = split.split()
                col = split.column()
                col.prop(self, "{}_priority".format(prop_name), "")

            # This has duplicate data but I don't know how to access the property names defined earlier since self.defprefix_bounds.name doesn't seem to work.
            # For some reason self.defprefix_bounds = "defprefix_bounds" instead of an instance of StringProperty.
            draw_definition_property("Brick Bounds", "defprefix_bounds")
            draw_definition_property("Collision Cuboids", "defprefix_collision")
            draw_definition_property("Object Colors", "defprefix_color")

            # Sorting definitions.

            draw_definition_property("Section, Top", "defprefix_quad_sort_top")
            draw_definition_property("Section, Bottom", "defprefix_quad_sort_bottom")
            draw_definition_property("Section, North", "defprefix_quad_sort_north")
            draw_definition_property("Section, East", "defprefix_quad_sort_east")
            draw_definition_property("Section, South", "defprefix_quad_sort_south")
            draw_definition_property("Section, West", "defprefix_quad_sort_west")
            draw_definition_property("Section, Omni", "defprefix_quad_sort_omni")

            # Grid definitions.

            row = box.row()
            split = row.split(percentage=0.35)
            col = split.column()
            col.label("Brick Grid")
            col.label("Symbol")

            split = split.split(percentage=0.6)
            col = split.column()
            col.label()
            col.label("Prefix")

            split = split.split()
            col = split.column()
            col.label()
            col.label("Priority")

            draw_grid_definition_property("b", "defprefix_gridb")
            draw_grid_definition_property("d", "defprefix_gridd")
            draw_grid_definition_property("u", "defprefix_gridu")
            draw_grid_definition_property("-", "defprefix_griddash")
            draw_grid_definition_property("x", "defprefix_gridx")

        # =======
        # Writing
        # =======

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
