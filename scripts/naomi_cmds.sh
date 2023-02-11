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
