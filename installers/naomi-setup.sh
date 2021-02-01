#!/bin/bash

#########################################
# Determines the OS & Version to direct
# Naomi build process correctly.
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

CONTINUE() {
    read -n1 -p "Press 'q' to quit, any other key to continue: " CONTINUE
    echo
    if [ "$CONTINUE" = "q" ] || [ "$CONTINUE" = "Q" ]; then
        echo "EXITING"
        exit 1
    fi
}
SUDO_COMMAND() {
    echo
    printf "${B_R}Notice:${B_W} this program is about to use sudo to run the following command:${NL}"
    printf "[$(pwd)]\$ ${B_G}${1}${B_W}${NL}"
    if [ "$SUDO_APPROVE" != "-y" ]; then
        CONTINUE
    fi
    $1
}
CHECK_HEADER() {
    echo "#include <$1>" | cpp $(pkg-config alsa --cflags) -H -o /dev/null > /dev/null 2>&1
    echo $?
}
CHECK_PROGRAM() {
    type -p "$1" > /dev/null 2>&1
    echo $?
}

unknown_os ()
{
  printf "${B_R}Notice:${B_W} Unfortunately, your operating system distribution and version are not supported by this script at this time.${NL}"
  echo
  printf "${B_R}Notice:${B_W} You can find a list of supported OSes and distributions on our website: ${B_Y}https://projectnaomi.com/dev/docs/installation/${NL}"
  echo
  printf "${B_R}Notice:${B_W} Please join our Discord or email us at ${B_Y}contact@projectnaomi.com${B_W} and let us know if you run into any issues.${NL}"
  exit 1
}

os_detect ()
{
  if [[ ( -z "${os}" ) && ( -z "${dist}" ) ]]; then
    # some systems dont have lsb-release yet have the lsb_release binary and
    # vice-versa
    if [ -e /etc/lsb-release ]; then
      . /etc/lsb-release

      if [ "${ID}" = "raspbian" ]; then
        os=${ID}
        dist=`cut --delimiter='.' -f1 /etc/debian_version`
      else
        os=${DISTRIB_ID}
        dist=${DISTRIB_CODENAME}

        if [ -z "$dist" ]; then
          dist=${DISTRIB_RELEASE}
        fi
      fi

    elif [ `which lsb_release 2>/dev/null` ]; then
      dist=`lsb_release -c | cut -f2`
      os=`lsb_release -i | cut -f2 | awk '{ print tolower($1) }'`

    elif [ -e /etc/debian_version ]; then
      # some Debians have jessie/sid in their /etc/debian_version
      # while others have '6.0.7'
      os=`cat /etc/issue | head -1 | awk '{ print tolower($1) }'`
      if grep -q '/' /etc/debian_version; then
        dist=`cut --delimiter='/' -f1 /etc/debian_version`
      else
        dist=`cut --delimiter='.' -f1 /etc/debian_version`
      fi

    elif [ -e /etc/os-release ]; then
      . /etc/os-release
      os=${ID}
      if [ "${os}" = "poky" ]; then
        dist=`echo ${VERSION_ID}`
      elif [ "${os}" = "sles" ]; then
        dist=`echo ${VERSION_ID}`
      elif [ "${os}" = "opensuse" ]; then
        dist=`echo ${VERSION_ID}`
      elif [ "${os}" = "opensuse-leap" ]; then
        os=opensuse
        dist=`echo ${VERSION_ID}`
      else
        dist=`echo ${VERSION_ID} | awk -F '.' '{ print $1 }'`
      fi

      elif [ `which lsb_release 2>/dev/null` ]; then
        # get major version (e.g. '5' or '6')
        dist=`lsb_release -r | cut -f2 | awk -F '.' '{ print $1 }'`

        # get os (e.g. 'centos', 'redhatenterpriseserver', etc)
        os=`lsb_release -i | cut -f2 | awk '{ print tolower($1) }'`

      elif [ -e /etc/oracle-release ]; then
        dist=`cut -f5 --delimiter=' ' /etc/oracle-release | awk -F '.' '{ print $1 }'`
        os='ol'

      elif [ -e /etc/fedora-release ]; then
        dist=`cut -f3 --delimiter=' ' /etc/fedora-release`
        os='fedora'

      elif [ -e /etc/redhat-release ]; then
        os_hint=`cat /etc/redhat-release  | awk '{ print tolower($1) }'`
        if [ "${os_hint}" = "centos" ]; then
          dist=`cat /etc/redhat-release | awk '{ print $3 }' | awk -F '.' '{ print $1 }'`
          os='centos'
        elif [ "${os_hint}" = "scientific" ]; then
          dist=`cat /etc/redhat-release | awk '{ print $4 }' | awk -F '.' '{ print $1 }'`
          os='scientific'
        else
          dist=`cat /etc/redhat-release  | awk '{ print tolower($7) }' | cut -f1 --delimiter='.'`
          os='redhatenterpriseserver'
        fi

    else
      unknown_os
    fi
  fi

  if [[ ( -z "${os}" ) || ( -z "${dist}" ) ]]; then
    unknown_os
  fi

  # remove whitespace from OS and dist name
  os="${os// /}"
  dist="${dist// /}"

  printf "${B_W}Detected operating system as $os/$dist.${NL}"
}

curl_check ()
{
  printf "${B_W}Checking for curl...${NL}"
  if command -v curl > /dev/null; then
    printf "${B_W}Detected curl...${NL}"
  else
    printf "${B_G}Installing curl...${NL}"
    if [ -n "$(command -v yum)" ]; then
	  printf "${B_W}yum found${NL}"
      SUDO_COMMAND "yum install -d0 -e0 -y curl"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install curl! Your base system has a problem; please check your default OS's package repositories because curl should work.${NL}"
        printf "${B_R}Notice:${B_W} Curl installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v apt-get)" ]; then
	  printf "${B_W}apt found${NL}"
      SUDO_COMMAND "sudo apt-get install -q -y curl"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install curl! Your base system has a problem; please check your default OS's package repositories because curl should work.${NL}"
        printf "${B_R}Notice:${B_W} Curl installation aborted.${NL}"
        exit 1
      fi
    else
      printf "${B_R}Notice:${B_W} Neither yum nor apt-get found${NL}"
      printf "${B_R}Notice:${B_W} Unable to install curl! Your base system has a problem; please check your default OS's package repositories because curl should work.${NL}"
      printf "${B_R}Notice:${B_W} Curl installation aborted.${NL}"
      exit 1
    fi
  fi
}

function apt_setup_wizard() {
  if [ ! -f ~/Naomi/README.md ]; then
    echo
    printf "${B_G}Starting Naomi Apt Setup Wizard...${NL}${B_W}"
    . <( wget -O - "https://installers.projectnaomi.com/script.deb.sh" );
    wget_exit_code=$?
    if [ "$wget_exit_code" = "0" ]; then
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
    else
      echo
      printf "${B_R}Notice: ${B_W}Naomi Apt Setup Wizard Failed.${NL}"
      echo
      exit 1
    fi
  else
    printf "${B_W}=========================================================================${NL}"
    printf "${B_W}It looks like you have Naomi source in the ${B_G}~/Naomi${B_W} directory,${NL}"
    printf "${B_W}however it looks to be out of date. Please update or remove the Naomi${NL}"
    printf "${B_W}source and try running the installer again.${NL}"
    echo
    printf "${B_W}Please join our Discord or email us at ${B_Y}contact@projectnaomi.com${B_W} and let us know if you run into any issues.${NL}"
    exit 1
  fi
}
function yum_setup_wizard() {
  if [ ! -f ~/Naomi/README.md ]; then
    echo
    echo
    echo
    echo
    printf "${B_G}Starting Naomi Yum Setup Wizard...${NL}${B_W}"
    . <( wget -O - "https://installers.projectnaomi.com/script.rpm.sh" );
    wget_exit_code=$?
    if [ "$wget_exit_code" = "0" ]; then
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
    else
      echo
      printf "${B_R}Notice: ${B_W}Naomi Yum Setup Wizard Failed.${NL}"
      echo
      exit 1
    fi
  else
    printf "${B_W}=========================================================================${NL}"
    printf "${B_W}It looks like you have Naomi source in the ${B_G}~/Naomi${B_W} directory,${NL}"
    printf "${B_W}however it looks to be out of date. Please update or remove the Naomi${NL}"
    printf "${B_W}source and try running the installer again.${NL}"
    echo
    printf "${B_W}Please join our Discord or email us at ${B_Y}contact@projectnaomi.com${B_W} and let us know if you run into any issues.${NL}"
    exit 1
  fi
}

tput reset
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

echo
os_detect
curl_check

if [ "$1" == "uninstall" ]; then
	printf "${B_W}=========================================================================${NL}"
  printf "${B_R}Notice:${B_W} You are about to uninstall Naomi, is that what you want?${NL}"
  printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
    while true; do
        read -N1 -s key
        case $key in
         [Y])
            printf "${B_M}$key ${B_W}- Uninstalling Naomi${NL}"
            sudo rm -Rf ~/Naomi
            sudo rm -Rf ~/.config/naomi
            break
            ;;
         [N])
            printf "${B_M}$key ${B_W}- Cancelling Uninstall${NL}"
            break
            ;;
        esac
    done
elif [ ! -d ~/.config/naomi ]; then
  echo
  echo
  echo
  echo
  printf "${B_W}=========================================================================${NL}"
  printf "${B_W}Welcome to Naomi. This process is designed to make getting started with${NL}"
  printf "${B_W}Naomi quick and easy. This process can take up to 3 hours to complete.${NL}"
  printf "${B_W}Would you like to continue with the process now or wait for another time?${NL}"
  echo
  printf "${B_M}  Y${B_W})es, I'd like the proceed with the setup.${NL}"
  printf "${B_M}  N${B_W})ope, I will come back at another time.${NL}"
  echo
  printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
  while true; do
    read -N1 -s key
    case $key in
      [Nn])
        printf "${B_M}$key ${B_W}- Nope${NL}"
        echo
        printf "${B_W}Alright, Good luck & have fun!${NL}"
        echo
        break
        break
        ;;
      [Yy])
        printf "${B_M}$key ${B_W}- Yes${NL}"
        echo
        if [ -n "$(command -v apt-get)" ]; then
          apt_setup_wizard
        elif [ -n "$(command -v yum)" ]; then
          unknown_os
        else
          unknown_os
        fi
        break
        ;;
    esac
  done
elif [ -d ~/.config/naomi ]; then
  printf "${B_W}=========================================================================${NL}"
  printf "${B_W}It looks like you already have Naomi installed.${NL}"
  printf "${B_W}To start Naomi just type '${B_G}Naomi${B_W}' in any terminal.${NL}"
  echo
  printf "${B_W}Note: If you are getting this message but have not ran the${NL}"
  printf "${B_W}setup before or if you have installed Naomi in the past, please${NL}"
  printf "${B_W}run ${B_G}naomi-setup.sh -uninstall${B_W} and rerun the installer.${NL}"
fi