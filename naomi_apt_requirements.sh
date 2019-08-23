#!/bin/bash
xargs -a <(awk '! /^ *(#|$)/' apt_requirements.txt) -r -- sudo apt install

