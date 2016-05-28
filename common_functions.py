'''
Various functions used in multiple classes.

@author: Demian Wright
'''

from constants import INDEX_X, INDEX_Y, INDEX_Z

def swizzle(sequence, order):
    """
    Specify the new order of the given sequence using lowercase letters a-z of the English alphabet.
    I.e. "a" signifies the index 0 and "z" stands for index 25.
    Allows duplicating values by specifying the the same letter multiple times.
    Returns a copy of the given sequence of up to 26 values in the specified order.
    """
    letters = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')

    # For every letter in the given order.
    # Get the index of the letter in the letters tuple.
    # Get the value of that index in the given sequence.
    # And add it to the new list.
    return [sequence[letters.index(letter)] for letter in order]

def rotate(xyz, forward_axis):
    """Returns a new list of XYZ values copied from the given XYZ sequence where given coordinates are rotated according to the selected forward axis."""

    rotated = []

    if forward_axis == "POSITIVE_X":
        # Rotate: 0 degrees clockwise
        return xyz

    elif forward_axis == "POSITIVE_Y":
        # Rotate: 90 degrees clockwise = X Y Z -> Y -X Z

        rotated.append(xyz[INDEX_Y])
        rotated.append(-xyz[INDEX_X])

    elif forward_axis == "NEGATIVE_X":
        # Rotate: 180 degrees clockwise = X Y Z -> -X -Y Z

        rotated.append(-xyz[INDEX_X])
        rotated.append(-xyz[INDEX_Y])

    elif forward_axis == "NEGATIVE_Y":
        # Rotate: 270 degrees clockwise = X Y Z -> -Y X Z

        rotated.append(-xyz[INDEX_Y])
        rotated.append(xyz[INDEX_X])

    # The Z axis is not yet taken into account.
    rotated.append(xyz[INDEX_Z])

    return rotated
