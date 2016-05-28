'''
Various functions used in multiple classes.

@author: Demian Wright
'''

from string import ascii_lowercase

# Blender requires imports from ".".
from . import constants


def swizzle(sequence, order):
    """
    Changes the order of the elements in the specified sequence. (Max 26 elements.)
    The new order of the sequence must be specified as string or a sequence of lower case Latin letters.
    Sequence indices are represented using lower case letters a-z of the Latin alphabet.
    I.e. "a" signifies the index 0 and "z" stands for index 25.
    Duplicating elements is possible by specifying the the same letter multiple times.
    Returns a new sequence of values shallowly copied from the specified sequence in the specified order.
    The new sequence will only contain the elements specified in the order.
    """
    # For every letter in the specified order.
    # Get the index of the letter in the ascii_lowercase string.
    # Get the value of that index in the specified sequence.
    # Add it to a new list.
    # Return the new list.
    return [sequence[ascii_lowercase.index(letter)] for letter in order]


def rotate(xyz, forward_axis):
    """
    Rotates the specified XYZ coordinate sequence according to the specified forward axis so the points will be correctly represented in the game.
    By default Blockland assumes that coordinates are relative to +X axis being the brick forward axis pointing away from the player.
    Returns a new list of XYZ coordinates.
    """
    rotated = []

    if forward_axis == "POSITIVE_X":
        # Rotate: 0 degrees clockwise
        return xyz

    elif forward_axis == "POSITIVE_Y":
        # Rotate: 90 degrees clockwise = X Y Z -> Y -X Z
        rotated.append(xyz[constants.INDEX_Y])
        rotated.append(-xyz[constants.INDEX_X])

    elif forward_axis == "NEGATIVE_X":
        # Rotate: 180 degrees clockwise = X Y Z -> -X -Y Z
        rotated.append(-xyz[constants.INDEX_X])
        rotated.append(-xyz[constants.INDEX_Y])

    elif forward_axis == "NEGATIVE_Y":
        # Rotate: 270 degrees clockwise = X Y Z -> -Y X Z
        rotated.append(-xyz[constants.INDEX_Y])
        rotated.append(xyz[constants.INDEX_X])

    # The Z axis is not yet taken into account.
    rotated.append(xyz[constants.INDEX_Z])

    return rotated
