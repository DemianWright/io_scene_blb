'''
Various functions used in multiple classes.

@author: Demian Wright
'''

# Blender requires imports from ".".
from . import constants

def swizzle(sequence, order):
    """
    Changes the order of the elements in the specified sequence of up to 26 elements.
    The new order of the sequence must be specified as string or a sequence of lower case letters.
    Sequence indices are represented using lower case letters a-z of the Latin alphabet.
    I.e. "a" signifies the index 0 and "z" stands for index 25.
    Duplicating elements is possible by specifying the the same letter multiple times.
    Returns a copy of the specified sequence in the specified order.
    """
    letters = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')

    # For every letter in the given order.
    # Get the index of the letter in the letters tuple.
    # Get the value of that index in the given sequence.
    # And add it to the new list.
    # Return the new list.
    return [sequence[letters.index(letter)] for letter in order]

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
