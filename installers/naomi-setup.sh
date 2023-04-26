#!/bin/bash

source "scripts/misc.sh"
source "scripts/pre_checks.sh"
source "scripts/naomi_cmds.sh"

#########################################
# Determines the OS & Version to direct
# Naomi build process correctly.
#########################################

curl_check
jq_check
python_check
git_check
zip_check

apt_setup_wizard() {
  if [ ! -f ~/Naomi/README.md ]; then
    echo
    printf "${B_G}Starting Naomi Apt Setup Wizard...${NL}${B_W}"
    . <( wget -O - "https://installers.projectnaomi.com/script.deb.sh" );
    wget_exit_code=$?
    if [ "$wget_exit_code" = "0" ]; then
      installDone
    else
      echo
      printf "${B_R}Notice: ${B_W}Naomi Apt Setup Wizard Failed.${NL}"
      echo
      exit 1
    fi
  elif [ -f ~/Naomi/README.md ] && [ -f ~/Naomi/installers/script.deb.sh ]; then
    chmod a+x ~/Naomi/installers/script.deb.sh
    bash ~/Naomi/installers/script.deb.sh
    script_exit_code=$?
    if [ "$script_exit_code" = "0" ]; then
      installDone
    else
      echo
      printf "${B_R}Notice: ${B_W}Naomi Apt Setup Wizard Failed.${NL}"
      echo
      exit 1
    fi
  else
    existingInstall
  fi
}
yum_setup_wizard() {
  if [ ! -f ~/Naomi/README.md ]; then
    echo
    echo
    echo
    echo
    printf "${B_G}Starting Naomi Yum Setup Wizard...${NL}${B_W}"
    . <( wget -O - "https://installers.projectnaomi.com/script.rpm.sh" );
    wget_exit_code=$?
    if [ "$wget_exit_code" = "0" ]; then
      installDone
    else
      echo
      printf "${B_R}Notice: ${B_W}Naomi Yum Setup Wizard Failed.${NL}"
      echo
      exit 1
    fi
  elif [ -f ~/Naomi/README.md ] && [ -f ~/Naomi/installers/script.rpm.sh ]; then
    chmod a+x ~/Naomi/installers/script.rpm.sh
    bash ~/Naomi/installers/script.rpm.sh
    script_exit_code=$?
    if [ "$script_exit_code" = "0" ]; then
      installDone
    else
      echo
      printf "${B_R}Notice: ${B_W}Naomi Yum Setup Wizard Failed.${NL}"
      echo
      exit 1
    fi
  else
    existingInstall
  fi
}


tput reset
sleep 5

printNaomi

if [ "$1" == "--uninstall" ]; then
    naomi_uninstall
fi

installOptions
