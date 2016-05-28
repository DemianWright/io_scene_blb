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
