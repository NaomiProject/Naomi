#!/bin/bash

#########################################
# Does Pre-Checks to ensure requirements
# are met.
#########################################

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

zip_check () {
  printf "${B_W}Checking for zip...${NL}"
  if command -v python3 > /dev/null; then
    printf "${B_W}Detected zip...${NL}"
  else
    printf "${B_G}Installing zip...${NL}"
    if [ -n "$(command -v yum)" ]; then
	  printf "${B_W}yum found${NL}"
      SUDO_COMMAND "yum install -d0 -e0 -y zip"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install zip! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} git installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v apt-get)" ]; then
	  printf "${B_W}apt found${NL}"
      SUDO_COMMAND "sudo apt-get install -y zip"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install zip! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} git installation aborted.${NL}"
        exit 1
      fi
    elif [ -n "$(command -v pacman -Syu)" ]; then
	  printf "${B_W}pacman found${NL}"
      SUDO_COMMAND "sudo pacman -S zip"
      if [ "$?" -ne "0" ]; then
        printf "${B_R}Notice:${B_W} Unable to install zip! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
        printf "${B_R}Notice:${B_W} git installation aborted.${NL}"
        exit 1
      fi
    else
      printf "${B_R}Notice:${B_W} Neither yum | apt-get | pacman found${NL}"
      printf "${B_R}Notice:${B_W} Unable to install zip! Your base system has a problem; please check your default OS's package repositories because jq should work.${NL}"
      printf "${B_R}Notice:${B_W} git installation aborted.${NL}"
      exit 1
    fi
  fi
}

