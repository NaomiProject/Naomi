# -*- coding: utf-8 -*-
import subprocess

def run_command(command):
    output = subprocess.check_output(
        ['/usr/bin/flite','-lv'],
        shell=False
    ).decode('utf-8').strip()
    return output
