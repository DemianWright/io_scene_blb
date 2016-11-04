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
A module for exporting Blender data into the BLB format.

@author: Demian Wright
'''
from decimal import Decimal
import bpy

from . import const, logger, blb_processor, blb_writer, common


# The export mediator module.

# ==========================
# DerivativeProperties Class
# ==========================

class DerivativeProperties(object):
    """A class for storing various properties derived from the user-defined Blender properties to guide the export process.

    Stores the following data:
        blendprop (Blender properties object): The original Blender properties object containing more properties that have not been processed further.
        plate_height (Decimal): The height of one Blockland plate in Blender units.
        human_error (Decimal): Error allowed for manually created definition objects, because they must lie exactly on the brick grid.
        scale (Decimal): The scale to export the brick at. Value is in range [0.0,1.0].
        grid_def_obj_token_priority (sequence): A sequence containing the user-defined brick grid definitions in reverse priority order.
        grid_definitions_priority (sequence): A sequence containing the brick grid symbols in the same order as grid_def_obj_token_priority.
        quad_sort_definitions (sequence): A sequence containing the user-defined definitions for quad sorting.
    """

    def __init__(self, properties):
        """Creates the DerivativeProperties object from the specified Blender properties.

        Args:
            properties (Blender properties object): A Blender object containing user preferences.
        """
        #===========
        # Properties
        # ==========
        self.blendprop = properties
        self.error_message = None

        # Build the brick grid definition tokens and symbol priority tuple.
        # Contains the brick grid definition object name tokens in reverse priority order.
        result = self.__build_grid_priority_tuples(properties)

        if result is None:
            self.error_message = 'Two or more brick grid definitions had the same priority.'
        else:
            #===========
            # Brick Grid
            # ==========
            self.grid_def_obj_token_priority = result[0]
            self.grid_definitions_priority = result[1]

            #=============
            # Quad Sorting
            # ============
            self.quad_sort_definitions = self.__build_quad_sort_definitions(properties)

            #======
            # Scale
            # =====
            # export_scale is a percentage value.
            self.scale = Decimal("{0:.{1}f}".format(properties.export_scale, const.MAX_FP_DECIMALS_TO_WRITE)) * Decimal("0.01")
            logger.info("Export at {} scale.".format(self.scale))

            #===========================
            # Plate Height & Human Error
            # ==========================
            if properties.export_scale == 100.0:
                # A 1x1 Blockland plate is equal to 1.0 x 1.0 x 0.4 Blender units (X,Y,Z)
                self.plate_height = Decimal("0.4")

                # Used for rounding vertex positions to the brick grid.
                self.human_error = Decimal("0.1")
            else:
                properties.human_error = properties.human_error * self.scale
                properties.plate_height = properties.plate_heigh * self.scale

            #==========
            # Precision
            # =========
            prec = properties.float_precision

            if common.to_float_or_none(prec) is None:
                self.error_message = 'Invalid floating point precision value given.'
            else:
                if prec == '0':
                    logger.info('Setting floating point precision to minimum.')
                    # We're only writing 16 decimals anyway.
                    prec = "0.{}1".format('0' * (const.MAX_FP_DECIMALS_TO_WRITE - 1))

                logger.info("Using floating point precision: {}".format(prec))

                self.precision = prec

    @classmethod
    def __build_grid_priority_tuples(cls, properties):
        """Sorts the grid definition object name tokens into reverse priority order according the user properties.
        Definitions earlier in the sequence are overwritten by tokens later in the sequence.

        Args:
            properties (Blender properties object): A Blender object containing user preferences.

        Returns:
            A tuple containing the grid definition object tokens in the first element and the grid symbols in the same order in the second element or None if one or more definition had the same priority which leads to undefined behavior and is disallowed.
        """
        # There are exactly 5 tokens.
        tokens = [None] * 5

        # Go through every priority individually.
        tokens[properties.deftoken_gridx_priority] = properties.deftoken_gridx
        tokens[properties.deftoken_griddash_priority] = properties.deftoken_griddash
        tokens[properties.deftoken_gridu_priority] = properties.deftoken_gridu
        tokens[properties.deftoken_gridd_priority] = properties.deftoken_gridd
        tokens[properties.deftoken_gridb_priority] = properties.deftoken_gridb

        if None in tokens:
            logger.error("Two or more brick grid definitions had the same priority. Unable to proceed.")
            return None
        else:
            symbols = [None] * 5

            symbols[properties.deftoken_gridx_priority] = const.GRID_INSIDE
            symbols[properties.deftoken_griddash_priority] = const.GRID_OUTSIDE
            symbols[properties.deftoken_gridu_priority] = const.GRID_UP
            symbols[properties.deftoken_gridd_priority] = const.GRID_DOWN
            symbols[properties.deftoken_gridb_priority] = const.GRID_BOTH

            return (tuple(tokens), tuple(symbols))

    @classmethod
    def __build_quad_sort_definitions(cls, properties):
        """Creates tuple of quad section definitions used to sort quads.

        Args:
            properties (Blender properties object): A Blender object containing user preferences.

        Returns:
            A tuple containing the definitions for manual quad section sorting in the correct order.
        """
        # The definitions must be in the same order as const.QUAD_SECTION_ORDER
        return (properties.deftoken_quad_sort_top,
                properties.deftoken_quad_sort_bottom,
                properties.deftoken_quad_sort_north,
                properties.deftoken_quad_sort_east,
                properties.deftoken_quad_sort_south,
                properties.deftoken_quad_sort_west,
                properties.deftoken_quad_sort_omni)


def export(context, properties, export_dir, export_file, file_name):
    """Processes the data from the scene and writes it to a BLB file.

    Args:
        context (Blender context object): A Blender object containing scene data.
        properties (Blender properties object): A Blender object containing user preferences.
        export_dir (string): The absolute path to the directory where to write the BLB file.
        export_file (string): The name of the file to be written with the extension or None if brick name is to be retrieved from the bounds definition object.
        file_name (string):  The name of the .blend file with the BLB extension to be used as a fall back option.

    Returns:
        None if everything went OK or a string containing an error message to display to the user if the file was not written
    """
    # TODO: Exporting multiple bricks from a single file.

    logger.configure(properties.write_log, properties.write_log_warnings)

    # Process the user properties further.
    deriv_properties = DerivativeProperties(properties)

    if deriv_properties.error_message is not None:
        return deriv_properties.error_message
    else:
        # Process Blender data into a writable format.
        # The context variable contains all the Blender data.
        # The properties variable contains all user-defined settings to take into account when processing the data.
        data = blb_processor.process_blender_data(context, deriv_properties)

        # Got the BLBData we need.
        if isinstance(data, blb_processor.BLBData):
            # Name was sourced from the bounds object.
            if export_file is None:
                # No name was actually found?
                if data.brick_name is None:
                    # Fall back to file name.
                    export_file = file_name
                else:
                    # Use the found name.
                    export_file = "{}{}".format(data.brick_name, const.BLB_EXT)

            export_path = "{}{}".format(export_dir, export_file)

            logger.info('Writing to file.')
            # Write the data to a file.
            blb_writer.write_file(deriv_properties, export_path, data)

            logger.info("Output file: {}".format(export_path), 1)

            # Remove the .BLB extension and change it to the log extension.
            logname = bpy.path.ensure_ext(export_file[:-4], const.LOG_EXT)

            # Build the full path and write the log.
            logger.write_log("{}{}".format(export_dir, logname))

            return None
        else:
            # Something went wrong, pass on the message.
            return data
