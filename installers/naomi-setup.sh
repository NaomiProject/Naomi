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
version="3.0"
theDateRightNow=$(date +%m-%d-%Y-%H:%M:%S)
gitVersionNumber=$(git rev-parse --short HEAD)
gitURL="https://github.com/naomiproject/naomi"

CONTINUE() {
    read -n1 -p "Press 'q' to quit, any other key to continue: " CONTINUE
    echo
    if [ "$CONTINUE" = "q" ] || [ "$CONTINUE" = "Q" ]; then
        echo "EXITING"
        exit 1
    fi
}
quit() {
    read -n1 -p "Press 'q' to quit, any other key to continue: " CONTINUE
    echo
    if [ "$CONTINUE" = "q" ] || [ "$CONTINUE" = "Q" ]; then
        echo "EXITING"
        exit 1
    else
        exec bash $0
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
unknown_os () {
  printf "${B_R}Notice:${B_W} Unfortunately, your operating system distribution and version are not supported by this script at this time.${NL}"
  echo
  printf "${B_R}Notice:${B_W} You can find a list of supported OSes and distributions on our website: ${B_Y}https://projectnaomi.com/dev/docs/installation/${NL}"
  echo
  printf "${B_R}Notice:${B_W} Please join our Discord or email us at ${B_Y}contact@projectnaomi.com${B_W} and let us know if you run into any issues.${NL}"
  exit 1
}
os_detect () {
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
      os_like=${ID_LIKE}
      if [ "${os}" = "poky" ]; then
        dist=`echo ${VERSION_ID}`
      elif [ "${os}" = "sles" ]; then
        dist=`echo ${VERSION_ID}`
      elif [ "${os}" = "opensuse" ]; then
        dist=`echo ${VERSION_ID}`
      elif [ "${os}" = "opensuse-leap" ]; then
        os=opensuse
        dist=`echo ${VERSION_ID}`
      elif [ "${os_like}" = "arch" ]; then
        os=arch
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

curl_check () {
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
    elif [ -n "$(command -v pacman -Syu)" ]; then
	  printf "${B_W}apt found${NL}"
      SUDO_COMMAND "sudo paru -S curl"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install curl! Your base system has a problem; please check your default OS's package repositories because curl should work.${NL}"
        printf "${B_R}Notice:${B_W} Curl installation aborted.${NL}"
        exit 1
      fi
    else
      printf "${B_R}Notice:${B_W} Neither yum | apt-get | pacman found${NL}"
      printf "${B_R}Notice:${B_W} Unable to install curl! Your base system has a problem; please check your default OS's package repositories because curl should work.${NL}"
      printf "${B_R}Notice:${B_W} Curl installation aborted.${NL}"
      exit 1
    fi
  fi
}

jq_check () {
  printf "${B_W}Checking for jq...${NL}"
  if command -v jq > /dev/null; then
    printf "${B_W}Detected jq...${NL}"
  else
    printf "${B_G}Installing jq...${NL}"
    if [ -n "$(command -v yum)" ]; then
	  printf "${B_W}yum found${NL}"
      SUDO_COMMAND "yum install -d0 -e0 -y jq"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install jq! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} jq installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v apt-get)" ]; then
	  printf "${B_W}apt found${NL}"
      SUDO_COMMAND "sudo apt-get install -q -y jq"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install jq! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} jq installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v pacman -Syu)" ]; then
	  printf "${B_W}pacman found${NL}"
      SUDO_COMMAND "sudo pacman -S jq"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install jq! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} jq installation aborted.${NL}"
        exit 1
      fi
    else
      printf "${B_R}Notice:${B_W} Neither yum | apt-get | pacman found${NL}"
      printf "${B_R}Notice:${B_W} Unable to install jq! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
      printf "${B_R}Notice:${B_W} jq installation aborted.${NL}"
      exit 1
    fi
  fi
}

python_check () {
  printf "${B_W}Checking for python3...${NL}"
  if command -v python3 > /dev/null; then
    printf "${B_W}Detected python3...${NL}"
  else
    printf "${B_G}Installing python3...${NL}"
    if [ -n "$(command -v yum)" ]; then
	  printf "${B_W}yum found${NL}"
      SUDO_COMMAND "yum install -d0 -e0 -y python3"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install python3! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} python3 installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v apt-get)" ]; then
	  printf "${B_W}apt found${NL}"
      SUDO_COMMAND "sudo apt-get install -q -y python3"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install python3! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} python3 installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v pacman -Syu)" ]; then
	  printf "${B_W}pacman found${NL}"
      SUDO_COMMAND "sudo pacman -S python3"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install python3! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} python3 installation aborted.${NL}"
        exit 1
      fi
    else
      printf "${B_R}Notice:${B_W} Neither yum | apt-get | pacman found${NL}"
      printf "${B_R}Notice:${B_W} Unable to install python3! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
      printf "${B_R}Notice:${B_W} python3 installation aborted.${NL}"
      exit 1
    fi
  fi
}

git_check () {
  printf "${B_W}Checking for git...${NL}"
  if command -v python3 > /dev/null; then
    printf "${B_W}Detected git...${NL}"
  else
    printf "${B_G}Installing git...${NL}"
    if [ -n "$(command -v yum)" ]; then
	  printf "${B_W}yum found${NL}"
      SUDO_COMMAND "yum install -d0 -e0 -y git"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install git! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} git installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v apt-get)" ]; then
	  printf "${B_W}apt found${NL}"
      SUDO_COMMAND "sudo apt-get install -q -y git"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install git! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} git installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v pacman -Syu)" ]; then
	  printf "${B_W}pacman found${NL}"
      SUDO_COMMAND "sudo pacman -S git"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install git! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} git installation aborted.${NL}"
        exit 1
      fi
    else
      printf "${B_R}Notice:${B_W} Neither yum | apt-get | pacman found${NL}"
      printf "${B_R}Notice:${B_W} Unable to install git! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
      printf "${B_R}Notice:${B_W} git installation aborted.${NL}"
      exit 1
    fi
  fi
}


apt_setup_wizard() {
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

arch_setup_wizard() {
  if [ ! -f ~/Naomi/README.md ]; then
    echo
    printf "${B_G}Starting Naomi Arch Setup Wizard...${NL}${B_W}"
    #. <( wget -O - "https://installers.projectnaomi.com/script.deb.sh" );
    # . <( wget -O - "./arch.pacman.sh" );
    #TODO: Check Why this is failing
    bash installers/arch.pacman.sh;

    # ./installers/arch.pacman.sh

    if [ -n "$(command bash installers/arch.pacman.sh)" ]; then
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

    wget_exit_code=$?
    elif [ "$wget_exit_code" = "0" ]; then
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
      printf "${B_R}Notice: ${B_W}Naomi Arch Setup Wizard Failed.${NL}"
      echo
      exit 1
    fi
  elif [ -f ~/Naomi/README.md ] && [ -f ~/Naomi/installers/arch.pacman.sh ]; then
    chmod a+x ~/Naomi/installers/arch.pacman.sh
    bash ~/Naomi/installers/arch.pacman.sh
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
      printf "${B_R}Notice: ${B_W}Naomi Arch Setup Wizard Failed.${NL}"
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
naomi_install() {
    printf "${B_W}=========================================================================${NL}"
    printf "${B_M}Install ${B_W}...${NL}"
    printf "${B_W}=========================================================================${NL}"
    echo
    if [ -d ~/.config/naomi ]; then
        printf "${B_W}It looks like you already have Naomi installed.${NL}"
        printf "${B_W}To start Naomi just type '${B_G}Naomi${B_W}' in any terminal.${NL}"
        echo
        printf "${B_W}Running the install process again will create a backup of Naomi${NL}"
        printf "${B_W}in the '${B_G}~/.config/naomi-backup${B_W}' directory and then create a fresh install.${NL}"
        printf "${B_W}Is this what you want?${NL}"
        echo
        while true; do
            printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
            read installChoice
            if [ "$installChoice" = "y" ] || [ "$installChoice" = "Y" ]; then
                printf "${B_M}Y ${B_W}- Creating Backup${NL}"
                theDateRightNow=$(date +%m-%d-%Y-%H:%M:%S)
                mkdir -p ~/.config/naomi_backup/
                mv ~/Naomi ~/.config/naomi_backup/Naomi-Source
                mv ~/.config/naomi ~/.config/naomi_backup/Naomi-SubDir
                cd ~/.config/naomi_backup/
                zip -r Naomi-Backup.$theDateRightNow.zip ~/.config/naomi_backup/
                sudo rm -Rf ~/.config/naomi_backup/Naomi-Source/
                sudo rm -Rf ~/.config/naomi_backup/Naomi-SubDir/
                printf "${B_M}Y ${B_W}- Installing Naomi${NL}"
                if [ -n "$(command -v apt-get)" ]; then
                    apt_setup_wizard
                elif [ -n "$(command -v pacman -Syu)" ]; then
                    arch_setup_wizard
                elif [ -n "$(command -v yum)" ]; then
                    unknown_os
                else
                    unknown_os
                fi
                break
            elif [ "$installChoice" = "n" ] || [ "$installChoice" = "N" ]; then
                printf "${B_M}N ${B_W}- Cancelling Install${NL}"
                sleep 5
                exec bash $0
            else
                printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
                echo
            fi
        done
    elif [ ! -d ~/.config/naomi ]; then
        printf "${B_W}This process can take up to 3 hours to complete.${NL}"
        printf "${B_W}Would you like to continue with the process now or wait for another time?${NL}"
        echo
        printf "${B_M}  Y${B_W})es, I'd like the proceed with the setup.${NL}"
        printf "${B_M}  N${B_W})ope, I will come back at another time.${NL}"
        echo
        while true; do
            printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
            read installChoice
            if [ "$installChoice" = "y" ] || [ "$installChoice" = "Y" ]; then
                printf "${B_M}Y ${B_W}- Installing Naomi${NL}"
                if [ -n "$(command -v apt-get)" ]; then
                    apt_setup_wizard
                elif [ -n"$(command -v pacman -Syu)" ]; then
                    arch_setup_wizard
                elif [ -n "$(command -v yum)" ]; then
                    unknown_os
                else
                    unknown_os
                fi
                break
            elif [ "$installChoice" = "n" ] || [ "$installChoice" = "N" ]; then
                printf "${B_M}N ${B_W}- Cancelling Install${NL}"
                sleep 5
                exec bash $0
            else
                printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
                echo
            fi
        done
    fi
}
naomi_uninstall() {
    printf "${B_W}=========================================================================${NL}"
    printf "${B_M}Uninstall ${B_W}...${NL}"
    printf "${B_W}=========================================================================${NL}"
    printf "${B_R}Notice:${B_W} You are about to uninstall Naomi, is that what you want?${NL}"
    echo
    while true; do
        printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
        read uninstallChoice
        if [ "$uninstallChoice" = "y" ] || [ "$uninstallChoice" = "Y" ]; then
            printf "${B_M}$key ${B_W}- Uninstalling Naomi${NL}"
            SUDO_COMMAND "sudo rm -Rf ~/Naomi"
            SUDO_COMMAND "sudo rm -Rf ~/.config/naomi"
            break
        elif [ "$uninstallChoice" = "n" ] || [ "$uninstallChoice" = "N" ]; then
            printf "${B_M}N ${B_W}- Cancelling Install${NL}"
            sleep 5
            exec bash $0
        else
            printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
            echo
        fi
    done
}
naomi_update() {
    printf "${B_W}=========================================================================${NL}"
    printf "${B_M}Update ${B_W}...${NL}"
    printf "${B_W}=========================================================================${NL}"
    printf "${B_R}Notice: ${B_W}You are about to manually update Naomi, is that what you want?${NL}"
    echo
    while true; do
        printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
        read updateChoice
        if [ "$updateChoice" = "y" ] || [ "$updateChoice" = "Y" ]; then
            if [ "$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)" = '"nightly"' ]; then
                printf "${B_M}$key ${B_W}- Forcing Update${NL}"
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b naomi-dev Naomi
                cd Naomi
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cd ~
                sudo rm -Rf ~/Naomi-Temp
                break
            elif [ "$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)" = '"milestone"' ]; then
                printf "${B_M}$key ${B_W}- Forcing Update${NL}"
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b naomi-dev Naomi
                cd Naomi
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cd ~
                sudo rm -Rf ~/Naomi-Temp
                break
            elif [ "$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)" = '"stable"' ]; then
                printf "${B_M}$key ${B_W}- Forcing Update${NL}"
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b master Naomi
                cd Naomi
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cd ~
                sudo rm -Rf ~/Naomi-Temp
                break
            else
                printf "${B_R}Notice:${B_W} Error finding your Naomi Options file...${NL}"
                echo
            fi
        elif [ "$updateChoice" = "n" ] || [ "$updateChoice" = "N" ]; then
            printf "${B_M}N ${B_W}- Cancelling Update${NL}"
            sleep 5
            exec bash $0
        else
            printf "${B_R}Notice:${B_W} Error finding your Naomi Options file...${NL}"
        fi
    done
    sleep 5
    exec bash $0
}
naomi_version() {
    printf "${B_W}=========================================================================${NL}"
    printf "${B_M}Version ${B_W}...${NL}"
    printf "${B_W}=========================================================================${NL}"
    echo
    if [ "$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)" = '"stable"' ]; then
        printf "${B_W}It looks like you are using '${B_G}Stable${B_W}',${NL}"
        printf "${B_W}would you like to change versions?${NL}"
        echo
        while true; do
            printf "${B_Blue}Choice [${B_M}Milestone${B_Blue} or ${B_M}Nightly${B_Blue} or ${B_M}Quit${B_Blue}]: ${B_W}"
            read versionChoice
            if [ "$versionChoice" = "Milestone" ] || [ "$versionChoice" = "MILESTONE" ] || [ "$versionChoice" = "milestone" ]; then
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b naomi-dev Naomi
                cd Naomi
                cat <<< $(jq '.use_release = "milestone"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                printf "${B_M}Milestone ${B_W}- Version Changed${NL}"
                sudo rm -Rf ~/Naomi-Temp
                break
            elif [ "$versionChoice" = "Nightly" ] || [ "$versionChoice" = "NIGHTLY" ] || [ "$versionChoice" = "nightly" ]; then
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b naomi-dev Naomi
                cd Naomi
                cat <<< $(jq '.use_release = "nightly"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.auto_update = "true"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                printf "${B_M}Nightly ${B_W}- Version Changed${NL}"
                sudo rm -Rf ~/Naomi-Temp
                break
            elif [ "$versionChoice" = "Quit" ] || [ "$versionChoice" = "QUIT" ] || [ "$versionChoice" = "quit" ]; then
                printf "${B_M}Quit ${B_W}- Cancelling Version Change${NL}"
                sleep 5
                exec bash $0
            else
                printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
                echo
            fi
        done
    elif [ "$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)" = '"milestone"' ]; then
        printf "${B_W}It looks like you are using '${B_G}Milestone${B_W}',${NL}"
        printf "${B_W}would you like to change versions?${NL}"
        echo
        while true; do
            printf "${B_Blue}Choice [${B_M}Stable${B_Blue} or ${B_M}Nightly${B_Blue} or ${B_M}Quit${B_Blue}]: ${B_W}"
            read versionChoice
            if [ "$versionChoice" = "Stable" ] || [ "$versionChoice" = "STABLE" ] || [ "$versionChoice" = "stable" ]; then
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b master Naomi
                cd Naomi
                cat <<< $(jq '.use_release = "stable"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                printf "${B_M}Stable ${B_W}- Version Changed${NL}"
                sudo rm -Rf ~/Naomi-Temp
                break
            elif [ "$versionChoice" = "Nightly" ] || [ "$versionChoice" = "NIGHTLY" ] || [ "$versionChoice" = "nightly" ]; then
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b naomi-dev Naomi
                cd Naomi
                cat <<< $(jq '.use_release = "nightly"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.auto_update = "true"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                printf "${B_M}Nightly ${B_W}- Version Changed${NL}"
                sudo rm -Rf ~/Naomi-Temp
                break
            elif [ "$versionChoice" = "Quit" ] || [ "$versionChoice" = "QUIT" ] || [ "$versionChoice" = "quit" ]; then
                printf "${B_M}Quit ${B_W}- Cancelling Version Change${NL}"
                sleep 5
                exec bash $0
            else
                printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
                echo
            fi
        done
    elif [ "$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)" = '"nightly"' ]; then
        printf "${B_W}It looks like you are using '${B_G}Nightly${B_W}',${NL}"
        printf "${B_W}would you like to change versions?${NL}"
        echo
        while true; do
            printf "${B_Blue}Choice [${B_M}Stable${B_Blue} or ${B_M}Milestone${B_Blue} or ${B_M}Quit${B_Blue}]: ${B_W}"
            read versionChoice
            if [ "$versionChoice" = "Stable" ] || [ "$versionChoice" = "STABLE" ] || [ "$versionChoice" = "stable" ]; then
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b master Naomi
                cd Naomi
                cat <<< $(jq '.use_release = "stable"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                printf "${B_M}Stable ${B_W}- Version Changed${NL}"
                sudo rm -Rf ~/Naomi-Temp
                break
            elif [ "$versionChoice" = "Milestone" ] || [ "$versionChoice" = "MILESTONE" ] || [ "$versionChoice" = "milestone" ]; then
                mv ~/Naomi ~/Naomi-Temp
                cd ~
                git clone $gitURL.git -b naomi-dev Naomi
                cd Naomi
                cat <<< $(jq '.use_release = "milestone"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.version = "Naomi-'$version'.'$gitVersionNumber'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                cat <<< $(jq '.date = "'$theDateRightNow'"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                printf "${B_M}Milestone ${B_W}- Version Changed${NL}"
                sudo rm -Rf ~/Naomi-Temp
                break
            elif [ "$versionChoice" = "Quit" ] || [ "$versionChoice" = "QUIT" ] || [ "$versionChoice" = "quit" ]; then
                printf "${B_M}Quit ${B_W}- Cancelling Version Change${NL}"
                sleep 5
                exec bash $0
            else
                printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
                echo
            fi
        done
    else
        printf "${B_R}Notice:${B_W} Error finding your Naomi Options file...${NL}"
    fi
    sleep 5
    exec bash $0
}
naomi_autoupdate() {
    printf "${B_W}=========================================================================${NL}"
    printf "${B_M}AutoUpdate ${B_W}...${NL}"
    printf "${B_W}=========================================================================${NL}"
    echo
    if [ "$(jq '.auto_update' ~/.config/naomi/configs/.naomi_options.json)" = '"true"' ]; then
        printf "${B_W}It looks like you have AutoUpdates '${B_G}Enabled${B_W}',${NL}"
        printf "${B_W}would you like to disabled AutoUpdates?${NL}"
        echo
        while true; do
            printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
            read autoupdateChoice
            if [ "$autoupdateChoice" = "y" ] || [ "$autoupdateChoice" = "Y" ]; then
                cat <<< $(jq '.auto_update = "false"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                printf "${B_M}Y ${B_W}- AutoUpdate Disabled${NL}"
                break
            elif [ "$autoupdateChoice" = "n" ] || [ "$autoupdateChoice" = "N" ]; then
                printf "${B_M}N ${B_W}- No Change${NL}"
                break
            else
                printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
                echo
            fi
        done
    elif [ "$(jq '.auto_update' ~/.config/naomi/configs/.naomi_options.json)" = '"false"' ]; then
        printf "${B_W}It looks like you have AutoUpdates '${B_G}Disabled${B_W}',${NL}"
        printf "${B_W}would you like to enable AutoUpdates?${NL}"
        echo
        while true; do
            printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
            read autoupdateChoice
            if [ "$autoupdateChoice" = "y" ] || [ "$autoupdateChoice" = "Y" ]; then
                cat <<< $(jq '.auto_update = "true"' ~/.config/naomi/configs/.naomi_options.json) > ~/.config/naomi/configs/.naomi_options.json
                printf "${B_M}Y ${B_W}- AutoUpdate Enabled${NL}"
                break
            elif [ "$autoupdateChoice" = "n" ] || [ "$autoupdateChoice" = "N" ]; then
                printf "${B_M}N ${B_W}- No Change${NL}"
                break
            else
                printf "${B_R}Notice:${B_W} Did not recognize input, try again...${NL}"
                echo
            fi
        done
    else
        printf "${B_R}Notice:${B_W} Error finding your Naomi Options file...${NL}"
    fi
    sleep 5
    exec bash $0
}

tput reset
os_detect
curl_check
jq_check
python_check
git_check
sleep 5
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

sleep 5

echo

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
