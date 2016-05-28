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

# Generic.
INDEX_X = 0
INDEX_Y = 1
INDEX_Z = 2

# Definition object name constants.
# TODO: Make these properties.
BOUNDS_NAME_PREFIX = "bounds"
COLLISION_PREFIX = "collision"


# Brick grid definition object name prefixes in reverse priority order.
GRID_DEF_OBJ_PREFIX_PRIORITY = ("gridx",
                                "grid-",
                                "gridu",
                                "gridd",
                                "gridb")

QUAD_SECTION_ORDER = ["TOP", "BOTTOM", "NORTH", "EAST", "SOUTH", "WEST", "OMNI"]
