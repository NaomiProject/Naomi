#!/bin/bash
SUDO_APPROVE=""

DebianSetup() {
    for var in "$@"; do
        if [ "$var" = "-y" ] || [ "$var" = "--yes" ]; then
            SUDO_APPROVE="-y"
        fi
    done
    xargs -a <(awk '! /^ *(#|$)/' apt_requirements.txt) -r -- apt install $SUDO_APPROVE
}

ArchSetup() {
    for var in "$@"; do
        if [ "$var" = "-y" ] || [ "$var" = "--yes" ]; then
            SUDO_APPROVE="--noconfirm"
        fi
    done
    xargs -a <(awk '! /^ *(#|$)/' arch_requirements.txt) -r -- pacman -Syu $SUDO_APPROVE
}

if [ -e /etc/os-release ]; then
    /etc/os-release
    os=${ID}
    os_like=${ID_LIKE}
    if [ "${os_like}"="arch" ]; then
        ArchSetup
    elif [ "${os}"="debian" ]; then
        DebianSetup
    elif [ "${os}"="arch" ]; then
        ArchSetup
    fi
else
    echo "Can't detect OS script will exit now..."
    exit 1
fi
