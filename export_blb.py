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

# The export mediator.


def export(context, properties, filepath):
    """Processes the data from the scene and writes it to a BLB file.

    Args:
        context (Blender context object): A Blender object containing scene data.
        properties (Blender properties object): A Blender object containing user preferences.
        filepath (string): The path to the BLB to be written, with the extension.

    Returns:
        True if the BLB file was written.
    """

    from . import blb_processor, blb_writer

    # TODO: Exporting multiple bricks from a single file.

    # Create a new processor and process the data.
    # The context variable contains all the Blender data.
    # The properties variable contains all user-defined settings to take into account when processing the data.
    blb_data = blb_processor.process_blender_data(context, properties)

    # The program has crashed long before reaching this line if blb_data is None...
    if blb_data is not None:
        # Write the data to a file.
        # TODO: Actually return true only if the file was written.
        blb_writer.write_file(properties, filepath, blb_data)
        return True

    return False
