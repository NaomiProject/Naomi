#!/bin/bash

#########################################
# Installing python and necessary packages
# for Naomi. This script will install python
# into the ~/.naomi/local/bin directory and
# install naomi & requirements in their
# respective directories.
#########################################
NL="
"
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
LT_GRAY='\033[0;37m'
DK_GRAY='\033[1;30m'
LT_RED='\033[1;31m'
LT_GREEN='\033[1;32m'
YELLOW='\033[1;33m'
LT_BLUE='\033[1;34m'
LT_PURPLE='\033[1;35m'
LT_CYAN='\033[1;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
OPTION="0"

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
    printf "${RED}Notice:${NC} this program is about to use sudo to run the following command:${NL}"
    printf "  ${GREEN}${1}${NC}${NL}"
    CONTINUE
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

function network_setup() {
    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "NETWORK SETUP:"
    echo
    sleep 3

    # silent check at first
    if ping -q -c 1 -W 1 1.1.1.1 >/dev/null 2>&1 ; then
        return 0
    fi

    # Wait for an internet connection -- either the user finished Wifi Setup or
    # plugged in a network cable.
    show_prompt=1
    should_reboot=255
    reset_wlan0=0
    while ! ping -q -c 1 -W 1 1.1.1.1 >/dev/null 2>&1 ; do
        if [ $show_prompt = 1 ]
        then
            echo -e "\e[1;36m"
            echo "Network connection not found, select an option to"
            echo "setup via keyboard or plug in a network cable:"
            echo "  1) Basic wifi with SSID and password"
            echo "  2) Wifi with no password"
            echo "  3) Edit wpa_supplicant.conf directly"
            echo "  4) Force reboot"
            echo -n -e "\e[1;36mChoice [\e[1;35m1\e[1;36m-\e[1;35m4\e[1;36m]: \e[0m"
            show_prompt=0
        fi

        read -N1 -s -t 1 pressed

        case $pressed in
         1)
            echo
            echo -n -e "\e[1;36mEnter a network SSID: \e[0m"
            read user_ssid
            echo -n -e "\e[1;36mEnter the password: \e[0m"
            read -s user_pwd
            echo
            echo -n -e "\e[1;36mEnter the password again: \e[0m"
            read -s user_confirm
            echo

            if [[ "$user_pwd" = "$user_confirm" && "$user_ssid" != "" ]]
            then
                echo "network={" | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
                echo "        ssid=\"$user_ssid\"" | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
                echo "        psk=\"$user_pwd\"" | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
                echo "}" | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
                reset_wlan0=1
                break
            else
                show_prompt=1
            fi
            ;;
         2)
            echo
            echo -n -e "\e[1;36mEnter a network SSID: \e[0m"
            read user_ssid

            if [ ! "$user_ssid" = "" ]
            then
                echo "network={" | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
                echo "        ssid=\"$user_ssid\"" | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
                echo "        key_mgmt=NONE" | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
                echo "}" | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
                reset_wlan0=5
                break
            else
                show_prompt=1
            fi
            ;;
         3)
            sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
            reset_wlan0=5
            break
            ;;
         4)
            should_reboot=1
            break;
            ;;
        esac

        if [[ $reset_wlan0 -gt 0 ]]
        then
            if [[ $reset_wlan0 -eq 5 ]]
            then
                echo -e "\e[1;32mReconfiguring WLAN0...\e[0m"
                wpa_cli -i wlan0 reconfigure
                show_prompt=1
                sleep 3
            elif [[ $reset_wlan0 -eq 1 ]]
            then
                echo -e "\e[1;31mFailed to connect to network."
                show_prompt=1
            else
                # decrement the counter
                reset_wlan0= expr $reset_wlan0 - 1
            fi

            $reset_wlan0=4
        fi
    
    done

    if [[ $should_reboot -eq 255 ]]
    then
        # Auto-detected
        echo
        echo -e "\e[1;32mNetwork connection detected! Continuing...\e[0m"
        should_reboot=0
    fi

    return $should_reboot
    echo
    echo
    echo
    echo
}

function engine_setup() {

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "TTS SETUP:"
    echo "TTS, stands for Text To Speech, and is software that transforms text into speech,"
    echo "which is how Naomi can speak to you. You will need to pick one of the options below"
    echo 
    echo "Note: Some engines do not require you to do anything other than input information during the profile setup."
    echo
    echo -e "\e[1;36m"
    echo "  1) Google TTS"
    echo "  2) Microsoft TTS"
    echo "  3) Festival (only english is available at this time!)"
    echo "  4) Espeak"
    echo "  5) SvoxPico"
    echo "  6) Flite"
    echo -n -e "\e[1;36mChoice [\e[1;35m1\e[1;36m-\e[1;35m6\e[1;36m]: \e[0m"
    while true; do
        read -N1 -s key
        case $key in
         1)
            echo -e "\e[1;32m$key - Google TTS"
            # nothing to do, handled in POP
            break
            ;;
         2)
            echo -e "\e[1;32m$key - Mirosoft TTS"
            # nothing to do, handled in POP
            break
            ;;
         3)
            echo -e "\e[1;32m$key - Festival"
            cd ~
            sudo apt-get install festival festvox-kallpc16k
            break
            ;;
         4)
            echo -e "\e[1;32m$key - Espeak"
            cd ~
            sudo apt-get install espeak
            break
            ;;
         5)
            echo -e "\e[1;32m$key - SvoxPico"
            cd ~
            sudo apt-get install libttspico-utils
            break
            ;;
         6)
            echo -e "\e[1;32m$key - Flite"
            cd ~
            sudo apt install flite -y
            break
            ;;
        esac
    done
    echo
    echo
    echo
    echo

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "STT SETUP:"
    echo "STT, stands for Speech to Text, and is software that transforms spoken words & sentences"
    echo "into text, which is how Naomi can understand you. You will need to pick one of the Below"
    echo 
    echo "Note: For accuracy, really good understanding and easy to use, online solutions are better!"
    echo "      But for privacy reasons and to use Naomi without internet access, we recommend"
    echo "      the use of offline solutions"
    echo
    echo -e "\e[1;36m"
    echo "  1) Wit.ai"
    echo "  2) Google Cloud STT"
    echo "  3) Pocketsphinx"
    echo "  4) Mozilla DeepSpeech"
    echo -n -e "\e[1;36mChoice [\e[1;35m1\e[1;36m-\e[1;35m4\e[1;36m]: \e[0m"
    while true; do
        read -N1 -s key
        case $key in
         1)
            echo -e "\e[1;32m$key - Wit.ai"
            echo -e "\e[1;36m"
            echo "You will need a token that you receive for free by registering an account on the Wit.ai website!"
            echo "https://wit.ai"
            sleep 5
            pip install wit
            break
            ;;
         2)
            echo -e "\e[1;32m$key - Google Cloud STT"
            echo -e "\e[1;36m"
            echo "You will need a token that you receive for free by registering an account on the Google Cloud website!"
            echo "https://cloud.google.com/speech-to-text/"
            echo
            echo "In particular, this page explains how to register and how to retrieve your private key:"
            echo "https://cloud.google.com/speech-to-text/docs/quickstart-protocol"
            sleep 5
            break
            ;;
         3)
            echo -e "\e[1;32m$key - Pocketsphinx"
            echo "Beginning the Pocket build process.  This will take around 3 hours..."
            echo "Treat yourself to a movie and some popcorn in the mean time."
            echo -e "Results will be in the \e[1;35m~/.naomi/pocketsphinx-build.log"
            sleep 10
            cd ~/.naomi/scripts/
            wget https://git.io/JeBlW -O pocketsphinx-setup.sh
            cd ~
            bash ~/.naomi/scripts/pocketsphinx-setup.sh -y 2>&1 | tee ~/.naomi/pocketsphinx-build.log
            echo
            echo -e "\e[1;36mBuild complete.  Press any key to review the output."
            read -N1 -s key
            nano ~/.naomi/pocketsphinx-build.log
            cd ~
            break
            ;;
         4)
            echo -e "\e[1;32m$key - DeepSpeech"
            cd ~
            sudo pip3 install DeepSpeech
            wget https://github.com/mozilla/DeepSpeech/releases/download/v0.5.1/deepspeech-0.5.1-models.tar.gz
            tar xzvf deepspeech-0.5.1-models.tar.gz
            cd ~
            break
            ;;
        esac
    done
}

function setup_wizard() {

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "SETUP WIZARD"
    echo "This process will first walk you through setting up your device,"
    echo "installing Naomi, and default plugins."
    echo
    sleep 3
    echo
    echo

    # Handle internet connection
    network_setup
    if [[ $? -eq 1 ]]
    then
        echo -e "\e[1;32mRebooting...\e[0m"
        sudo reboot
    fi

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "LOCALIZATION SETUP:"
    echo -e "By default the Raspbian OS has \e[1;33men_GB.UTF-8 \e[1;36mlocale enabled by default."
    echo "Which is rightfully so since the Raspberry Pi Foundation is located in the UK. But for"
    echo "any one not living in the UK this presents an issue if configured wrong."
    echo
    echo "Select your locale from the list below:"
    echo
    echo -e "\e[1;36m"
    echo "  1) en_GB"
    echo "  2) en_US"
    echo "  3) fr_FR"
    echo "  4) de_DE"
    echo -n -e "\e[1;36mChoice [\e[1;35m1\e[1;36m-\e[1;35m4\e[1;36m]: \e[0m"
    while true; do
        read -N1 -s key
        case $key in
         [1])
            echo -e "\e[1;32m$key - Enabling en_GB UTF-8"
            sudo su -c 'echo "en_GB.UTF-8 UTF-8" > /etc/locale.gen'
            sudo locale-gen en_GB.UTF-8
            sudo su -c 'echo "LANG=en_GB.UTF-8" > /etc/default/locale'
            sudo update-locale en_GB.UTF-8
            LANG="en_GB.UTF-8"
            break
            ;;
         [2])
            echo -e "\e[1;32m$key - Enabling en_US UTF-8"
            sudo su -c 'echo "en_US.UTF-8 UTF-8" > /etc/locale.gen'
            sudo locale-gen en_US.UTF-8
            sudo su -c 'echo "LANG=en_US.UTF-8" > /etc/default/locale'
            sudo update-locale en_US.UTF-8
            LANG="en_US.UTF-8"
            break
            ;;
         [3])
            echo -e "\e[1;32m$key - Enabling fr_FR UTF-8"
            sudo su -c 'echo "fr_FR.UTF-8 UTF-8" > /etc/locale.gen'
            sudo locale-gen fr_FR.UTF-8
            sudo su -c 'echo "LANG=fr_FR.UTF-8" > /etc/default/locale'
            sudo update-locale fr_FR.UTF-8
            LANG="fr_FR.UTF-8"
            break
            ;;
         [4])
            echo -e "\e[1;32m$key - Enabling de_DE UTF-8"
            sudo su -c 'echo "de_DE.UTF-8 UTF-8" > /etc/locale.gen'
            sudo locale-gen de_DE.UTF-8
            sudo su -c 'echo "LANG=de_DE.UTF-8" > /etc/default/locale'
            sudo update-locale de_DE.UTF-8
            LANG="fr_FR.UTF-8"
            break
            ;;
        esac
    done
    echo
    echo
    echo
    echo

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "SECURITY SETUP:"
    echo "Let's examine a few security settings."
    echo
    sleep 3
    echo

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "ENVIRONMENT SETUP:"
    echo "Now setting up the file stuctures & requirements"
    echo
    sleep 3
    echo

    # Create basic folder structures
    echo
    echo -e "\e[1;32mCreating File Structure...\e[0m"
    mkdir ~/.naomi/
    mkdir ~/.naomi/configs/
    mkdir ~/.naomi/scripts/

    # Check if apt-get is installed
    echo
    echo -e "\e[1;32mChecking For 'apt-get'...\e[0m"
    APT=0
    if command -v apt-get > /dev/null 2>&1 ; then
        APT=1
    fi

    # Download and setup Naomi Dev as default
    echo
    echo -e "\e[1;32mInstalling 'git'...\e[0m"
    sudo apt-get install git -y
    echo
    echo -e "\e[1;32mDownloading 'Naomi'...\e[0m"
    cd ~
    git clone https://github.com/NaomiProject/Naomi.git
    cd ~/Naomi
    git checkout naomi-dev
    git pull

    NAOMI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"

    if [ $APT -eq 1 ]; then
        echo
        echo -e "\e[1;32mDependencies Update & Install...\e[0m"
        sudo apt-get update
        sudo apt-get install gettext portaudio19-dev libasound2-dev -y
    else
        ERROR=""
        if [[ $(CHECK_PROGRAM msgfmt) -ne "0" ]]; then
            ERROR="${ERROR} gettext program msgfmt not found${NL}"
        fi
        if [[ $(CHECK_HEADER portaudio.h) -ne "0" ]]; then
            ERROR="${ERROR} portaudio development file portaudio.h not found${NL}"
        fi
        if [[ $(CHECK_HEADER asoundlib.h) -ne "0" ]]; then
            ERROR="${ERROR} libasound development file asoundlib.h not found${NL}"
        fi
        if [ ! -z "$ERROR" ]; then
            echo "Missing dependencies:${NL}${NL}$ERROR"
            CONTINUE
        else
            printf "${GREEN}All depenancies look okay${NC}${NL}"
        fi
    fi

    echo
    echo -e "\e[1;32mVirtualEnv Setup...\e[0m"
    if [ $APT -eq 1 ]; then
        sudo apt-get install python python-pip python3 python3-pip
    else
        ERROR=""
        if [[ $(CHECK_PROGRAM python) -ne "0" ]]; then
            ERROR="${ERROR} python not found${NL}"
        fi
        if [[ $(CHECK_PROGRAM pip) -ne "0" ]]; then
            ERROR="${ERROR} pip not found${NL}"
        fi
        if [[ $(CHECK_PROGRAM python3) -ne "0" ]]; then
            ERROR="${ERROR} python3 not found${NL}"
        fi
        if [[ $(CHECK_PROGRAM pip3) -ne "0" ]]; then
            ERROR="${ERROR} pip3 not found${NL}"
        fi
        if [ ! -z "$ERROR" ]; then
            echo "Missing depenancies:${NL}${NL}$ERROR"
            CONTINUE
        fi
    fi
    pip install --user virtualenvwrapper
    echo 'sourcing virtualenvwrapper.sh'
    export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv
    source ~/.local/bin/virtualenvwrapper.sh
    echo 'checking if Naomi virtualenv exists'
    workon Naomi > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo 'Naomi virtualenv does not exist. Creating.'
        PATH=$PATH:~/.local/bin mkvirtualenv -p python3 Naomi
        workon Naomi
    fi
    if [ $(which pip) = $HOME/.virtualenvs/Naomi/bin/pip ]; then
        echo 'in the Naomi virtualenv'
        pip install -r python_requirements.txt
        deactivate
    else
        echo "Something went wrong, not in virtual environment..." >&2
        exit 1
    fi
    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >> Naomi
    echo "source ~/.local/bin/virtualenvwrapper.sh" >> Naomi
    echo "workon Naomi" >> Naomi
    echo "python $NAOMI_DIR/Naomi.py \$@" >> Naomi
    echo "deactivate" >> Naomi
    echo
    echo
    echo
    echo

    echo -e "\e[1;36m"
    echo "We will set up Naomi to run in a python virtualenvwrapper environment"
    echo "to prevent Naomi's dependencies from interfering with other python"
    echo "scripts running on your system."
    echo " "
    echo "If you want, we can add the call to start virtualenvwrapper directly"
    echo -e "to the end of your \e[1;35m~/.bashrc\e[1;36m file, so if you want to use the same"
    echo "python that Naomi does for debugging or installing additional"
    echo -e "dependencies, all you have to type is \e[1;35m'workon Naomi'\e[1;36m"
    echo " "
    echo "Otherwise, you will need to enter:"
    echo -e "\e[1;35m'VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv'\e[1;36m"
    echo -e "\e[1;35m'source ~/.local/bin/virtualenvwrapper.sh'\e[1;36m"
    echo -e "before you will be able activate the Naomi environment with \e[1;35m'workon Naomi'\e[1;36m"
    echo " "
    echo "All of this will be incorporated into the Naomi script, so to simply"
    echo -e "launch Naomi, all you have to type is \e[1;35m'./Naomi'\e[1;36m regardless of your choice here."
    echo " "
    echo -e "\e[1;36m[\e[1;33m?\e[1;36m] Would you like to start VirtualEnvWrapper automatically? \e[0m"
    echo -e "\e[1;36m"
    echo "  Y)es, start virtualenvwrapper whenever I start a shell"
    echo "  N)o, don't start virtualenvwrapper for me"
    echo -n -e "\e[1;36mChoice [\e[1;35mY\e[1;36m/\e[1;35mN\e[1;36m]: \e[0m"
    while true; do
        read -N1 -s key
        case $key in
        [Yy])
            echo -e "\e[1;32m$key - Automating Naomi Startup"
            echo '######################################################################' >> ~/.bashrc
            echo '# Initialize Naomi to auto start on any terminal or ssh' >> ~/.bashrc
            echo '######################################################################' >> ~/.bashrc
            echo 'VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv source ~/.local/bin/virtualenvwrapper.sh' >> ~/.bashrc
            break
            ;;
        [Nn])
           echo -e "\e[1;32m$key - Manual Start"
           break
           ;;
        esac
    done
    echo
    echo
    echo
    echo

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "NAOMI SETUP:"
    echo "Naomi is continuously updated. There are three options to choose from:"
    echo
    echo "'Stable' versions are thoroughly tested official releases of Naomi. Use"
    echo "the stable version for your production environment if you don't need the"
    echo "latest enhancements and prefer a robust system"
    echo
    echo "'Milestone' versions are intermediary releases of the next Naomi version,"
    echo "released about once a month, and they include the new recently added"
    echo "features and bugfixes. They are a good compromise between the current"
    echo "stable version and the bleeding-edge and potentially unstable nightly version."
    echo
    echo "'Nightly' versions are at most 1 or 2 days old and include the latest code."
    echo "Use nightly for testing out very recent changes, but be aware some nightly"
    echo "versions might be unstable. Use in production at your own risk!"
    echo
    echo "Note: 'Nightly' comes with automatic updates by default!"
    echo -e "\e[1;36m"
    echo "  1) Use the recommended ('Stable')"
    echo "  2) Monthly releases sound good to me ('Milestone')"
    echo "  3) I'm a developer or want the cutting edge, put me on 'Nightly'"
    echo -n -e "\e[1;36mChoice [\e[1;35m1\e[1;36m-\e[1;35m3\e[1;36m]: \e[0m"
    while true; do
        read -N1 -s key
        case $key in
         1)
            echo -e "\e[1;32m$key - Easy Peasy!"
            version="2.2"
            echo '{"use_release":"stable", "version":"Naomi-'$version'", "auto_update":"false"}' > ~/.naomi/configs/.naomi_options.json
            cd ~
            mv ~/Naomi ~/Naomi-Temp
            cd ~
            curl -L "https://dl.bintray.com/naomiproject/rpi-repo2/stable/Naomi-$version.zip" -o Naomi-$version.zip
            unzip Naomi-$version.zip
            mv Naomi-$version Naomi
            cd ~
            break
            ;;
         2)
            echo -e "\e[1;32m$key - Good Choice!"    
            version="3.0"
            month=$(date +%-m)
            offset=12
            milestone=$((month+offset))
            echo '{"use_release":"milestone", "version":"Naomi-'$version'.M'$milestone'", "auto_update":"false"}' > ~/.naomi/configs/.naomi_options.json
            cd ~
            mv ~/Naomi ~/Naomi-Temp
            cd ~
            curl -L "https://dl.bintray.com/naomiproject/rpi-repo2/dev/Naomi-$version.M$milestone.zip" -o Naomi-$version.M$milestone.zip
            unzip Naomi-$version.M$milestone.zip
            mv Naomi-$version.M$milestone Naomi
            cd ~
            break
            ;;
         3)
            echo -e "\e[1;32m$key - You know what you are doing!"
            echo '{"use_release":"nightly", "version":"Naomi-Nightly", "auto_update":"true"}' > ~/.naomi/configs/.naomi_options.json
            cd ~
            mv ~/Naomi ~/Naomi-Temp
            cd ~
            curl -L "https://dl.bintray.com/naomiproject/rpi-repo2/nightly/Naomi-Nightly.zip" -o Naomi-Nightly.zip
            unzip Naomi-Nightly.zip
            mv Naomi-Nightly Naomi
            cd ~
            break
            ;;
        esac
    done
    echo
    echo
    echo
    echo

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "PLUGIN SETUP"
    echo "Now we'll tackle the different plugin options available for Text-to-Speech, Speech-to-Text, and more."
    echo
    sleep 3
    echo

    echo -e "\e[1;36m"
    echo "========================================================================="
    echo "Pre-Configs:"
    echo "Naomi has various options for active and or passive Text-to-Speech engines as well"
    echo "as Speech-to-Text engines. We have put together two pre-configured setups that make"
    echo "setup easier. The options fall into two categories: Better Privacy & Better Accuracy."
    echo
    echo "Better Privacy includes Flite for TTS & PocketSphinx for STT"
    echo
    echo "Better Accuracy includes Google for TTS & active listening STT, and PocketSphinx"
    echo "for passive listening STT"
    echo
    echo "Note: As always you can select to set things up manually if you so wish."
    echo
    echo -e "\e[1;36m"
    echo "  1) Better Privacy"
    echo "  2) Better Accuracy"
    echo "  3) Manual Setup"
    echo -n -e "\e[1;36mChoice [\e[1;35m1\e[1;36m-\e[1;35m3\e[1;36m]: \e[0m"
    while true; do
        read -N1 -s key
        case $key in
         1)
            echo -e "\e[1;32m$key - Better Privacy!"
            echo "Installing Flite..."
            cd ~
            sudo apt install flite -y
            echo "Beginning the Pocket build process.  This will take around 3 hours..."
            echo "Treat yourself to a movie and some popcorn in the mean time."
            echo -e "Results will be in the \e[1;35m~/.naomi/pocketsphinx-build.log"
            sleep 10
            cd ~/.naomi/scripts/
            wget https://git.io/JeBlW -O pocketsphinx-setup.sh
            cd ~
            bash ~/.naomi/scripts/pocketsphinx-setup.sh -y 2>&1 | tee ~/.naomi/pocketsphinx-build.log
            echo
            echo -e "\e[1;36mBuild complete.  Press any key to review the output."
            read -N1 -s key
            nano ~/.naomi/pocketsphinx-build.log
            cd ~
            break
            ;;
         2)
            echo -e "\e[1;32m$key - Better Accuracy!"
            pip3 install google-api-core==1.9.0
            pip3 install google-auth==1.6.3
            pip3 install google-cloud-speech==1.0.0
            pip3 install google-cloud-texttospeech==0.5.0
            pip3 install googleapis-common-protos==1.5.9
            pip3 install grpcio
            touch download_google_json
            cd ~/.naomi/scripts/
            wget https://git.io/JeBlW -O pocketsphinx-setup.sh
            cd ~
            bash ~/.naomi/scripts/pocketsphinx-setup.sh -y 2>&1 | tee ~/.naomi/pocketsphinx-build.log
            echo
            echo -e "\e[1;36mBuild complete.  Press any key to review the output."
            read -N1 -s key
            nano ~/.naomi/pocketsphinx-build.log
            cd ~
            break
            ;;
         3)
            echo -e "\e[1;32m$key - Manual Setup!"
            engine_setup
            break
            ;;
        esac
    done
    echo
    echo
    echo
    echo
 
    # Compiling Translations
    echo
    echo -e "\e[1;32mCompiling Translations...\e[0m"
    cd ~/Naomi
    chmod +x compile_translations.sh
    ./compile_translations.sh
    chmod a+x Naomi
    cd ~
    echo
    echo
    echo
    echo

    if [ -f download_google_json ]
    then
        echo -e "\e[1;36m"
        echo "========================================================================="
        echo
        echo "That's all, installation is complete! Now you'll need to follow the"
        echo "instructions for the Better Accuracy config."
        echo
        echo "https://projectnaomi.com/dev/docs/configuration/pre-configs/"
        echo
        echo "Please follow the instructions and you will have Naomi running in no time!"
        echo -e "\e[1;36mPress any key to finish installation..."
        read -N1 -s anykey
        mv ~/Naomi-Temp/Naomi ~/Naomi/Naomi
        sudo rm -Rf ~/Naomi-Temp
        break
    elif [ ! $skip_last_prompt ];
    then
        echo -e "\e[1;36m"
        echo "========================================================================="
        echo
        echo "That's all, installation is complete! Now we'll hand you over to the profile"
        echo "population process and after that Naomi will start."
        echo
        echo "In the future, run $NAOMI_DIR/Naomi to start Naomi"
        echo
        echo -e "\e[1;36mPress any key to start populating your profile..."
        read -N1 -s anykey
        mv ~/Naomi-Temp/Naomi ~/Naomi/Naomi
        sudo rm -Rf ~/Naomi-Temp
        # Launch Naomi Population
        cd ~/Naomi
        ./Naomi --repopulate
    fi
}



tput reset
echo -e "\e[33m"
echo "      ___           ___           ___           ___                  "
echo "     /\__\         /\  \         /\  \         /\__\          ___    "
echo "    /::|  |       /::\  \       /::\  \       /::|  |        /\  \   "
echo "   /:|:|  |      /:/\:\  \     /:/\:\  \     /:|:|  |        \:\  \  "
echo "  /:/|:|  |__   /::\~\:\  \   /:/  \:\  \   /:/|:|__|__      /::\__\ "
echo " /:/ |:| /\__\ /:/\:\ \:\__\ /:/__/ \:\__\ /:/ |::::\__\  __/:/\/__/ "
echo " \/__|:|/:/  / \/__\:\/:/  / \:\  \ /:/  / \/__/~~/:/  / /\/:/  /    "
echo "     |:/:/  /       \::/  /   \:\  /:/  /        /:/  /  \::/__/     "
echo "     |::/  /        /:/  /     \:\/:/  /        /:/  /    \:\__\     "
echo "     /:/  /        /:/  /       \::/  /        /:/  /      \/__/     "
echo "     \/__/         \/__/         \/__/         \/__/                 "



if [ ! -f ~/.naomi/configs/profile.yml ]
then
    echo -e "\e[1;36m"
    echo "Welcome to Naomi. This process is designed to make getting started with"
    echo "Naomi quick and easy. Would you like help setting up your system?"
    echo
    echo "Note: Some options can cause the process to take up to 3 hours"
    echo
    echo "  Y)es, I'd like the guided setup."
    echo "  N)ope, just get me a command line and get out of my way!"
    echo
    echo -n -e "\e[1;36mChoice [\e[1;35mY\e[1;36m/\e[1;35mN\e[1;36m]: \e[0m"
    while true; do
        read -N1 -s key
        case $key in
         [Nn])
            echo -e "\e[1;32m$key - Nope"
            echo
            echo -e "\e[1;92mAlright, Good luck & have fun!"
            echo
            break
            break
            ;;
         [Yy])
            echo -e "\e[1;32m$key - Yes"
            echo
            setup_wizard
            break
            ;;
        esac
    done
fi