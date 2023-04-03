#!/bin/bash

#########################################
# Installs python and necessary packages
# for deb based Naomi. This script will install python
# into the ~/.config/naomi/local/bin directory and
# install naomi & requirements in their
# respective directories.
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
REQUIRE_AUTH=""
version="3.0"
theDateRightNow=$(date +%m-%d-%Y-%H:%M:%S)
gitVersionNumber=$(git rev-parse --short HEAD)
gitURL="https://github.com/naomiproject/naomi"

CONTINUE() {
    printf "${B_W}If you want to allow the process to run uninterrupted type '${B_G}S${B_W}'${NL}"
    printf "${B_W}or press '${B_G}Q${B_W}' to quit, any other key to continue:${NL}"
    read -n1 -p "" CONTINUE
    echo
    if [ "$CONTINUE" = "q" ] || [ "$CONTINUE" = "Q" ]; then
        echo
        printf "${B_R}EXITING${B_W}${NL}"
        exit 1
    elif [ "$CONTINUE" = "S" ] || [ "$CONTINUE" = "s" ]; then
        REQUIRE_AUTH="0"
        SUDO_APPROVE="-y"
    fi
}
SUDO_COMMAND() {
    echo
    printf "${B_R}Notice:${B_W} this program is about to use sudo to run the following command:${NL}"
    printf "[$(pwd)]\$ ${B_G}${1}${B_W}${NL}"
    echo
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

setup_wizard() {
    echo
    printf "${B_W}=========================================================================${NL}"
    printf "${B_W}DEB SETUP WIZARD${NL}"
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

    echo
    printf "${B_W}=========================================================================${NL}"
    printf "${B_W}ENVIRONMENT SETUP:${NL}"
    printf "${B_W}Now setting up the file stuctures & requirements${NL}"
    echo
    sleep 3
    echo

    # Create basic folder structures
    echo
    printf "${B_G}Creating File Structure...${B_W}${NL}"
    mkdir -p ~/.config/naomi/
    mkdir -p ~/.config/naomi/configs/
    mkdir -p ~/.config/naomi/scripts/
    mkdir -p ~/.config/naomi/sources/

    # Download and setup Naomi Dev repo as default
    echo
    printf "${B_G}Installing 'git'...${B_W}${NL}"
    if [ $REQUIRE_AUTH -eq 1 ]; then
      SUDO_COMMAND "sudo apt-get install git $SUDO_APPROVE"
    else
      printf "${B_W}${NL}"
      sudo apt-get install git $SUDO_APPROVE
    fi
    echo

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
    while true; do
        read -N1 -s key
        case $key in
         1)
            printf "${B_M}$key ${B_W}- Easy Peasy!${NL}"
            cd ~
            if [ ! -f ~/Naomi/README.md ]; then
              printf "${B_G}Downloading 'Naomi'...${B_W}${NL}"
              cd ~
              git clone $gitURL.git -b master Naomi
              cd Naomi
              echo '{"use_release":"stable", "branch":"master", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' > ~/.config/naomi/configs/.naomi_options.json
              cd ~
            else
              mv ~/Naomi ~/Naomi-Temp
              cd ~
              git clone $gitURL.git -b master Naomi
              cd Naomi
              echo '{"use_release":"stable", "branch":"master", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' > ~/.config/naomi/configs/.naomi_options.json
              cd ~
            fi
            break
            ;;
         2)
            printf "${B_M}$key ${B_W}- Good Choice!${NL}"
            echo '{"use_release":"milestone", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' > ~/.config/naomi/configs/.naomi_options.json
            cd ~
            if [ ! -f ~/Naomi/README.md ]; then
              printf "${B_G}Downloading 'Naomi'...${B_W}${NL}"
              cd ~
              git clone $gitURL.git -b naomi-dev Naomi
              cd Naomi
              echo '{"use_release":"milestone", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' > ~/.config/naomi/configs/.naomi_options.json
              cd ~
            else
              mv ~/Naomi ~/Naomi-Temp
              cd ~
              git clone $gitURL.git -b naomi-dev Naomi
              cd Naomi
              echo '{"use_release":"milestone", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' > ~/.config/naomi/configs/.naomi_options.json
              cd ~
            fi
            break
            ;;
         3)
            printf "${B_M}$key ${B_W}- You know what you are doing!${NL}"
            cd ~
            if [ ! -f ~/Naomi/README.md ]; then
              printf "${B_G}Downloading 'Naomi'...${B_W}${NL}"
              cd ~
              git clone $gitURL.git -b naomi-dev Naomi
              cd Naomi
              echo '{"use_release":"nightly", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"true"}' > ~/.config/naomi/configs/.naomi_options.json
              cd ~
            else
              mv ~/Naomi ~/Naomi-Temp
              cd ~
              git clone $gitURL.git -b naomi-dev Naomi
              cd Naomi
              echo '{"use_release":"nightly", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"true"}' > ~/.config/naomi/configs/.naomi_options.json
              cd ~
            fi
            break
            ;;
         S)
            printf "${B_M}$key ${B_W}- Skipping Section${NL}"
            echo '{"use_release":"testing", "version":"Naomi-Development", "version":"Development", "date":"'$theDateRightNow'", "auto_update":"false"}' > ~/.config/naomi/configs/.naomi_options.json
            break
            ;;
        esac
    done
    echo
    echo

    find ~/Naomi -maxdepth 1 -iname '*.py' -type f -exec chmod a+x {} \;
    find ~/Naomi -maxdepth 1 -iname '*.sh' -type f -exec chmod a+x {} \;
    find ~/Naomi/installers -maxdepth 1 -iname '*.sh' -type f -exec chmod a+x {} \;

    NAOMI_DIR="$(cd ~/Naomi && pwd)"

    cd ~/Naomi
    APT=1
    if [ $APT -eq 1 ]; then
      if [ $REQUIRE_AUTH -eq 1 ]; then
        SUDO_COMMAND "sudo apt-get update"
        SUDO_COMMAND "sudo apt upgrade $SUDO_APPROVE"
        SUDO_COMMAND "sudo ./naomi_apt_requirements.sh $SUDO_APPROVE"
        if [ $? -ne 0 ]; then
          printf "${B_R}Notice:${B_W} Error installing apt packages${NL}" >&2
          exit 1
        fi
      else
        printf "${B_W}${NL}"
        sudo apt-get update
        sudo apt upgrade $SUDO_APPROVE
        sudo ./naomi_apt_requirements.sh $SUDO_APPROVE
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

    pip3 install --user virtualenv virtualenvwrapper=='4.8.4'
    printf "${B_G}sourcing virtualenvwrapper.sh${B_W}${NL}"
    export WORKON_HOME=$HOME/.virtualenvs
    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv
    source ~/.local/bin/virtualenvwrapper.sh
    export VIRTUALENVWRAPPER_ENV_BIN_DIR=bin
    printf "${B_G}checking if Naomi virtualenv exists${B_W}${NL}"
    workon Naomi > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        printf "${B_G}Naomi virtualenv does not exist. Creating.${B_W}${NL}"
        PATH=$PATH:~/.local/bin mkvirtualenv -p python3 Naomi
    fi
    workon Naomi
    if [ "$(which pip)" = "$HOME/.virtualenvs/Naomi/bin/pip" ]; then
        echo
        echo
        echo
        echo
        printf "${B_W}If you want, we can add the call to start virtualenvwrapper directly${NL}"
        printf "${B_W}to the end of your ${B_G}~/.bashrc${B_W} file, so if you want to use the same${NL}"
        printf "${B_W}python that Naomi does for debugging or installing additional${NL}"
        printf "${B_W}dependencies, all you have to type is '${B_G}workon Naomi${B_W}'${NL}"
        echo
        printf "${B_W}Otherwise, you will need to enter:${NL}"
        printf "${B_W}'${B_G}VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv${B_W}'${NL}"
        printf "${B_W}'${B_G}source ~/.local/bin/virtualenvwrapper.sh${B_W}'${NL}"
        printf "${B_W}before you will be able activate the Naomi environment with '${B_G}workon Naomi${B_W}'${NL}"
        echo
        printf "${B_W}All of this will be incorporated into the Naomi script, so to simply${NL}"
        printf "${B_W}launch Naomi, all you have to type is '${B_G}Naomi${B_W}' in a terminal regardless of your choice here.${NL}"
        echo 
        printf "${B_W}Would you like to start VirtualEnvWrapper automatically?${NL}"
        echo
        printf "${B_M}  Y${B_W})es, start virtualenvwrapper whenever I start a shell${NL}"
        printf "${B_M}  N${B_W})o, don't start virtualenvwrapper for me${NL}"
        printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"
        export AUTO_START=""
        if [ "$SUDO_APPROVE" = "-y" ]; then
            AUTO_START="Y"
        else
            while [ "$AUTO_START" != "Y" ] && [ "$AUTO_START" != "y" ] && [ "$AUTO_START" != "N" ] && [ "$AUTO_START" != "n" ]; do
                read -e -p 'Please select: ' AUTO_START
                if [ "$AUTO_START" = "" ]; then
                    AUTO_START="Y"
                fi
                if [ "$AUTO_START" != "Y" ] && [ "$AUTO_START" != "y" ] && [ "$AUTO_START" != "N" ] && [ "$AUTO_START" != "n" ]; then
                    printf "${B_R}Notice:${B_W} Please choose 'Y' or 'N'"
                fi
            done
        fi
        if [ "$AUTO_START" = "Y" ] || [ "$AUTO_START" = "y" ]; then
            printf "${B_W}${NL}"
            echo '' >> ~/.bashrc
            echo '' >> ~/.bashrc
            echo '' >> ~/.bashrc
            echo '######################################################################' >> ~/.bashrc
            echo '# Initialize Naomi VirtualEnvWrapper' >> ~/.bashrc
            echo '######################################################################' >> ~/.bashrc
            echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc
            echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.bashrc
            echo "export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >> ~/.bashrc
            echo "source ~/.local/bin/virtualenvwrapper.sh" >> ~/.bashrc
        fi
        pip install -r python_requirements.txt
        if [ $? -ne 0 ]; then
            printf "${B_R}Notice:${B_W} Error installing python requirements: ${NL}${NL}$!" >&2
            exit 1
        fi
    else
        printf "${B_R}Notice:${B_W} Something went wrong, not in virtual environment...${NL}" >&2
        exit 1
    fi
    # start the naomi setup process
    printf "${B_W}${NL}"
    echo
    echo
    echo '' >> ~/.bashrc
    echo '' >> ~/.bashrc
    echo '' >> ~/.bashrc
    echo '######################################################################' >> ~/.bashrc
    echo '# Initialize Naomi to start on command' >> ~/.bashrc
    echo '######################################################################' >> ~/.bashrc
    echo 'source ~/.config/naomi/Naomi.sh' >> ~/.bashrc
    echo
    echo
    echo '[Desktop Entry]' > ~/Desktop/Naomi.desktop
    echo 'Name=Naomi' >> ~/Desktop/Naomi.desktop
    echo 'Comment=Your privacy respecting digital assistant' >> ~/Desktop/Naomi.desktop
    echo 'Icon=/home/pi/Naomi/Naomi.png' >> ~/Desktop/Naomi.desktop
    echo 'Exec=Naomi' >> ~/Desktop/Naomi.desktop
    echo 'Type=Application' >> ~/Desktop/Naomi.desktop
    echo 'Encoding=UTF-8' >> ~/Desktop/Naomi.desktop
    echo 'Terminal=True' >> ~/Desktop/Naomi.desktop
    echo 'Categories=None;' >> ~/Desktop/Naomi.desktop
    echo
    echo
    echo "#!/bin/bash" > ~/.config/naomi/Naomi.sh
    echo "" >> ~/.config/naomi/Naomi.sh
    echo "B_W='\033[1;97m' #Bright White  For standard text output" >> ~/.config/naomi/Naomi.sh
    echo "B_R='\033[1;91m' #Bright Red    For alerts/errors" >> ~/.config/naomi/Naomi.sh
    echo "B_Blue='\033[1;94m' #Bright Blue For prompt question" >> ~/.config/naomi/Naomi.sh
    echo "B_M='\033[1;95m' #Bright Magenta For prompt choices" >> ~/.config/naomi/Naomi.sh
    echo 'NL="' >> ~/.config/naomi/Naomi.sh
    echo '"' >> ~/.config/naomi/Naomi.sh
    echo 'version="3.0"' >> ~/.config/naomi/Naomi.sh
    echo 'theDateRightNow=$(date +%m-%d-%Y-%H:%M:%S)' >> ~/.config/naomi/Naomi.sh
    echo 'gitURL="https://github.com/naomiproject/naomi"' >> ~/.config/naomi/Naomi.sh
    echo "" >> ~/.config/naomi/Naomi.sh
    echo "function Naomi() {" >> ~/.config/naomi/Naomi.sh
    echo "  if [ \"\$(jq '.auto_update' ~/.config/naomi/configs/.naomi_options.json)\" = '\"true\"' ]; then" >> ~/.config/naomi/Naomi.sh
    echo '    printf "${B_W}=========================================================================${NL}"' >> ~/.config/naomi/Naomi.sh
    echo '    printf "${B_W}Checking for Naomi Updates...${NL}"' >> ~/.config/naomi/Naomi.sh
    echo "    cd ~/Naomi" >> ~/.config/naomi/Naomi.sh
    echo "    git fetch -q " >> ~/.config/naomi/Naomi.sh
    echo '    if [ "$(git rev-parse HEAD)" != "$(git rev-parse @{u})" ] ; then' >> ~/.config/naomi/Naomi.sh
    echo '      printf "${B_W}Downloading & Installing Updates...${NL}"' >> ~/.config/naomi/Naomi.sh
    echo "      git pull" >> ~/.config/naomi/Naomi.sh
    echo "      sudo apt-get -o Acquire::ForceIPv4=true update -y" >> ~/.config/naomi/Naomi.sh
    echo "      sudo apt -o upgrade -y" >> ~/.config/naomi/Naomi.sh
    echo "      sudo ./naomi_apt_requirements.sh -y" >> ~/.config/naomi/Naomi.sh
    echo "    else" >> ~/.config/naomi/Naomi.sh
    echo '      printf "${B_W}No Updates Found.${NL}"' >> ~/.config/naomi/Naomi.sh
    echo "    fi" >> ~/.config/naomi/Naomi.sh
    echo "  else" >> ~/.config/naomi/Naomi.sh
    echo '    printf "${B_R}Notice: ${B_W}Naomi Auto Update Failed!${NL}"' >> ~/.config/naomi/Naomi.sh
    echo '    printf "${B_R}Notice: ${B_W}Would you like to force update Naomi?${NL}"' >> ~/.config/naomi/Naomi.sh
    echo '    printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"' >> ~/.config/naomi/Naomi.sh
    echo '    while true; do' >> ~/.config/naomi/Naomi.sh
    echo '      read -N1 -s key' >> ~/.config/naomi/Naomi.sh
    echo '      case $key in' >> ~/.config/naomi/Naomi.sh
    echo '        Y)' >> ~/.config/naomi/Naomi.sh
    echo '          printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >> ~/.config/naomi/Naomi.sh
    echo "          if [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"nightly\"' ]; then" >> ~/.config/naomi/Naomi.sh
    echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >> ~/.config/naomi/Naomi.sh
    echo '            cd ~' >> ~/.config/naomi/Naomi.sh
    echo '            mv ~/Naomi ~/Naomi-Temp' >> ~/.config/naomi/Naomi.sh
    echo "            git clone \$gitURL.git -b naomi-dev Naomi" >> ~/.config/naomi/Naomi.sh
    echo "            echo '{\"use_release\":\"nightly\", \"branch\":\"naomi-dev\", \"version\":\"Naomi-\$version.\$(git rev-parse --short HEAD)\", \"date\":\"\$theDateRightNow\", \"auto_update\":\"true\"}' > ~/.config/naomi/configs/.naomi_options.json" >> ~/.config/naomi/Naomi.sh
    echo '            break' >> ~/.config/naomi/Naomi.sh
    echo "          elif [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"milestone\"' ]; then" >> ~/.config/naomi/Naomi.sh
    echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >> ~/.config/naomi/Naomi.sh
    echo '            cd ~' >> ~/.config/naomi/Naomi.sh
    echo '            mv ~/Naomi ~/Naomi-Temp' >> ~/.config/naomi/Naomi.sh
    echo "            git clone \$gitURL.git -b naomi-dev Naomi" >> ~/.config/naomi/Naomi.sh
    echo "            echo '{\"use_release\":\"milestone\", \"branch\":\"naomi-dev\", \"version\":\"Naomi-\$version.\$(git rev-parse --short HEAD)\", \"date\":\"\$theDateRightNow\", \"auto_update\":\"true\"}' > ~/.config/naomi/configs/.naomi_options.json" >> ~/.config/naomi/Naomi.sh
    echo '            break' >> ~/.config/naomi/Naomi.sh
    echo "          elif [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"stable\"' ]; then" >> ~/.config/naomi/Naomi.sh
    echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >> ~/.config/naomi/Naomi.sh
    echo '            cd ~' >> ~/.config/naomi/Naomi.sh
    echo '            mv ~/Naomi ~/Naomi-Temp' >> ~/.config/naomi/Naomi.sh
    echo "            git clone \$gitURL.git -b master Naomi" >> ~/.config/naomi/Naomi.sh
    echo "            echo '{\"use_release\":\"stable\", \"branch\":\"master\", \"version\":\"Naomi-\$version.\$(git rev-parse --short HEAD)\", \"date\":\"\$theDateRightNow\", \"auto_update\":\"false\"}' > ~/.config/naomi/configs/.naomi_options.json" >> ~/.config/naomi/Naomi.sh
    echo '            cd ~' >> ~/.config/naomi/Naomi.sh
    echo '          fi' >> ~/.config/naomi/Naomi.sh
    echo '          break' >> ~/.config/naomi/Naomi.sh
    echo '          ;;' >> ~/.config/naomi/Naomi.sh
    echo '         N)' >> ~/.config/naomi/Naomi.sh
    echo '          printf "${B_M}$key ${B_W}- Launching Naomi!${NL}"' >> ~/.config/naomi/Naomi.sh
    echo '          break' >> ~/.config/naomi/Naomi.sh
    echo '          ;;' >> ~/.config/naomi/Naomi.sh
    echo '       esac' >> ~/.config/naomi/Naomi.sh
    echo '   done' >> ~/.config/naomi/Naomi.sh
    echo "  fi" >> ~/.config/naomi/Naomi.sh
    echo "  export WORKON_HOME=$HOME/.virtualenvs" >> ~/.config/naomi/Naomi.sh
    echo "  export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.config/naomi/Naomi.sh
    echo "  export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >> ~/.config/naomi/Naomi.sh
    echo "  source ~/.local/bin/virtualenvwrapper.sh" >> ~/.config/naomi/Naomi.sh
    echo "  workon Naomi" >> ~/.config/naomi/Naomi.sh
    echo "  python $NAOMI_DIR/Naomi.py \"\$@\"" >> ~/.config/naomi/Naomi.sh
    echo "}" >> ~/.config/naomi/Naomi.sh
    echo
    echo
    echo
    echo

    find ~/Naomi -maxdepth 1 -iname '*.py' -type f -exec chmod a+x {} \;
    find ~/Naomi -maxdepth 1 -iname '*.sh' -type f -exec chmod a+x {} \;
    find ~/.config/naomi -maxdepth 1 -iname '*.sh' -type f -exec chmod a+x {} \;
    find ~/Naomi/installers -maxdepth 1 -iname '*.sh' -type f -exec chmod a+x {} \;

    # Compiling Translations
    echo
    printf "${B_G}Compiling Translations...${B_W}${NL}"
    cd ~/Naomi
    chmod a+x compile_translations.sh
    ./compile_translations.sh
    cd ~
    echo
    echo
    echo
    echo
}

setup_wizard
