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

class Logger(object):
    """Logger class for printing messages to the console and optionally writing the messages to a log file."""
    __log_lines = []

    def __init__(self, write_file, warnings_only=True, logpath=""):
        """Initializes the logger with the specified options and an appropriate log path."""
        self.__write_file = write_file
        self.__warnings_only = warnings_only
        self.__logpath = logpath

    def log(self, message, is_warning=False):
        """Prints the given message to the console and additionally to a log file if so specified at object creation."""
        print(message)

        # Only write to a log if specified.
        if self.__write_file:
            if self.__warnings_only:
                # If only writing a log when a warning is encountered, ensure that current log message is a warning.
                if is_warning:
                    self.__log_lines.append(message)
            else:
                # Alternatively write to a log if writing all messages.
                self.__log_lines.append(message)

    def warning(self, message):
        """Shorthand for log(message, True) to improve clarity."""
        self.log(message, True)

    def write_log(self):
        """Writes a log file only if so specified at object creation."""
        # Write a log file? Anything to write?
        if self.__write_file and len(self.__log_lines) > 0:
            if self.__warnings_only:
                print("Writing log (warnings only) to:", self.__logpath)
            else:
                print("Writing log to:", self.__logpath)

            # Write the log file.
            with open(self.__logpath, "w") as file:
                for line in self.__log_lines:
                    file.write(line)
                    file.write("\n")
