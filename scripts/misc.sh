#!/bin/bash

#########################################
# Miscellaneous Script That has variables
# For Naomi Build Scripts
#########################################

BLACK='\033[1;30m'
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
MAGENTA='\033[1;35m'
CYAN='\033[1;36m'
WHITE='\033[1;37m'
B_C='\033[1;96m' #Bright Cyan                           For logo
B_R='\033[1;91m' #Bright Red                            For alerts/errors
B_G='\033[1;92m' #Bright Green                          For initiating a process i.e. "Installing blah blah..." or calling attention to thing in outputs
B_Y='\033[1;93m' #Bright Yellow                         For urls & emails
B_Black='\033[1;90m' #Bright Black                      For lower text
B_Blue='\033[1;94m' #Bright Blue                        For prompt question
B_M='\033[1;95m' #Bright Magenta                        For prompt choices
B_W='\033[1;97m' #Bright White                          For standard text output
NL="
"
OPTION="0"
SUDO_APPROVE=""
version="3.0"
theDateRightNow=$(date +%m-%d-%Y-%H:%M:%S)
gitVersionNumber=$(git rev-parse --short HEAD)
gitURL="https://github.com/naomiproject/naomi"

GIT="git"
JQ="jq"
CURL="curl"
PYTHON="python"
ZIP="zip"

printNaomi() {

    echo
    printf "${B_C}      ___           ___           ___           ___                  ${NL}"
    printf "${B_C}     /\__\         /\  \         /\  \         /\__\          ___    ${NL}"
    printf "${B_C}    /::|  |       /::\  \       /::\  \       /::|  |        /\  \   ${NL}"
    printf "${B_C}   /:|:|  |      /:/\:\  \     /:/\:\  \     /:|:|  |        \:\  \  ${NL}"
    printf "${B_C}  /:/|:|  |__   /::\~\:\  \   /:/  \:\  \   /:/|:|__|__      /::\__\ ${NL}"
    printf "${B_C} /:/ |:| /\__\ /:/\:\ \:\__\ /:/__/ \:\__\ /:/ |::::\__\  __/:/\/__/ ${NL}"
    printf "${B_C} \/__|:|/:/  / \/__\:\/:/  / \:\  \ /:/  / \/__/~~/:/  / /\/:/  /    ${NL}"
    printf "${B_C}     |:/:/  /       \::/  /   \:\  /:/  /        /:/  /  \::/__/     ${NL}"
    printf "${B_C}     |::/  /        /:/  /     \:\/:/  /        /:/  /    \:\__\     ${NL}"
    printf "${B_C}     /:/  /        /:/  /       \::/  /        /:/  /      \/__/     ${NL}"
    printf "${B_C}     \/__/         \/__/         \/__/         \/__/                 ${NL}"

    sleep 5

    echo

}

createDirs(){
  # Create basic folder structures
  echo
  printf "${B_G}Creating File Structure...${B_W}${NL}"
  mkdir -p ~/.config/naomi/
  mkdir -p ~/.config/naomi/configs/
  mkdir -p ~/.config/naomi/scripts/
  mkdir -p ~/.config/naomi/sources/

}

installDone() {
      echo
      echo
      echo
      echo
      printf "${B_W}=========================================================================${NL}"
      echo
      printf "${B_W}That's all, installation is complete! All that is left is the profile${NL}"
      printf "${B_W}population process and after that Naomi will start.${NL}"
      echo
      printf "${B_W}In the future, to start Naomi type '${B_G}Naomi${B_W}' in a terminal${NL}"
      echo
      printf "${B_W}Please type '${B_G}Naomi --repopulate${B_W}' on the prompt below to populate your profile...${NL}"
      sudo rm -Rf ~/Naomi-Temp
      # Launch Naomi Population
      cd ~/Naomi
      chmod a+x Naomi.sh
      cd ~
      exec bash
}

existingInstall() {
    printf "${B_W}=========================================================================${NL}"
    printf "${B_W}It looks like you have Naomi source in the ${B_G}~/Naomi${B_W} directory,${NL}"
    printf "${B_W}however it looks to be out of date. Please update or remove the Naomi${NL}"
    printf "${B_W}source and try running the installer again.${NL}"
    echo
    printf "${B_W}Please join our Discord or email us at ${B_Y}contact@projectnaomi.com${B_W} and let us know if you run into any issues.${NL}"
    exit 1
}

wizardSetup(){

  echo
  printf "${B_W}=========================================================================${NL}"
  printf "${B_W}ARCH SETUP WIZARD${NL}"
  printf "${B_W}This process will first walk you through setting up your device,${NL}"
  printf "${B_W}installing Naomi, and default plugins.${NL}"
  echo
  sleep 3
  echo
  echo

  echo
  printf "${B_W}=========================================================================${NL}"
  printf "${B_W}LOCALIZATION SETUP:${NL}"
  printf "${B_W}Let's examine your localization settings.${NL}"
  echo
  sleep 3
  echo

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
}

env(){
  echo
  echo
  echo

  echo
  printf "${B_W}=========================================================================${NL}"
  printf "${B_W}ENVIRONMENT SETUP:${NL}"
  printf "${B_W}Now setting up the file stuctures & requirements${NL}"
  echo
  sleep 3
  echo


}

naomiChannel(){
  echo
  printf "${B_W}=========================================================================${NL}"
  printf "${B_W}NAOMI SETUP:${NL}"
  printf "${B_W}Naomi is continuously updated. There are three options to choose from:${NL}"
  echo
  printf "${B_W}'${B_G}Stable${B_W}' versions are thoroughly tested official releases of Naomi. Use${NL}"
  printf "${B_W}the stable version for your production environment if you don't need the${NL}"
  printf "${B_W}latest enhancements and prefer a robust system${NL}"
  echo
  printf "${B_W}'${B_G}Milestone${B_W}' versions are intermediary releases of the next Naomi version,${NL}"
  printf "${B_W}released about once a month, and they include the new recently added${NL}"
  printf "${B_W}features and bugfixes. They are a good compromise between the current${NL}"
  printf "${B_W}stable version and the bleeding-edge and potentially unstable nightly version.${NL}"
  echo
  printf "${B_W}'${B_G}Nightly${B_W}' versions are at most 1 or 2 days old and include the latest code.${NL}"
  printf "${B_W}Use nightly for testing out very recent changes, but be aware some nightly${NL}"
  printf "${B_W}versions might be unstable. Use in production at your own risk!${NL}"
  echo
  printf "${B_W}Note: '${B_G}Nightly${B_W}' comes with automatic updates by default!${NL}"
  echo
  printf "${B_M}  1${B_W}) Use the recommended ('${B_G}Stable${B_W}')${NL}"
  printf "${B_M}  2${B_W}) Monthly releases sound good to me ('${B_G}Milestone${B_W}')${NL}"
  printf "${B_M}  3${B_W}) I'm a developer or want the cutting edge, put me on '${B_G}Nightly${B_W}'${NL}"
  printf "${B_Blue}Choice [${B_M}1${B_Blue}-${B_M}3${B_Blue}]: ${B_W}"
}
