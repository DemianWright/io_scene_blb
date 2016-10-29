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
A module for writing data into a BLB file.

@author: Demian Wright
'''

# Blender requires imports from ".".
from . import const


def __write_sequence(file, sequence, new_line=True, decimal_digits=None):
    """Writes the values of the specified sequence separated with spaces into the specified file.
    An optional new line character is added at the end of the line by default.

    Args:
        file (object): The file to be written to.
        sequence (sequence): A sequence of data to be written.
        new_line (bool): Add a newline character at the end of the line?
        decimal_digits (int): The number of decimal digits to write if the sequence contains floating point values."""
    for index, value in enumerate(sequence):
        if index != 0:
            # Write a space before each value except the first one.
            file.write(" ")
        if value == 0:
            # Handle zeros.
            file.write("0")
        else:
            # TODO: The trimming should be a property.
            # Format the value into string, remove all zeros from the end, then remove all periods.
            if decimal_digits is None:
                file.write("{}".format(value).rstrip('0').rstrip('.'))
            else:
                file.write("{0:.{1}f}".format(value, decimal_digits).rstrip('0').rstrip('.'))
    if new_line:
        # Write a new line after all values.
        file.write("\n")


def write_file(filepath, blb_data):
    """Writes the BLB file.

    Args:
        filepath (string): Path to the BLB file to be written.
        blb_data (BLBData): A BLBData object containing the data to be written."""
    with open(filepath, "w") as file:
        # ----------
        # Brick Size
        # ----------
        __write_sequence(file, blb_data.brick_size)

        # ----------
        # Brick Type
        # ----------
        file.write("SPECIAL\n\n")

        # ----------
        # Brick Grid
        # ----------
        for axis_slice in blb_data.brick_grid:
            for row in axis_slice:
                # Join each Y-axis of data without a separator.
                file.write("".join(row) + "\n")

            # A new line after each axis slice.
            file.write("\n")

        # ---------
        # Collision
        # ---------
        if len(blb_data.collision) == 0:
            # Write default collision.

            file.write("1\n")
            file.write("\n")

            # Center of the cuboid is at the middle of the brick.
            file.write("0 0 0\n")

            # The size of the cuboid is the size of the bounds.
            __write_sequence(file, blb_data.brick_size)
        else:
            # Write defined collisions.

            # Write the number of collision cuboids.
            file.write(str(len(blb_data.collision)))
            file.write("\n")

            for (center, dimensions) in blb_data.collision:
                file.write("\n")
                __write_sequence(file, center)
                __write_sequence(file, dimensions)

        # --------
        # Coverage
        # --------
        file.write("COVERAGE:\n")
        for (hide_adjacent, plate_count) in blb_data.coverage:
            file.write(str(int(hide_adjacent)) + " : " + str(plate_count) + "\n")

        # -----
        # Quads
        # -----
        for index, section_name in enumerate(const.QUAD_SECTION_ORDER):
            # TODO: Terse mode where optional stuff is excluded.

            # Write section name.
            file.write("--{} QUADS--\n".format(section_name))  # Optional.

            # Write section length.
            file.write("{}\n".format(str(len(blb_data.quads[index]))))

            for (positions, normals, uvs, colors, texture) in blb_data.quads[index]:
                # Face texture name.
                file.write("\nTEX:")  # Optional.
                file.write(texture)

                # Vertex positions.
                file.write("\nPOSITION:\n")  # Optional.
                for position in positions:
                    __write_sequence(file, position, True, const.FLOATING_POINT_DECIMALS)

                # Face UV coordinates.
                file.write("UV COORDS:\n")  # Optional.
                for uv_vector in uvs:
                    __write_sequence(file, uv_vector)

                # Vertex normals.
                file.write("NORMALS:\n")  # Optional.
                for normal in normals:
                    __write_sequence(file, normal)

                # Vertex colors, if any.
                if colors is not None:
                    file.write("COLORS:\n")  # Optional.
                    for color in colors:
                        __write_sequence(file, color)
