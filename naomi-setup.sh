#!/bin/bash

#########################################
# Installing python and necessary packages
# for Naomi. This script will install python
# into the ~/.config/naomi/local/bin directory and
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
    printf "${RED}Notice:${NC} this program is about to use sudo to run the following command:${NL}"
    printf "[$(pwd)]\$ ${GREEN}${1}${NC}${NL}"
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

# Create our working directory
# FIXME unfortunately this does not currently take into account the 
# $NAOMI_SUB environment variable)
mkdir -p ~/.config/naomi/sources

# Check command line options
for var in "$@"; do
    if [ "$var" = "--virtualenv" ]; then
        OPTION="1"
        SUDO_APPROVE="-y"
    fi
    if [ "$var" = "--local-compile" ]; then
        OPTION="2"
        SUDO_APPROVE="-y"
    fi
    if [ "$var" = "--system" ]; then
        OPTION="3"
        SUDO_APPROVE="-y"
    fi
    if [ "$var" = "--help" ]; then
        echo "USAGE: $0 [-y|--yes] [--virtualenv | --local | --primary | --help]"
        echo
        echo "  --virtualenv    - install Naomi using a virtualenv environment for Naomi"
        echo "                    (this is the recommended choice. You will need to issue"
        echo "                    'workon Naomi' before installing additional libraries"
        echo "                    for Naomi)"
        echo
        echo "  --local-compile - download, compile and install a special copy of Python 3"
        echo "                    for Naomi (does not work for all distros)"
        echo
        echo "  --system        - use your primary Python 3 environment"
        echo "                    (this can be dangerous, it can lead to a broken python"
        echo "                    environment on your system, which other software may"
        echo "                    depend on. This is the simplest setup, but only recommended"
        echo "                    when Naomi is the primary program you intend to run on this"
        echo "                    computer. You will probably need to use the 'pip3' command"
        echo "                    to install additional libraries for Naomi.)"
        echo "                    USE AT YOUR OWN RISK!"
        echo
        echo "  Including any of the above options will also cause the script to accept all"
        echo "  default options and run without user intervention"
        echo
        echo "  --help          - Print this message and exit"
        exit 0
    fi
done
# Check if apt-get is installed
APT=0
if command -v apt-get > /dev/null 2>&1 ; then
    APT=1
fi

# Main program logic
if [ $OPTION = "0" ]; then
    printf "${LT_BLUE}There are three methods to install Naomi:${NL}"
    printf "${NL}"
    printf "1) Use virtualenvwrapper to create a virtual Python 3 environment${NL}"
    printf "   for Naomi (${GREEN}recommended${LT_BLUE})${NL}"
    printf "2) Download, compile, and install a local copy of Python for Naomi${NL}"
    printf "   (may not work for some users)${NL}"
    printf "3) Use your primary Python 3 environment (this can be dangerous${NL}"
    printf "   and can break other software on your system. It is only${NL}"
    printf "   recommended for machines you intend to devote to running Naomi,${NL}"
    printf "   like a virtual machine or Raspberry Pi)${NL}"
    printf "4) Exit without installing${NL}"
    printf "${NL}"
    printf "${RED}Note: This process can take quite a bit of time (up to three hours)${NC}${NL}"
    echo
    while [ $OPTION != "1" ] && [ $OPTION != "2" ] && [ $OPTION != "3" ] && [ $OPTION != "4" ]; do
        read -e -p 'Please select: ' OPTION
        if [ $OPTION != "1" ] && [ $OPTION != "2" ] && [ $OPTION != "3" ] && [ $OPTION != "4" ]; then
            echo "Please choose 1, 2, 3 or 4"
        fi
    done
fi

case $OPTION in
    "1")
        printf "${GREEN}Installing using VirtualEnvWrapper${NC}${NL}"
        ;;
    "2")
        printf "${GREEN}Installing using custom built python${NC}${NL}"
        ;;
    "3")
        printf "${GREEN}Installing using default python3${NC}${NL}"
        ;;
    "4")
        printf "${GREEN}Exiting${NC}${NL}"
        exit 1
        ;;
esac

# Assume this program is in the main Naomi directory
# so we can save and return to it.
NAOMI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ $APT -eq 1 ]; then
    SUDO_COMMAND "sudo apt-get update"
    SUDO_COMMAND "sudo apt upgrade $SUDO_APPROVE"
    # install dependencies
    SUDO_COMMAND "sudo ./naomi_apt_requirements.sh $SUDO_APPROVE"
    if [ $? -ne 0 ]; then
        echo "Error installing apt packages" >&2
        exit 1
    fi
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
    if [[ $(CHECK_PROGRAM python3) -ne "0" ]]; then
        ERROR="${ERROR} python3 not found${NL}"
    fi
    if [[ $(CHECK_PROGRAM pip3) -ne "0" ]]; then
        ERROR="${ERROR} pip3 not found${NL}"
    fi
    if [ ! -z "$ERROR" ]; then
        echo "Missing dependencies:${NL}${NL}$ERROR"
        CONTINUE
    fi
fi
# make sure pulseaudio is running
pulseaudio --check
if [ $? -ne 0 ]; then
    pulseaudio -D
fi
if [ $OPTION = "1" ]; then
    pip3 install --user virtualenv virtualenvwrapper=='4.8.4'
    echo 'sourcing virtualenvwrapper.sh'
    export WORKON_HOME=$HOME/.virtualenvs
    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv
    source ~/.local/bin/virtualenvwrapper.sh
    export VIRTUALENVWRAPPER_ENV_BIN_DIR=bin
    echo 'checking if Naomi virtualenv exists'
    workon Naomi > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo 'Naomi virtualenv does not exist. Creating.'
        PATH=$PATH:~/.local/bin mkvirtualenv -p python3 Naomi
    fi
    workon Naomi
    if [ "$(which pip)" = "$HOME/.virtualenvs/Naomi/bin/pip" ]; then
        echo -e "\e[1;36mIf you want, we can add the call to start virtualenvwrapper directly"
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
        echo -n -e "\e[1;36mChoice [\e[1;35mY\e[1;36m/\e[1;35mn\e[1;36m]: \e[0m"
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
                    echo "Please choose 'Y' or 'N'"
                fi
            done
        fi
        if [ "$AUTO_START" = "Y" ] || [ "$AUTO_START" = "y" ]; then
            echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc
            echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.bashrc
            echo "export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >> ~/.bashrc
            echo "source ~/.local/bin/virtualenvwrapper.sh" >> ~/.bashrc
        fi
        pip install -r python_requirements.txt
        if [ $? -ne 0 ]; then
            echo "Error installing python requirements: $!" >&2
            exit 1
        fi
    else
        echo "Something went wrong, not in virtual environment..." >&2
        exit 1
    fi
    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "export WORKON_HOME=$HOME/.virtualenvs" >> Naomi
    echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> Naomi
    echo "export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >> Naomi
    echo "source ~/.local/bin/virtualenvwrapper.sh" >> Naomi
    echo "workon Naomi" >> Naomi
    echo "python $NAOMI_DIR/Naomi.py \$@" >> Naomi
fi
if [ $OPTION = "2" ]; then
    # installing python
    echo 'Installing python 3.7.7 to ~/.config/naomi/local'
    # libffi-dev required to build cython, required for setuptools, required for pip
    # libsqlite3-dev required to build sqlite3 module
    SUDO_COMMAND "sudo apt install libffi-dev libsqlite3-dev $SUDO_APPROVE"
    mkdir -p ~/.config/naomi/local
    cd ~/.config/naomi/sources
    NAME=Python
    VERSION=3.7.7
    VERNAME=$NAME-$VERSION
    CHKSUM=d348d978a5387512fbc7d7d52dd3a5ef
    TARFILE=$VERNAME.tgz
    URL=https://www.python.org/ftp/python/$VERSION/$TARFILE
    KEYID=2D347EA6AA65421D # Ned Deily (Python release signing key) <nad@python.org>
    if [ ! -f $TARFILE ]; then
        wget $URL
    fi
    if [ ! -f $TARFILE.asc ]; then
        wget $URL.asc
    fi
    gpg --list-keys $KEYID || gpg --keyserver pgp.mit.edu --recv-keys $KEYID || gpg --keyserver keys.gnupg.net --recv-keys $KEYID
    gpg --verify $TARFILE.asc
    if [ $? -eq 0 ]; then
        echo "Python tarball signature verified"
    else
        echo "Can't verify $TARFILE signature" >&2
        exit 1
    fi
    echo "$CHKSUM $TARFILE" | md5sum -c -

    if [ $? -eq 0 ]; then
        echo "Python checksum verified"
    else
        echo "Python checksum verification failed" >&2
        exit 1
    fi
    tar xvzf $TARFILE
    cd $VERNAME
    export PYTHONHOME=$(cd ~/.config/naomi/local && pwd)
    printf "[$(pwd)]\$ ${GREEN}./configure --prefix=${PYTHONHOME}${NC}${NL}"
    ./configure --prefix=$PYTHONHOME
    printf "[$(pwd)]\$ ${GREEN}make${NC}${NL}"
    make
    printf "[$(pwd)]\$ ${GREEN}make altinstall prefix=${PYTHONHOME}${NC}${NL}"
    make altinstall prefix=$PYTHONHOME  # specify local installation directory

    echo "****************"
    echo "Python Installed to ${PYTHONHOME}/bin/python"
    echo "****************"
    ln -s ~/.config/naomi/local/bin/python${VERSION:0:3} ~/.config/naomi/local/bin/python
    ln -s ~/.config/naomi/local/bin/pip${VERSION:0:3} ~/.config/naomi/local/bin/pip
    echo "Links created"
    cd ..  # ~/.config/naomi/local

    # install naomi & dependencies
    echo "Returning to $NAOMI_DIR"
    cd $NAOMI_DIR
    # Create a custom cache dir so we don't use cached files from our main python
    export XDG_CACHE_HOME=~/.config/naomi/local/cache
    mkdir -p "$XDG_CACHE_HOME"
    ~/.config/naomi/local/bin/pip install --cache-dir=~/.config/naomi/local/cache -r python_requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error installing python_requirements.txt" >&2
        exit 1
    fi

    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "~/.config/naomi/local/bin/python $NAOMI_DIR/Naomi.py \$@" >> Naomi
fi
if [ $OPTION = "3" ]; then
    pip3 install --user -r python_requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error installing python_requirements.txt" >&2
        exit 1
    fi
    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "python3 $NAOMI_DIR/Naomi.py \$@" >> Naomi
fi
if [ $OPTION = "4" ]; then
    echo 'Exiting'
    exit 0
fi
# Build Phonetisaurus
# Building and installing openfst
echo
echo -e "\e[1;32mBuilding and installing openfst...\e[0m"
cd ~/.config/naomi/sources

if [ ! -f "openfst-1.6.9.tar.gz" ]; then
    wget http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.6.9.tar.gz
fi
tar -zxvf openfst-1.6.9.tar.gz
cd openfst-1.6.9
autoreconf -i
./configure --enable-static --enable-shared --enable-far --enable-lookahead-fsts --enable-const-fsts --enable-pdt --enable-ngram-fsts --enable-linear-fsts --prefix=/usr
make
SUDO_COMMAND "sudo make install"
if [ $? -ne 0 ]; then
    echo $! >&2
    exit 1
fi

if [ -z "$(which fstinfo)" ]; then
    echo "ERROR: openfst not installed" >&2
    exit 1
fi

# Building and installing mitlm-0.4.2
echo
echo -e "\e[1;32mInstalling & Building mitlm-0.4.2...\e[0m"
cd ~/.config/naomi/sources
if [ ! -d "mitlm" ]; then
    git clone https://github.com/mitlm/mitlm.git
    if [ $? -ne 0 ]; then
        printf "${ERROR}Error cloning mitlm${NC}${NL}"
        exit 1
    fi
fi

cd mitlm
./autogen.sh
make
echo "Installing mitlm"
SUDO_COMMAND "sudo make install"
if [ $? -ne 0 ]; then
    echo $! >&2
    exit 1
fi

# Building and installing CMUCLMTK
echo
echo -e "\e[1;32mInstalling & Building cmuclmtk...\e[0m"
cd ~/.config/naomi/sources
svn co https://svn.code.sf.net/p/cmusphinx/code/trunk/cmuclmtk/
if [ $? -ne 0 ]; then
    echo "Error cloning cmuclmtk" >&2
    exit 1
fi

cd cmuclmtk
./autogen.sh
make
echo "Installing CMUCLMTK"
SUDO_COMMAND "sudo make install"

echo "Linking shared libraries"
SUDO_COMMAND "sudo ldconfig"

# Building and installing phonetisaurus
echo
echo -e "\e[1;32mInstalling & Building phonetisaurus...\e[0m"
cd ~/.config/naomi/sources
if [ ! -d "Phonetisaurus" ]; then
    git clone https://github.com/AdolfVonKleist/Phonetisaurus.git
    if [ $? -ne 0 ]; then
        echo "Error cloning Phonetisaurus" >&2
        exit 1
    fi
fi
cd Phonetisaurus
./configure --enable-python
make
echo "Installing Phonetisaurus"
SUDO_COMMAND "sudo make install"

printf "[$(pwd)]\$ ${GREEN}cd python${NC}${NL}"
cd python
echo $(pwd)

cp -v ../.libs/Phonetisaurus.so ./
if [ "$OPTION" = "1" ]; then
    SUDO_COMMAND "sudo python setup.py install"
fi
if [ "$OPTION" = "2" ]; then
    SUDO_COMMAND "sudo ~/.config/naomi/local/bin/python setup.py install"
fi
if [ "$OPTION" = "3" ]; then
    SUDO_COMMAND "sudo python3 setup.py install"
fi

if [ -z "$(which phonetisaurus-g2pfst)" ]; then
    echo "ERROR: phonetisaurus-g2pfst does not exist" >&2
    EXIT 1
fi

# Installing & Building sphinxbase
echo
echo -e "\e[1;32mBuilding and installing sphinxbase...\e[0m"
cd ~/.config/naomi/sources
if [ ! -d "pocketsphinx-python" ]; then
    git clone --recursive https://github.com/cmusphinx/pocketsphinx-python.git
    if [ $? -ne 0 ]; then
        echo "Error cloning pocketsphinx" >&2
        exit 1
    fi
fi

cd pocketsphinx-python/sphinxbase
./autogen.sh
make
SUDO_COMMAND "sudo make install"

# Installing & Building pocketsphinx
echo
echo -e "\e[1;32mBuilding and installing pocketsphinx...\e[0m"
cd ~/.config/naomi/sources/pocketsphinx-python/pocketsphinx
./autogen.sh
make
SUDO_COMMAND "sudo make install"

# Installing PocketSphinx Python module
echo
echo -e "\e[1;32mInstalling PocketSphinx module...\e[0m"
cd ~/.config/naomi/sources/pocketsphinx-python
if [ "$OPTION" = "1" ]; then
    python setup.py install
fi
if [ "$OPTION" = "2" ]; then
    ~/.config/naomi/local/bin/python setup.py install
fi
if [ "$OPTION" = "3" ]; then
    SUDO_COMMAND "sudo python3 setup.py install"
fi

cd $NAOMI_DIR
if [ -z "$(which text2wfreq)" ]; then
    echo "ERROR: text2wfreq does not exist" >&2
    EXIT 1
fi
if [ -z "$(which text2idngram)" ]; then
    echo "ERROR: text2idngram does not exist" >&2
    EXIT 1
fi
if [ -z "$(which idngram2lm)" ]; then
    echo "ERROR: idngram2lm does not exist" >&2
    EXIT 1
fi

./compile_translations.sh

chmod a+x Naomi

echo "Installation is complete"
echo "You can delete the directories in ~/.config/naomi/sources if you like"
echo

if [ $OPTION = "1" ]; then
    echo
    echo "You will need to activate the Naomi virtual environment when installing"
    echo "or testing python modules for Naomi using the following command:"
    echo "  $ workon Naomi"
    echo "You should add the following lines to your ~/.bashrc script:"
    echo "  export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv"
    echo "  source ~/.local/bin/virtualenvwrapper.sh"
    echo
fi
if [ $OPTION = "2" ]; then
    echo
    echo "You will need to use Naomi's special python and pip commands when"
    echo "installing modules or testing with Naomi:"
    echo "  ~/.config/naomi/local/bin/python"
    echo "  ~/.config/naomi/local/bin/pip"
    echo
fi
echo "In the future, run $NAOMI_DIR/Naomi to start Naomi"
echo
./Naomi --repopulate
