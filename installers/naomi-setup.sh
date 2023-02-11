#!/bin/bash

source "scripts/misc.sh"
source "scripts/pre_checks.sh"
source "scripts/naomi_cmds.sh"

#########################################
# Determines the OS & Version to direct
# Naomi build process correctly.
#########################################

#TODO: Call The following

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

#TODO: Why is there a second check?
tput reset
os_detect
curl_check
jq_check
python_check
git_check
zip_check

sleep 5
tput reset

printNaomi

if [ "$1" == "--uninstall" ]; then
	naomi_uninstall
fi

printf "${B_W}=========================================================================${NL}"
printf "${B_W}Welcome to the Naomi Installer. Pick one of the options below to get started:${NL}"
echo
printf "${B_W}'${B_M}Install${B_W}':${NL}"
printf "${B_W}This will fresh install & setup Naomi on your system.${NL}"
echo
printf "${B_W}'${B_M}Uninstall${B_W}':${NL}"
printf "${B_W}This will remove Naomi from your system.${NL}"
echo
printf "${B_W}'${B_M}Update${B_W}':${NL}"
printf "${B_W}This will update Naomi if there is a newer release for your installed version.${NL}"
echo
printf "${B_W}'${B_M}Version${B_W}':${NL}"
printf "${B_W}This will allow you to switch what version of Naomi you have installed.${NL}"
echo
printf "${B_W}'${B_M}AutoUpdate${B_W}':${NL}"
printf "${B_W}This will allow you to enable/disable Naomi auto updates.${NL}"
echo
printf "${B_W}'${B_M}Quit${B_W}'${NL}"
echo
printf "${B_Blue}Input: ${B_W}"
while true; do
    read installerChoice
    if [ "$installerChoice" = "install" ] || [ "$installerChoice" = "INSTALL" ] || [ "$installerChoice" = "Install" ]; then
        naomi_install
        break
    elif [ "$installerChoice" = "uninstall" ] || [ "$installerChoice" = "UNINSTALL" ] || [ "$installerChoice" = "Uninstall" ]; then
        naomi_uninstall
        break
    elif [ "$installerChoice" = "update" ] || [ "$installerChoice" = "UPDATE" ] || [ "$installerChoice" = "Update" ]; then
        naomi_update
        break
    elif [ "$installerChoice" = "version" ] || [ "$installerChoice" = "VERSION" ] || [ "$installerChoice" = "Version" ]; then
        naomi_version
        break
    elif [ "$installerChoice" = "autoupdate" ] || [ "$installerChoice" = "AUTOUPDATE" ] || [ "$installerChoice" = "AutoUpdate" ] || [ "$installerChoice" = "Autoupdate" ] || [ "$installerChoice" = "autoUpdate" ]; then
        naomi_autoupdate
        break
    elif [ "$installerChoice" = "quit" ] || [ "$installerChoice" = "QUIT" ] || [ "$installerChoice" = "Quit" ]; then
        echo "EXITING"
        exit 1
    else
        printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
        echo
        printf "${B_Blue}Input: ${B_W}"
    fi
done
