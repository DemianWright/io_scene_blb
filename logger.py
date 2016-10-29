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
A module for printing messages to the console and optionally writing the messages to a log file.

@author: Demian Wright
'''

# I've implemented this myself instead of using the standard logging because I needed a feature where the log file is only written if there were warnings logged.
# I could not figure out a way to do that with the standard logging library so it was just faster to write it myself.

import bpy

__LOG_LINES = []
__WRITE_FILE = False
__WARNINGS_ONLY = True


def configure(write_file, write_only_on_warnings):
    """Configures the logger with the specified options.

    Args:
        write_file (bool): Write log to a file?
        write_only_on_warnings (bool): Write log to a file but only if warnings were logged."""
    global __WRITE_FILE, __WARNINGS_ONLY

    __WRITE_FILE = write_file
    __WARNINGS_ONLY = write_only_on_warnings


def __log(message, is_warning):
    """Prints the given message to the console and additionally to a log file if so specified at logger configuration.

    Args:
        message (string): Log message.
        is_warning (bool): Is the message a warning?"""
    print(message)

    # If log will be written to a file, append the message to the sequence for writing later.
    if __WRITE_FILE:
        # If log file will only be written when a warning is encountered.
        if __WARNINGS_ONLY:
            # Check that current message is a warning.
            if is_warning:
                __LOG_LINES.append(message)
            # Otherwise ignore the message.
        else:
            # Else if all messages are written to a log file, append the message to the sequence.
            __LOG_LINES.append(message)


def info(message):
    """Prints the given message to the console and additionally to a log file if so specified at logger configuration.

    Args:
        message (string): Log message."""
    __log(message, False)


def warning(message):
    """Prefixes the message with '[WARNING] ', prints it to the console (and additionally to a log file if so specified at logger configuration), and logs the message as a warning.

    Args:
        message (string): Log message."""
    __log("[WARNING] " + message, True)


def error(message):
    """Prefixes the message with '[ERROR] ', prints it to the console (and additionally to a log file if so specified at logger configuration), and logs the message as a warning.

    Args:
        message (string): Log message."""
    __log("[ERROR] " + message, True)


def build_countable_message(message_start, count, alternatives, message_end="", message_zero=None):
    """Builds a sentence with the correct message ending (i.e. singular or plural) based on the countable element.

    The function will append the start, the count, the singular or plural, and the end of the message one after the other without adding spaces in between.

    Args:
        message_start (string): The first part of message that will be the same for singular and plural messages.
        count (int): The countable element in the message that will determine if the message is singular or plural.
        alternatives (sequence of strings): A sequence of strings where:
                                                - the first element will be used if count is 1,
                                                - the second element will be used if count is 2 or count is 0 and message_zero is not specified.
        message_end (string): An optional final part of the message.
        message_zero (string): An optional message to show instead if count is 0.

    Returns:
        A grammatically correct message.
    """
    # Determine which message to use from the end alternatives.
    if count == 0:
        if message_zero is not None:
            # If a zero count message was specified, use that instead.
            return message_zero
        else:
            # Else the count is 0 but no zero count message was specified, use the plural message.
            message_index = 1
    elif count == 1:
        # Index 0 contains the singular.
        message_index = 0
    else:
        # Index 1 contains the plural.
        message_index = 1

    return "{}{}{}{}".format(message_start, count, alternatives[message_index], message_end)


def write_log(logpath):
    """Writes a log file (if so configured) to the specified path."""
    # Write a log file? Anything to write?
    if __WRITE_FILE and len(__LOG_LINES) > 0:
        if __WARNINGS_ONLY:
            print("Writing log (warnings only) to: {}{}".format(bpy.path.abspath("//"), logpath))
        else:
            print("Writing log to: {}{}".format(bpy.path.abspath("//"), logpath))

        # Write the log file.
        with open(logpath, "w") as file:
            for line in __LOG_LINES:
                file.write(line)
                file.write("\n")
