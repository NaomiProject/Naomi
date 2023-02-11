#!/bin/bash

source "scripts/misc.sh"
source "scripts/pre_checks.sh"
#########################################
# Installs python and necessary packages
# for arch based Naomi. This script will install python
# into the ~/.config/naomi/local/bin directory and
# install naomi & requirements in their
# respective directories.
#########################################


setup_wizard() {
    wizardSetup

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

    env

  createDirs

  # Download and setup Naomi Dev repo as default
  #TODO: Remove Git since pre_check already handles it
    naomiChannel

  while true; do
    read -N1 -s key
    case $key in
    1)
      printf "${B_M}$key ${B_W}- Easy Peasy!${NL}"
      #BUG: Does CWD to home
      #cd ~
      if [ ! -f ~/Naomi/README.md ]; then
        printf "${B_G}Downloading 'Naomi'...${B_W}${NL}"
        mkdir -p ~/Naomi/naomiInstaller
        #git clone ~/Naomi/naomiInstaller
        #pwd
        cp -r ../../Naomi ~/Naomi/naomiInstaller
        cd ~/Naomi/naomiInstaller/Naomi
        #TODO: Copy local repo instead | Write a script that will install directly to ~
        #TODO: Git pull upstream from particular branch | maybe just merge from Upstream
<<comment
        cd ~
        git clone $gitURL.git -b master Naomi
        cd Naomi

        cd ~
comment
        #BUG: does not recognise folder as git
        pwd

        git checkout master
        git fetch origin
        git merge origin master
        #cp -r ../Naomi ~
        echo '{"use_release":"stable", "branch":"master", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' >~/.config/naomi/configs/.naomi_options.json
      else

        mv ~/Naomi ~/Naomi-Temp
<<comment
        cd ~
        git clone $gitURL.git -b master Naomi
        cd Naomi
        echo '{"use_release":"stable", "branch":"master", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' >~/.config/naomi/configs/.naomi_options.json
        cd ~
comment



        git checkout master
        git fetch origin
        git merge origin master
        cp -r ../Naomi ~
        echo '{"use_release":"stable", "branch":"master", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' >~/.config/naomi/configs/.naomi_options.json

      fi
      break
      ;;
    2)
      printf "${B_M}$key ${B_W}- Good Choice!${NL}"
      echo '{"use_release":"milestone", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' >~/.config/naomi/configs/.naomi_options.json
      cd ~
      if [ ! -f ~/Naomi/README.md ]; then
        printf "${B_G}Downloading 'Naomi'...${B_W}${NL}"
        #TODO: Replace & use git origin
        # cd ~


        git checkout naomi-dev
        git fetch origin
        git merge origin naomi-dev
        cp -r ../Naomi ~

        #git clone $gitURL.git -b naomi-dev Naomi
        cd ~/Naomi
        echo '{"use_release":"milestone", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' >~/.config/naomi/configs/.naomi_options.json
        # cd ~
      else
        mv ~/Naomi ~/Naomi-Temp
        #TODO: Replace & use git upstream


        git checkout naomi-dev
        git fetch origin
        git merge origin naomi-dev
        cp -r ../Naomi ~

        cd ~/Naomi
        #git clone $gitURL.git -b naomi-dev Naomi
        #cd Naomi
        echo '{"use_release":"milestone", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"false"}' >~/.config/naomi/configs/.naomi_options.json
        # cd ~
      fi
      break
      ;;
    3)
      printf "${B_M}$key ${B_W}- You know what you are doing!${NL}"
      # cd ~
      if [ ! -f ~/Naomi/README.md ]; then
        printf "${B_G}Downloading 'Naomi'...${B_W}${NL}"
        #TODO: Replace with git upstream


        git checkout naomi-dev
        git fetch origin
        git merge origin naomi-dev
        cp -r ../Naomi ~

        cd ~/Naomi

        #git clone $gitURL.git -b naomi-dev Naomi
        #cd Naomi
        echo '{"use_release":"nightly", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"true"}' >~/.config/naomi/configs/.naomi_options.json
        # cd ~
      else
        mv ~/Naomi ~/Naomi-Temp
        #TODO: Replace with git upstream


        git checkout naomi-dev
        git fetch origin
        git merge origin naomi-dev
        cp -r ../Naomi ~

        cd ~/Naomi

        #cd ~
        #git clone $gitURL.git -b naomi-dev Naomi
        #cd Naomi
        echo '{"use_release":"nightly", "branch":"naomi-dev", "version":"Naomi-'$version'.'$gitVersionNumber'", "date":"'$theDateRightNow'", "auto_update":"true"}' >~/.config/naomi/configs/.naomi_options.json
        cd ~
      fi
      break
      ;;
    S)
      printf "${B_M}$key ${B_W}- Skipping Section${NL}"
      echo '{"use_release":"testing", "version":"Naomi-Development", "version":"Development", "date":"'$theDateRightNow'", "auto_update":"false"}' >~/.config/naomi/configs/.naomi_options.json
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
    #FIXME: Replace APT with ARCH
  cd ~/Naomi
  APT=1
  if [ $APT -eq 1 ]; then
    if [ $REQUIRE_AUTH -eq 1 ]; then
      SUDO_COMMAND "sudo pacman -Syu"
      SUDO_COMMAND "sudo pacman -Syu $SUDO_APPROVE"
      #FIXME: Broke here & couldnt find file
      pwd
      SUDO_COMMAND "sudo bash naomi_requirements.sh $SUDO_APPROVE"
      if [ $? -ne 0 ]; then
        printf "${B_R}Notice:${B_W} Error installing pacman packages${NL}" >&2
        exit 1
      fi
    else
      printf "${B_W}${NL}"
      sudo pacman -Syu
      sudo pacman -Syu $SUDO_APPROVE
      pwd
      #FIXME: Still broke and couldnt find file
      sudo bash naomi_requirements.sh $SUDO_APPROVE
      if [ $? -ne 0 ]; then
        printf "${B_R}Notice:${B_W} Error installing arch packages${NL}" >&2
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

  #TODO: Write the backup script to install the servers
  if [ pulseaudio --version ]; then
    echo "Pulseaudio detected running pulseaudio setup..."
  elif [ pipewire --version ]; then
    echo "Pipewire detected running pipewire setup..."
  else
    echo "Pipewire or Puleaudio are not installed"
    echo "Installing Pipewire instead"
    #FIXME: Add user choice for Pipewire
    sudo pacman -S pipewire
  fi

  pip3 install --user virtualenv virtualenvwrapper=='4.8.4'
  printf "${B_G}sourcing virtualenvwrapper.sh${B_W}${NL}"
  export WORKON_HOME=$HOME/.virtualenvs
  export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
  export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv
  source ~/.local/bin/virtualenvwrapper.sh
  export VIRTUALENVWRAPPER_ENV_BIN_DIR=bin
  printf "${B_G}checking if Naomi virtualenv exists${B_W}${NL}"
  workon Naomi >/dev/null 2>&1
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
      echo '' >>~/.bashrc
      echo '' >>~/.bashrc
      echo '' >>~/.bashrc
      echo '######################################################################' >>~/.bashrc
      echo '# Initialize Naomi VirtualEnvWrapper' >>~/.bashrc
      echo '######################################################################' >>~/.bashrc
      echo "export WORKON_HOME=$HOME/.virtualenvs" >>~/.bashrc
      echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >>~/.bashrc
      echo "export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >>~/.bashrc
      echo "source ~/.local/bin/virtualenvwrapper.sh" >>~/.bashrc
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
  echo '' >>~/.bashrc
  echo '' >>~/.bashrc
  echo '' >>~/.bashrc
  echo '######################################################################' >>~/.bashrc
  echo '# Initialize Naomi to start on command' >>~/.bashrc
  echo '######################################################################' >>~/.bashrc
  echo 'source ~/.config/naomi/Naomi.sh' >>~/.bashrc
  echo
  echo
  echo '[Desktop Entry]' >~/Desktop/Naomi.desktop
  echo 'Name=Naomi' >>~/Desktop/Naomi.desktop
  echo 'Comment=Your privacy respecting digital assistant' >>~/Desktop/Naomi.desktop
  echo 'Icon=/home/pi/Naomi/Naomi.png' >>~/Desktop/Naomi.desktop
  echo 'Exec=Naomi' >>~/Desktop/Naomi.desktop
  echo 'Type=Application' >>~/Desktop/Naomi.desktop
  echo 'Encoding=UTF-8' >>~/Desktop/Naomi.desktop
  echo 'Terminal=True' >>~/Desktop/Naomi.desktop
  echo 'Categories=None;' >>~/Desktop/Naomi.desktop
  echo
  echo
  echo "#!/bin/bash" >~/.config/naomi/Naomi.sh
  echo "" >>~/.config/naomi/Naomi.sh
  echo "B_W='\033[1;97m' #Bright White  For standard text output" >>~/.config/naomi/Naomi.sh
  echo "B_R='\033[1;91m' #Bright Red    For alerts/errors" >>~/.config/naomi/Naomi.sh
  echo "B_Blue='\033[1;94m' #Bright Blue For prompt question" >>~/.config/naomi/Naomi.sh
  echo "B_M='\033[1;95m' #Bright Magenta For prompt choices" >>~/.config/naomi/Naomi.sh
  echo 'NL="' >>~/.config/naomi/Naomi.sh
  echo '"' >>~/.config/naomi/Naomi.sh
  echo 'version="3.0"' >>~/.config/naomi/Naomi.sh
  #TODO: Migrate and use current cloned DIR
  echo 'theDateRightNow=$(date +%m-%d-%Y-%H:%M:%S)' >>~/.config/naomi/Naomi.sh
  echo 'gitURL="https://github.com/naomiproject/naomi"' >>~/.config/naomi/Naomi.sh
  echo "" >>~/.config/naomi/Naomi.sh
  echo "function Naomi() {" >>~/.config/naomi/Naomi.sh
  echo "  if [ \"\$(jq '.auto_update' ~/.config/naomi/configs/.naomi_options.json)\" = '\"true\"' ]; then" >>~/.config/naomi/Naomi.sh
  echo '    printf "${B_W}=========================================================================${NL}"' >>~/.config/naomi/Naomi.sh
  echo '    printf "${B_W}Checking for Naomi Updates...${NL}"' >>~/.config/naomi/Naomi.sh
  echo "    cd ~/Naomi" >>~/.config/naomi/Naomi.sh
  echo "    git fetch -q " >>~/.config/naomi/Naomi.sh
  echo '    if [ "$(git rev-parse HEAD)" != "$(git rev-parse @{u})" ] ; then' >>~/.config/naomi/Naomi.sh
  echo '      printf "${B_W}Downloading & Installing Updates...${NL}"' >>~/.config/naomi/Naomi.sh
  echo "      git pull" >>~/.config/naomi/Naomi.sh
  #echo "      sudo apt-get -o Acquire::ForceIPv4=true update -y" >>~/.config/naomi/Naomi.sh
  #echo "      sudo apt -o upgrade -y" >>~/.config/naomi/Naomi.sh
  echo "      sudo ./naomi_requirements.sh" >>~/.config/naomi/Naomi.sh
  echo "    else" >>~/.config/naomi/Naomi.sh
  echo '      printf "${B_W}No Updates Found.${NL}"' >>~/.config/naomi/Naomi.sh
  echo "    fi" >>~/.config/naomi/Naomi.sh
  echo "  else" >>~/.config/naomi/Naomi.sh
  echo '    printf "${B_R}Notice: ${B_W}Naomi Auto Update Failed!${NL}"' >>~/.config/naomi/Naomi.sh
  echo '    printf "${B_R}Notice: ${B_W}Would you like to force update Naomi?${NL}"' >>~/.config/naomi/Naomi.sh
  echo '    printf "${B_Blue}Choice [${B_M}Y${B_Blue}/${B_M}N${B_Blue}]: ${B_W}"' >>~/.config/naomi/Naomi.sh
  echo '    while true; do' >>~/.config/naomi/Naomi.sh
  echo '      read -N1 -s key' >>~/.config/naomi/Naomi.sh
  echo '      case $key in' >>~/.config/naomi/Naomi.sh
  echo '        Y)' >>~/.config/naomi/Naomi.sh
  echo '          printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >>~/.config/naomi/Naomi.sh
  echo '          mv ~/Naomi ~/Naomi-Temp' >>~/.config/naomi/Naomi.sh
  echo '          cd ~' >>~/.config/naomi/Naomi.sh
  echo "          if [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"nightly\"' ]; then" >>~/.config/naomi/Naomi.sh
  echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >>~/.config/naomi/Naomi.sh
  echo '            mv ~/Naomi ~/Naomi-Temp' >>~/.config/naomi/Naomi.sh
  echo '            cd ~' >>~/.config/naomi/Naomi.sh
  echo "            git clone \$gitURL.git -b naomi-dev Naomi" >>~/.config/naomi/Naomi.sh
  echo '            cd Naomi' >>~/.config/naomi/Naomi.sh
  echo "            echo '{\"use_release\":\"nightly\", \"branch\":\"naomi-dev\", \"version\":\"Naomi-\$version.\$(git rev-parse --short HEAD)\", \"date\":\"\$theDateRightNow\", \"auto_update\":\"true\"}' > ~/.config/naomi/configs/.naomi_options.json" >>~/.config/naomi/Naomi.sh
  echo '            cd ~' >>~/.config/naomi/Naomi.sh
  echo '            break' >>~/.config/naomi/Naomi.sh
  echo "          elif [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"milestone\"' ]; then" >>~/.config/naomi/Naomi.sh
  echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >>~/.config/naomi/Naomi.sh
  echo '            mv ~/Naomi ~/Naomi-Temp' >>~/.config/naomi/Naomi.sh
  echo '            cd ~' >>~/.config/naomi/Naomi.sh
  echo "            git clone \$gitURL.git -b naomi-dev Naomi" >>~/.config/naomi/Naomi.sh
  echo '            cd Naomi' >>~/.config/naomi/Naomi.sh
  echo "            echo '{\"use_release\":\"milestone\", \"branch\":\"naomi-dev\", \"version\":\"Naomi-\$version.\$(git rev-parse --short HEAD)\", \"date\":\"\$theDateRightNow\", \"auto_update\":\"true\"}' > ~/.config/naomi/configs/.naomi_options.json" >>~/.config/naomi/Naomi.sh
  echo '            cd ~' >>~/.config/naomi/Naomi.sh
  echo '            break' >>~/.config/naomi/Naomi.sh
  echo "          elif [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"stable\"' ]; then" >>~/.config/naomi/Naomi.sh
  echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >>~/.config/naomi/Naomi.sh
  echo '            mv ~/Naomi ~/Naomi-Temp' >>~/.config/naomi/Naomi.sh
  echo '            cd ~' >>~/.config/naomi/Naomi.sh
  echo "            git clone \$gitURL.git -b master Naomi" >>~/.config/naomi/Naomi.sh
  echo '            cd Naomi' >>~/.config/naomi/Naomi.sh
  echo "            echo '{\"use_release\":\"stable\", \"branch\":\"master\", \"version\":\"Naomi-\$version.\$(git rev-parse --short HEAD)\", \"date\":\"\$theDateRightNow\", \"auto_update\":\"false\"}' > ~/.config/naomi/configs/.naomi_options.json" >>~/.config/naomi/Naomi.sh
  echo '            cd ~' >>~/.config/naomi/Naomi.sh
  echo '          fi' >>~/.config/naomi/Naomi.sh
  echo '          break' >>~/.config/naomi/Naomi.sh
  echo '          ;;' >>~/.config/naomi/Naomi.sh
  echo '         N)' >>~/.config/naomi/Naomi.sh
  echo '          printf "${B_M}$key ${B_W}- Launching Naomi!${NL}"' >>~/.config/naomi/Naomi.sh
  echo '          break' >>~/.config/naomi/Naomi.sh
  echo '          ;;' >>~/.config/naomi/Naomi.sh
  echo '       esac' >>~/.config/naomi/Naomi.sh
  echo '   done' >>~/.config/naomi/Naomi.sh
  echo "  fi" >>~/.config/naomi/Naomi.sh
  echo "  export WORKON_HOME=$HOME/.virtualenvs" >>~/.config/naomi/Naomi.sh
  echo "  export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >>~/.config/naomi/Naomi.sh
  echo "  export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >>~/.config/naomi/Naomi.sh
  echo "  source ~/.local/bin/virtualenvwrapper.sh" >>~/.config/naomi/Naomi.sh
  echo "  workon Naomi" >>~/.config/naomi/Naomi.sh
  echo "  python $NAOMI_DIR/Naomi.py \"\$@\"" >>~/.config/naomi/Naomi.sh
  echo "}" >>~/.config/naomi/Naomi.sh
  echo
  echo
  echo
  echo

  find ~/Naomi -maxdepth 1 -iname '*.py' -type f -exec chmod a+x {} \;
  find ~/Naomi -maxdepth 1 -iname '*.sh' -type f -exec chmod a+x {} \;
  find ~/.config/naomi -maxdepth 1 -iname '*.sh' -type f -exec chmod a+x {} \;
  find ~/Naomi/installers -maxdepth 1 -iname '*.sh' -type f -exec chmod a+x {} \;

  echo
  printf "${B_W}=========================================================================${NL}"
  printf "${B_W}PLUGIN SETUP${NL}"
  printf "${B_W}Now we'll tackle the default plugin options available for Text-to-Speech, Speech-to-Text, and more.${NL}"
  echo
  sleep 3
  echo

  # Build Phonetisaurus
  # Building and installing openfst
  echo
  printf "${B_G}Building and installing openfst...${B_W}${NL}"
  cd ~/.config/naomi/sources

  if [ ! -f "openfst-1.6.9.tar.gz" ]; then
    wget http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.6.9.tar.gz
  fi
  tar -zxvf openfst-1.6.9.tar.gz
  cd openfst-1.6.9
  autoreconf -i
  ./configure --enable-static --enable-shared --enable-far --enable-lookahead-fsts --enable-const-fsts --enable-pdt --enable-ngram-fsts --enable-linear-fsts --prefix=/usr
  make
  if [ $REQUIRE_AUTH -eq 1 ]; then
    SUDO_COMMAND "sudo make install"
    if [ $? -ne 0 ]; then
      echo $! >&2
      exit 1
    fi
  else
    printf "${B_W}${NL}"
    sudo make install
    if [ $? -ne 0 ]; then
      echo $! >&2
      exit 1
    fi
  fi

  if [ -z "$(which fstinfo)" ]; then
    printf "${ERROR} ${B_R}Notice:${B_W} openfst not installed${NL}" >&2
    exit 1
  fi

  # Building and installing mitlm-0.4.2
  echo
  printf "${B_G}Installing & Building mitlm-0.4.2...${B_W}${NL}"
  cd ~/.config/naomi/sources
  if [ ! -d "mitlm" ]; then
    git clone https://github.com/mitlm/mitlm.git
    if [ $? -ne 0 ]; then
      printf "${ERROR} ${B_R}Notice:${B_W} Error cloning mitlm${NL}"
      exit 1
    fi
  fi
  cd mitlm
  ./autogen.sh
  make
  printf "${B_G}Installing mitlm${B_W}${NL}"
  if [ $REQUIRE_AUTH -eq 1 ]; then
    SUDO_COMMAND "sudo make install"
    if [ $? -ne 0 ]; then
      echo $! >&2
      exit 1
    fi
  else
    printf "${B_W}${NL}"
    sudo make install
    if [ $? -ne 0 ]; then
      echo $! >&2
      exit 1
    fi
  fi

  # Building and installing CMUCLMTK
  echo
  printf "${B_G}Installing & Building cmuclmtk...${B_W}${NL}"
  cd ~/.config/naomi/sources
  svn co https://svn.code.sf.net/p/cmusphinx/code/trunk/cmuclmtk/
  if [ $? -ne 0 ]; then
    printf "${ERROR} ${B_R}Notice:${B_W} Error cloning cmuclmtk${NL}" >&2
    exit 1
  fi
  cd cmuclmtk
  ./autogen.sh
  make
  printf "${B_G}Installing CMUCLMTK${B_W}${NL}"
  if [ $REQUIRE_AUTH -eq 1 ]; then
    SUDO_COMMAND "sudo make install"
  else
    printf "${B_W}${NL}"
    sudo make install
  fi

  printf "${B_G}Linking shared libraries${B_W}${NL}"
  if [ $REQUIRE_AUTH -eq 1 ]; then
    SUDO_COMMAND "sudo ldconfig"
  else
    printf "${B_W}${NL}"
    sudo ldconfig
  fi

  # Building and installing phonetisaurus
  # Remove Phonetisaurus then installed
<<comment
  echo
  printf "${B_G}Installing & Building phonetisaurus...${B_W}${NL}"
  cd ~/.config/naomi/sources
  if [ ! -d "Phonetisaurus" ]; then
    git clone https://github.com/AdolfVonKleist/Phonetisaurus.git
    if [ $? -ne 0 ]; then
      printf "${ERROR} ${B_R}Notice:${B_W} Error cloning Phonetisaurus${NL}" >&2
      exit 1
    fi
  fi
  cd Phonetisaurus
  ./configure --enable-python
  make
  printf "${B_G}Installing Phonetisaurus${B_W}${NL}"
  printf "${B_G}Linking shared libraries${B_W}${NL}"
  if [ $REQUIRE_AUTH -eq 1 ]; then
    SUDO_COMMAND "sudo make install"
  else
    printf "${B_W}${NL}"
    sudo make install
  fi

  printf "[$(pwd)]\$ ${B_G}cd python${B_W}${NL}"
  cd python
  echo $(pwd)
  cp -v ../.libs/Phonetisaurus.so ./
  if [ $REQUIRE_AUTH -eq 1 ]; then
    SUDO_COMMAND "sudo python setup.py install"
  else
    printf "${B_W}${NL}"
    sudo python setup.py install
  fi

  if [ -z "$(which phonetisaurus-g2pfst)" ]; then
    printf "${ERROR} ${B_R}Notice:${B_W} phonetisaurus-g2pfst does not exist${NL}" >&2
    exit 1
  fi
comment
  # Installing & Building sphinxbase
  #TODO: Use pip3 package instead #pip3 install pocketsphinx
  #TODO: Chuck out block for pocketsphinx replace with pip3 (aaron said it didnt end well)
  #TODO: There is PocketSphinx in the Linux Repos.
<<comment
  echo
  printf "${B_G}Building and installing sphinxbase...${B_W}${NL}"
  cd ~/.config/naomi/sources
  if [ ! -d "pocketsphinx-python" ]; then
    git clone --recursive https://github.com/bambocher/pocketsphinx-python.git
    if [ $? -ne 0 ]; then
      printf "${ERROR} ${B_R}Notice:${B_W} Error cloning pocketsphinx${NL}" >&2
      exit 1
    fi
  fi
  cd pocketsphinx-python/deps/sphinxbase
  ./autogen.sh
  make
  if [ $REQUIRE_AUTH -eq 1 ]; then
    SUDO_COMMAND "sudo make install"
  else
    printf "${B_W}${NL}"
    sudo make install
  fi

  # Installing & Building pocketsphinx

  echo
  printf "${B_G}Building and installing pocketsphinx...${B_W}${NL}"
  cd ~/.config/naomi/sources/pocketsphinx-python/deps/pocketsphinx
  ./autogen.sh
  make
  if [ $REQUIRE_AUTH -eq 1 ]; then
    SUDO_COMMAND "sudo make install"
  else
    printf "${B_W}${NL}"
    sudo make install
  fi

  # Installing PocketSphinx Python module
  echo
  printf "${B_G}Installing PocketSphinx module...${B_W}${NL}"
  cd ~/.config/naomi/sources/pocketsphinx-python
  python setup.py install
comment

    #TODO: Check if PocketSphinx works for Python3
    #pip3 install pocketsphinx
  cd $NAOMI_DIR
  if [ -z "$(which text2wfreq)" ]; then
    printf "${ERROR} ${B_R}Notice:${B_W} text2wfreq does not exist${NL}" >&2
    exit 1
  fi
  if [ -z "$(which text2idngram)" ]; then
    printf "${ERROR} ${B_R}Notice:${B_W} text2idngram does not exist${NL}" >&2
    exit 1
  fi
  if [ -z "$(which idngram2lm)" ]; then
    printf "${ERROR} ${B_R}Notice:${B_W} idngram2lm does not exist${NL}" >&2
    exit 1
  fi

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
