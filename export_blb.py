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


def export(context, properties, filepath=""):
    """
    Processes the data from the scene and writes it to a BLB file.
    Returns True if the BLB file was written.
    """

    from . import blb_processor, blb_writer

    # TODO: Layer support.
    # TODO: Exporting multiple bricks from a single file.
    # TODO: Move this function into init?

    # Process the data.
    # The context variable contains all the Blender data.
    # The properties variable contains all user-defined settings to take into account when processing the data.
    processor = blb_processor.BLBProcessor(context, properties)
    blb_data = processor.process()

    if blb_data is not None:
        # Write the data to a file.
        writer = blb_writer.BLBWriter(filepath, properties.axis_blb_forward, blb_data)

        # TODO: Actually return true only if the file was written.
        writer.write_file()
        return True

    return False
