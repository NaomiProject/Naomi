#!/bin/bash
SUDO_APPROVE=""
for var in "$@"; do
    if [ "$var" = "-y" ] || [ "$var" = "--yes" ]; then
        SUDO_APPROVE="-y"
    fi
done
xargs -a <(awk '! /^ *(#|$)/' apt_requirements.txt) -r -- apt install $SUDO_APPROVE

