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
#  4 - pipe stdin to subprocess and capture output
# The response is the raw CompletedProcess instance, containing the command,
# returncode, stdout and stderr properties and the check_returncode() method
# The subprocess.run command takes a wide variety of arguments, so I
# considered just making this a wrapper around the run() method, but since
# the different capture methods require referencing attributes of the
# subprocess module anyway, I decided to try simplifying it to these four
# use cases. This module is currently only used in populate.py (for capturing
# the system timezone) but I will need to use it a lot in my STT model
# training plugins.
# Aaron.Chantrill - added optional CWD parameter for specifying the directory
# where the command should be run from.
def run_command(command, capture=0, stdin=None, cwd=None):
    completedprocess = None
    if(capture == 1):
        completedprocess = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            cwd=cwd
        )
    elif(capture == 2):
        completedprocess = subprocess.run(
            command,
            stderr=subprocess.PIPE,
            cwd=cwd
        )
    elif(capture == 3):
        completedprocess = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd
        )
    elif (capture == 4):
        completedprocess = subprocess.run(
            command,
            input=stdin.encode() if hasattr(stdin, "encode") else stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd
        )
    else:
        completedprocess = subprocess.run(
            command,
            cwd=cwd
        )
    return completedprocess


def process_completedprocess(completedprocess, output='text'):
    result = "failure"
    command = " ".join(completedprocess.args)
    response = ""
    if(output == 'html'):
        response = "<h3>Check log for details</h3>\n"
    if(completedprocess.stdout):
        response = " - {}".format(
            completedprocess.stdout.decode("utf-8").strip()
        )
    if(completedprocess.returncode == 0):
        result = "success"
        response = ""
    if(output == 'html'):
        return '<pre>{}</pre>...<span class="{}">{}</span>{}'.format(
            command,
            result,
            result.upper(),
            response
        )
    else:
        return '{}...{}{}'.format(
            command,
            result,
            response
        )
