# -*- coding: utf-8 -*-
import subprocess

def run_command(command):
    return subprocess.run(
        command,
        stdout=subprocess.PIPE
    ).stdout.decode('utf-8').strip()
