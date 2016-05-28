'''
A module for printing messages to the console and optionally writing the messages to a log file.

@author: Demian Wright
'''
# I've implemented this myself instead of using the standard logging because I needed a feature where the log file is only written if there were warnings logged.
# I could not figure out a way to do that with the standard logging library so it was just faster to write it myself.
LOG_LINES = []
__WRITE_FILE = False
__WARNINGS_ONLY = True
__LOGPATH = ""

def configure(write_file, write_only_on_warnings, logpath):
    """Configures the logger with the specified options and a log path."""
    global __WRITE_FILE, __WARNINGS_ONLY, __LOGPATH

    __WRITE_FILE = write_file
    __WARNINGS_ONLY = write_only_on_warnings
    __LOGPATH = logpath

def info(message, is_warning=False):
    """Prints the given message to the console and additionally to a log file if so specified at logger creation."""
    print(message)

    # If log will be written to a file, append the message to the sequence for writing later.
    if __WRITE_FILE:
        # If log file will only be written when a warning is encountered.
        if __WARNINGS_ONLY:
            # Check that current message is a warning.
            if is_warning:
                LOG_LINES.append(message)
            # Otherwise ignore the message.
        else:
            # Else if all messages are written to a log file, append the message to the sequence.
            LOG_LINES.append(message)

def warning(message):
    """Prefixes the message with '[WARNING] ' and logs the message as a warning."""
    info("[WARNING] " + message, True)

def error(message):
    """Prefixes the message with '[ERROR] ' and logs the message as a warning."""
    info("[ERROR] " + message, True)

def write_log():
    """Writes a log file (if so configured) to the path specified at logger creation."""
    # Write a log file? Anything to write?
    if __WRITE_FILE and len(LOG_LINES) > 0:
        if __WARNINGS_ONLY:
            print("Writing log (warnings only) to:", __LOGPATH)
        else:
            print("Writing log to:", __LOGPATH)

        # Write the log file.
        with open(__LOGPATH, "w") as file:
            for line in LOG_LINES:
                file.write(line)
                file.write("\n")
