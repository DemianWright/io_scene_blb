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
Various constants used in multiple modules.

@author: Demian Wright
'''

# The BLB file extension.
BLB_EXT = '.blb'

# The log file extension.
LOG_EXT = '.log'

# One log indent level.
LOG_INDENT = '  '

# Generic.
X = 0
Y = 1
Z = 2

# Blockland does not accept bricks that are wide/deeper than 64 bricks or taller than 256 plates.
MAX_BRICK_HORIZONTAL_PLATES = 64
MAX_BRICK_VERTICAL_PLATES = 256

# Quad and coverage section IDs and directions for sorting.
QUAD_SECTION_IDX_TOP = 0
QUAD_SECTION_IDX_BOTTOM = 1
QUAD_SECTION_IDX_NORTH = 2
QUAD_SECTION_IDX_EAST = 3
QUAD_SECTION_IDX_SOUTH = 4
QUAD_SECTION_IDX_WEST = 5
QUAD_SECTION_IDX_OMNI = 6

# The quad sections in the correct order for writing to a BLB file.
QUAD_SECTION_ORDER = ('TOP', 'BOTTOM', 'NORTH', 'EAST', 'SOUTH', 'WEST', 'OMNI')

# A tuple of valid brick textures in alphabetical order-
VALID_BRICK_TEXTURES = ('BOTTOMEDGE', 'BOTTOMLOOP', 'RAMP', 'SIDE', 'TOP')

# The default coverage value = no coverage. (Number of plates that need to cover a brick side to hide it.)
# The maximum area a brick's side can cover is 64 * 256 = 16384 plates.
DEFAULT_COVERAGE = 99999

# Brick grid symbols.
GRID_INSIDE = 'x'  # Disallow building inside brick.
GRID_OUTSIDE = '-'  # Allow building in empty space.
GRID_UP = 'u'  # Allow placing bricks above this plate.
GRID_DOWN = 'd'  # Allow placing bricks below this plate.
GRID_BOTH = 'b'  # Allow placing bricks above and below this plate.

# Maximum number of decimal places to write to file.
MAX_FP_DECIMALS_TO_WRITE = 16
