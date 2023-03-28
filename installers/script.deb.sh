#!/bin/bash

source "scripts/misc.sh"
source "scripts/pre_checks.sh"
source "scripts/naomi_cmds.sh"

#########################################
# Installs python and necessary packages
# for deb based Naomi. This script will install python
# into the ~/.config/naomi/local/bin directory and
# install naomi & requirements in their
# respective directories.
#########################################

setup_wizard() {
    WizardSetup()
    echo
    printf "${B_W}=========================================================================${NL}"
    printf "${B_W}SECURITY SETUP:${NL}"
    printf "${B_W}Let's examine a few security settings.${NL}"
    echo
    printf "${B_W}By default, Naomi is configured to require a password to perform actions as${NL}"
    printf "${B_W}root (e.g. 'sudo ...') as well as confirm commands before continuing.${NL}"
    printf "${B_W}This means you will have to watch the setup process to confirm everytime a new${NL}"
    printf "${B_W}command needs to run.${NL}"
    echo
    printf "${B_W}However you can enable Naomi to continue the process uninterrupted for a hands off experience${NL}"
    echo
    printf "${B_W}Would you like the setup to run uninterrupted or would you like to look over the setup process?${NL}"
    echo
    printf "${B_M}  1${B_W}) Allow the process to run uninterrupted${NL}"
    printf "${B_M}  2${B_W}) Require authentication to continue and run commands${NL}"
    printf "${B_Blue}Choice [${B_M}1${B_Blue}-${B_M}2${B_Blue}]: ${B_W}"
    while true; do
        read -N1 -s key
        case $key in
         [1])
            printf "${B_M}$key ${B_W}- Proceeding uninterrupted${NL}"
            REQUIRE_AUTH="0"
            SUDO_APPROVE="-y"
            break
            ;;
         [2])
            printf "${B_M}$key ${B_W}- Requiring authentication${NL}"
            REQUIRE_AUTH="1"
            SUDO_APPROVE=""
            break
            ;;
        esac
    done
    echo
    echo
    echo

    env
    createDirs

    naomiChannel

    while true; do
        read -N1 -s key
        case $key in
         1)
            defaultFlavor
            break
            ;;
         2)
           stableVersion
           break
           ;;
         3)
           nightlyVersion
           break
           ;;
         S)
           skipFlavor
           break
           ;;
        esac
    done
    echo
    echo

    echo "entering findScripts"
    findScripts

    NAOMI_DIR="$(cd ~/Naomi && pwd)"
    echo "Naomi_dir=$NAOMI_DIR"
    cd ~/Naomi
    APT=1
    printf "APT = ${APT}${NL}"
    if [ $APT -eq 1 ]; then
      if [ $REQUIRE_AUTH -eq 1 ]; then
        SUDO_COMMAND "sudo apt-get update"
        SUDO_COMMAND "sudo apt upgrade $SUDO_APPROVE"
        SUDO_COMMAND "sudo ./naomi_requirements.sh $SUDO_APPROVE"
        if [ $? -ne 0 ]; then
          printf "${B_R}Notice:${B_W} Error installing apt packages${NL}" >&2
          exit 1
        fi
      else
        printf "${B_W}${NL}"
        sudo apt-get update
        sudo apt upgrade $SUDO_APPROVE
        sudo ./naomi_requirements.sh $SUDO_APPROVE
        if [ $? -ne 0 ]; then
          printf "${B_R}Notice:${B_W} Error installing apt packages${NL}" >&2
          exit 1
        fi
      fi      
    else
      ERROR=""
      if [[ $(CHECK_PROGRAM msgfmt) -ne "0" ]]; then
        ERROR="${ERROR} ${B_R}Notice:${B_W} gettext program msgfmt not found${NL}"
      fi
      if [[ $(CHECK_HEADER portaudio.h) -ne "0" ]]; then
        ERROR="${ERROR} ${B_R}Notice:${B_W} portaudio development file portaudio.h not found${NL}"
      fi
      if [[ $(CHECK_HEADER asoundlib.h) -ne "0" ]]; then
        ERROR="${ERROR} ${B_R}Notice:${B_W} libasound development file asoundlib.h not found${NL}"
      fi
      if [[ $(CHECK_PROGRAM python3) -ne "0" ]]; then
        ERROR="${ERROR} ${B_R}Notice:${B_W} python3 not found${NL}"
      fi
      if [[ $(CHECK_PROGRAM pip3) -ne "0" ]]; then
        ERROR="${ERROR} ${B_R}Notice:${B_W} pip3 not found${NL}"
      fi
      if [ ! -z "$ERROR" ]; then
        printf "${B_R}Notice:${B_W} Missing dependencies:${NL}${NL}$ERROR"
        CONTINUE
      fi
    fi

    # make sure pulseaudio is running
    pulseaudio --check
    if [ $? -ne 0 ]; then
      pulseaudio -D
    fi

    setupVenv
    
    findScripts

    # start the naomi setup process
    processNaomi

    pluginMsg

    # Get packages & build Phonetisaurus 
    # Building and installing openfst
    openfst

    # Building and installing mitlm-0.4.2
    mitlm

    # Building and installing CMUCLMTK
    cmuclmtk
    
    # Building and installing phonetisaurus
    #phonetisaurus

    # Installing & Building sphinxbase
    sphinxbase
    
    # Installing & Building pocketsphinx
    pocketsphinx

    # Installing PocketSphinx Python module
    pocketSphinx_python

    # Compiling Translations
    compileTranslations
}

setup_wizard
