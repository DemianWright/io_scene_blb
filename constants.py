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
Various constants used in multiple classes.

@author: Demian Wright
'''
from decimal import Decimal
from enum import Enum


class Axis(Enum):
    """An enumeration of the four directions axes can point in the XY plane."""
    positive_x = 0
    positive_y = 1
    negative_x = 2
    negative_y = 3


# Generic.
INDEX_X = 0
INDEX_Y = 1
INDEX_Z = 2

# Definition object name constants.
# TODO: Make these into properties.
BOUNDS_NAME_PREFIX = "bounds"
COLLISION_PREFIX = "collision"

# Brick grid definition object name prefixes in reverse priority order.
GRID_DEF_OBJ_PREFIX_PRIORITY = ("gridx",
                                "grid-",
                                "gridu",
                                "gridd",
                                "gridb")

QUAD_SECTION_ORDER = ["TOP", "BOTTOM", "NORTH", "EAST", "SOUTH", "WEST", "OMNI"]

DEFAULT_COVERAGE = 9999

AXIS_STRING_ENUM_DICT = {"POSITIVE_X": Axis.positive_x,
                         "POSITIVE_Y": Axis.positive_y,
                         "NEGATIVE_X": Axis.negative_x,
                         "NEGATIVE_Y": Axis.negative_y}

# A Blockland brick (plate) with dimensions 1 x 1 x 1 is equal to 1.0 x 1.0 x 0.4 Blender units (X,Y,Z)
PLATE_HEIGHT = Decimal("0.4")
