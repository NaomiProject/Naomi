#!/bin/bash

#########################################
# Runs Commands For Naomi
#########################################

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
               gzip -r Naomi-Backup.$theDateRightNow.zip ~/.config/naomi_backup/
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
               return;
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
               elif [ -n "$(command -v pacman -Syu)" ]; then
                   arch_setup_wizard
               elif [ -n "$(command -v yum)" ]; then
                   unknown_os
               else
                   unknown_os
               fi
               return;
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
            return;
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
                return;
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
                return;
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
                return;
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
                return;
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
                return;
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
                return;
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
                return;
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
                return;
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
                return;
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
                return;
            elif [ "$autoupdateChoice" = "n" ] || [ "$autoupdateChoice" = "N" ]; then
                printf "${B_M}N ${B_W}- No Change${NL}"
                return;
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
                return;
            elif [ "$autoupdateChoice" = "n" ] || [ "$autoupdateChoice" = "N" ]; then
                printf "${B_M}N ${B_W}- No Change${NL}"
                return;
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
#TODO: Implement functoin before setup wizard
#installProcess

defaultFlavor() {
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
   return;
   
}

stableVersion() {
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
   return;
}

nightlyVersion(){
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
 return;
}

skipFlavor(){
  printf "${B_M}$key ${B_W}- Skipping Section${NL}"
  echo '{"use_release":"testing", "version":"Naomi-Development", "version":"Development", "date":"'$theDateRightNow'", "auto_update":"false"}' > ~/.config/naomi/configs/.naomi_options.json
  return;

}


setupVenv() {
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
}

processNaomi() {
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
 echo '          mv ~/Naomi ~/Naomi-Temp' >> ~/.config/naomi/Naomi.sh
 echo '          cd ~' >> ~/.config/naomi/Naomi.sh
 echo "          if [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"nightly\"' ]; then" >> ~/.config/naomi/Naomi.sh
 echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >> ~/.config/naomi/Naomi.sh
 echo '            mv ~/Naomi ~/Naomi-Temp' >> ~/.config/naomi/Naomi.sh
 echo '            cd ~' >> ~/.config/naomi/Naomi.sh
 echo "            git clone \$gitURL.git -b naomi-dev Naomi" >> ~/.config/naomi/Naomi.sh
 echo '            cd Naomi' >> ~/.config/naomi/Naomi.sh
 echo "            echo '{\"use_release\":\"nightly\", \"branch\":\"naomi-dev\", \"version\":\"Naomi-\$version.\$(git rev-parse --short HEAD)\", \"date\":\"\$theDateRightNow\", \"auto_update\":\"true\"}' > ~/.config/naomi/configs/.naomi_options.json" >> ~/.config/naomi/Naomi.sh
 echo '            cd ~' >> ~/.config/naomi/Naomi.sh
 echo '            break' >> ~/.config/naomi/Naomi.sh
 echo "          elif [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"milestone\"' ]; then" >> ~/.config/naomi/Naomi.sh
 echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >> ~/.config/naomi/Naomi.sh
 echo '            mv ~/Naomi ~/Naomi-Temp' >> ~/.config/naomi/Naomi.sh
 echo '            cd ~' >> ~/.config/naomi/Naomi.sh
 echo "            git clone \$gitURL.git -b naomi-dev Naomi" >> ~/.config/naomi/Naomi.sh
 echo '            cd Naomi' >> ~/.config/naomi/Naomi.sh
 echo "            echo '{\"use_release\":\"milestone\", \"branch\":\"naomi-dev\", \"version\":\"Naomi-\$version.\$(git rev-parse --short HEAD)\", \"date\":\"\$theDateRightNow\", \"auto_update\":\"true\"}' > ~/.config/naomi/configs/.naomi_options.json" >> ~/.config/naomi/Naomi.sh
 echo '            cd ~' >> ~/.config/naomi/Naomi.sh
 echo '            break' >> ~/.config/naomi/Naomi.sh
 echo "          elif [ \"\$(jq '.use_release' ~/.config/naomi/configs/.naomi_options.json)\" = '\"stable\"' ]; then" >> ~/.config/naomi/Naomi.sh
 echo '            printf "${B_M}$key ${B_W}- Forcing Update${NL}"' >> ~/.config/naomi/Naomi.sh
 echo '            mv ~/Naomi ~/Naomi-Temp' >> ~/.config/naomi/Naomi.sh
 echo '            cd ~' >> ~/.config/naomi/Naomi.sh
 echo "            git clone \$gitURL.git -b master Naomi" >> ~/.config/naomi/Naomi.sh
 echo '            cd Naomi' >> ~/.config/naomi/Naomi.sh
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
}

openfst() {
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
}

mitlm() {
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
}

cmuclmtk() {
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
}

phonetisaurus() {
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
}

sphinxbase() {
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
}

pocketsphinx(){
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
}

pocketsphinx_python(){
 echo
 printf "${B_G}Installing PocketSphinx module...${B_W}${NL}"
 cd ~/.config/naomi/sources/pocketsphinx-python
 python setup.py install

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
}

compileTranslations(){
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
