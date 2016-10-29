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

# Generic.
X = 0
Y = 1
Z = 2

# TODO: Make most of these into properties.

# Definition object name const.
BOUNDS_NAME_PREFIX = "bounds"
COLLISION_PREFIX = "collision"

# Error allowed for manually created definition objects, because they must lie exactly on the brick grid.
# Used for rounding vertex positions to the brick grid.
HUMAN_ERROR = Decimal("0.1")

# Brick grid definition object name prefixes in reverse priority order.
GRID_DEF_OBJ_PREFIX_PRIORITY = ("gridx",
                                "grid-",
                                "gridu",
                                "gridd",
                                "gridb")

# Quad and coverage section IDs and directions for sorting.
QUAD_SECTION_IDX_TOP = 0
QUAD_SECTION_IDX_BOTTOM = 1
QUAD_SECTION_IDX_NORTH = 2
QUAD_SECTION_IDX_EAST = 3
QUAD_SECTION_IDX_SOUTH = 4
QUAD_SECTION_IDX_WEST = 5
QUAD_SECTION_IDX_OMNI = 6

# The quad sections in the correct order for writing to a BLB file.
QUAD_SECTION_ORDER = ["TOP", "BOTTOM", "NORTH", "EAST", "SOUTH", "WEST", "OMNI"]

# The default coverage value = no coverage. (Number of plates that need to cover a brick side to hide it.)
DEFAULT_COVERAGE = 9999

# A Blockland brick (plate) with dimensions 1 x 1 x 1 is equal to 1.0 x 1.0 x 0.4 Blender units (X,Y,Z)
PLATE_HEIGHT = Decimal("0.4")

# Brick grid symbols.
GRID_INSIDE = "x"  # Disallow building inside brick.
GRID_OUTSIDE = "-"  # Allow building in empty space.
GRID_UP = "u"  # Allow placing bricks above this plate.
GRID_DOWN = "d"  # Allow placing bricks below this plate.
GRID_BOTH = "b"  # Allow placing bricks above and below this plate.

# Brick grid definitions in reverse priority order.
# I.e. GRID_DOWN will overwrite GRID_OUTSIDE.
GRID_DEFINITIONS_PRIORITY = (GRID_INSIDE,
                             GRID_OUTSIDE,
                             GRID_UP,
                             GRID_DOWN,
                             GRID_BOTH)

# Number of decimal places to round floating point numbers.
FLOATING_POINT_DECIMALS = 6
FLOATING_POINT_PRECISION = "0.000001"
