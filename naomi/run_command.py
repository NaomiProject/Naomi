# -*- coding: utf-8 -*-
import subprocess

def run_command(command):
    return subprocess.check_output(
        command,
        shell=False
    ).decode('utf-8').strip()
