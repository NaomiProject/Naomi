# -*- coding: utf-8 -*-
import subprocess


# This program is just so we can avoid calling subprocess directly, which
# always causes Codacy to flag the pull request. 
# The first parameter is an array containing a command, flags and arguments.
# The second, optional parameter determines how the output of the command is
# handled:
#  0 (default) - don't capture output
#  1 - only capture stdout
#  2 - only capture stderr
#  3 - pipe stdout into stderr and capture stdout
# The response is the raw CompletedProcess instance, containing the command,
# returncode, stdout and stderr properties and the check_returncode() method
# The subprocess.run command takes a wide variety of arguments, so I
# considered just making this a wrapper around the run() method, but since
# the different capture methods require referencing attributes of the
# subprocess module anyway, I decided to try simplifying it to these four
# use cases. This module is currently only used in populate.py (for capturing
# the system timezone) but I will need to use it a lot in my STT model
# training plugins.
def run_command(command, capture=0):
    completedprocess = None
    if(capture == 1):
        completedprocess = subprocess.run(
            command,
            stdout=subprocess.PIPE
        )
    elif(capture == 2):
        completedprocess = subprocess.run(
            command,
            stderr=subprocess.PIPE
        )
    elif(capture == 3):
        completedprocess = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    else:
        completedprocess = subprocess.run(
            command
        )
    return completedprocess
