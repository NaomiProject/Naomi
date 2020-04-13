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
SUDO_APPROVE="n"

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

# Create our working directory (unfortunately this does not currently take into accunt the 
# $
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
    echo 'There are three methods to install Naomi:'
    echo
    echo '1) Use virtualenvwrapper to create a virtual Python 3 environment'
    echo '   for Naomi (recommended)'
    echo '2) Download, compile, and install a local copy of Python for Naomi'
    echo '   (may not work for some users)'
    echo '3) Use your primary Python 3 environment (this can be dangerous'
    echo '   and can break other software on your system. It is only'
    echo '   recommended for machines you intend to devote to running Naomi,'
    echo '   like a virtual machine or Raspberry Pi)'
    echo '4) Exit without installing'
    echo
    echo 'Note: This process can take quite a bit of time (up to three hours)'
    echo
    while [ $OPTION != "1" ] && [ $OPTION != "2" ] && [ $OPTION != "3" ] && [ $OPTION != "4" ]; do
        read -e -p 'Please select: ' OPTION
        if [ $OPTION != "1" ] && [ $OPTION != "2" ] && [ $OPTION != "3" ] && [ $OPTION != "4" ]; then
            echo "Please choose 1, 2, 3 or 4"
        fi
    done
fi
# Assume this program is in the main Naomi directory
# so we can save and return to it.
NAOMI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ $APT -eq 1 ]; then
    SUDO_COMMAND "sudo apt-get update"
    SUDO_COMMAND "sudo apt upgrade $SUDO_APPROVE"
    # install dependencies
    SUDO_COMMAND "sudo ./naomi_apt_requirements.sh $SUDO_APPROVE"
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
        echo "Missing depenancies:${NL}${NL}$ERROR"
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
        echo -n -e "\e[1;36mChoice [\e[1;35mY\e[1;36m/\e[1;35mN\e[1;36m]: \e[0m"
        export AUTO_START=""
        while [ "$AUTO_START" != "Y" ] && [ "$AUTO_START" != "y" ] && [ "$AUTO_START" != "N" ] && [ "$AUTO_START" != "n" ]; do
            read -e -p 'Please select: ' AUTO_START
            if [ "$AUTO_START" != "Y" ] && [ "$AUTO_START" != "y" ] && [ "$AUTO_START" != "N" ] && [ "$AUTO_START" != "n" ]; then
                echo "Please choose 'Y' or 'N'"
            fi
        done
        if [ "$AUTO_START" = "Y" ] || [ "$AUTO_START" = "y" ]; then
            echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc
            echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.bashrc
            echo "export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >> ~/.bashrc
            echo "source ~/.local/bin/virtualenvwrapper.sh" >> ~/.bashrc
        fi
        pip install -r python_requirements.txt
        if [ $? -ne 0 ]; then
            echo "Error installing python requirements: $!"
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
    # installing python 3.5.3
    echo 'Installing python 3.5.3 to ~/.config/naomi/local'
    mkdir -p ~/.config/naomi/local
    cd ~/.config/naomi/local
    NAME=Python
    VERSION=3.5.3
    VERNAME=$NAME-$VERSION
    CHKSUM=d8890b84d773cd7059e597dbefa510340de8336ec9b9e9032bf030f19291565a
    TARFILE=$VERNAME.tgz
    URL=https://www.python.org/ftp/python/$VERSION/$TARFILE
    KEYID=3A5CA953F73C700D # Larry Hastings <larry@hastings.org>
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
    echo "$CHKSUM $TARFILE" | sha256sum -c -
    if [ $? -eq 0 ]; then
        echo "Python checksum verified"
    else
        echo "Python checksum verification failed" >&2
        exit 1
    fi
    tar xvzf $TARFILE
    cd $VERNAME
    ./configure
    make
    make altinstall prefix=~/.config/naomi/local  # specify local installation directory
    ln -s ~/.config/naomi/local/bin/python3.5 ~/.config/naomi/local/bin/python
    cd ..  # ~/.config/naomi/local

    # install setuptools and pip for package management
    NAME=setuptools
    VERSION=40.6.3
    VERNAME=$NAME-$VERSION
    CHKSUM=3b474dad69c49f0d2d86696b68105f3a6f195f7ab655af12ef9a9c326d2b08f8
    ZIPFILE=$VERNAME.zip
    URL=https://files.pythonhosted.org/packages/37/1b/b25507861991beeade31473868463dad0e58b1978c209de27384ae541b0b/$ZIPFILE
    # URL=https://files.pythonhosted.org/packages/37/1b/b25507861991beeade31473868463dad0e58b1978c209de27384ae541b0b/setuptools-40.6.3.zip
    echo 'Installing setuptools'
    if [ ! -f $ZIPFILE ]; then
        wget $URL
    fi
    echo "$CHKSUM $ZIPFILE" | sha256sum -c -
    if [ $? -eq 0 ]; then
        echo "SetupTools checksum verified"
    else
        echo "SetupTools checksum verification failed" >&2
        exit 1
    fi
    unzip $ZIPFILE
    cd $VERNAME
    ~/.config/naomi/local/bin/python setup.py install  # specify the path to the python you installed above
    cd .. # ~/.config/naomi/local

    # The old version of pip expects to access pypi.org using http. PyPi now
    # requires ssl for all connections.
    NAME=pip
    VERSION=18.1
    VERNAME=$NAME-$VERSION
    CHKSUM=c0a292bd977ef590379a3f05d7b7f65135487b67470f6281289a94e015650ea1
    TARFILE=$VERNAME.tar.gz
    URL=https://files.pythonhosted.org/packages/45/ae/8a0ad77defb7cc903f09e551d88b443304a9bd6e6f124e75c0fbbf6de8f7/$TARFILE
    if [ ! -f $TARFILE ]; then
        wget $URL
    fi
    echo "$CHKSUM $TARFILE" | sha256sum -c -
    if [ $? -eq 0 ]; then
        echo "$TARFILE checksum verified"
    else
        echo "$TARFILE checksum failed" >&2
        exit 1
    fi
    tar xvzf $TARFILE
    cd $VERNAME # ~/.config/naomi/local/pip-18.1
    ~/.config/naomi/local/bin/python setup.py install  # specify the path to the python you installed above

    # install naomi & dependencies
    echo "Returning to $NAOMI_DIR"
    cd $NAOMI_DIR
    ~/.config/naomi/local/bin/pip install -r python_requirements.txt

    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "~/.config/naomi/local/bin/python $NAOMI_DIR/Naomi.py \$@" >> Naomi
fi
if [ $OPTION = "3" ]; then
    pip3 install -r python_requirements.txt
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
    echo $!
    exit 1
fi

if [ -z "$(which fstinfo)" ]; then
    echo "ERROR: openfst not installed"
    exit 1
fi

# Building and installing mitlm-0.4.2
echo
echo -e "\e[1;32mInstalling & Building mitlm-0.4.2...\e[0m"
cd ~/.config/naomi/sources
git clone https://github.com/mitlm/mitlm.git
cd mitlm
./autogen.sh
make
echo "Installing mitlm"
SUDO_COMMAND "sudo make install"
if [ $? -ne 0 ]; then
    echo $!
    exit 1
fi

# Building and installing CMUCLMTK
echo
echo -e "\e[1;32mInstalling & Building cmuclmtk...\e[0m"
cd ~/.config/naomi/sources
svn co https://svn.code.sf.net/p/cmusphinx/code/trunk/cmuclmtk/
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
git clone https://github.com/AdolfVonKleist/Phonetisaurus.git
cd Phonetisaurus
./configure --enable-python
make
echo "Installing Phonetisaurus"
SUDO_COMMAND "sudo make install"
cd python
cp -iv ../.libs/Phonetisaurus.so ./
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
    echo "ERROR: phonetisaurus-g2pfst does not exist"
    EXIT 1
fi

# Installing & Building sphinxbase
echo
echo -e "\e[1;32mBuilding and installing sphinxbase...\e[0m"
cd ~/.config/naomi/sources
git clone --recursive https://github.com/cmusphinx/pocketsphinx-python.git
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
    echo "ERROR: text2wfreq does not exist"
    EXIT 1
fi
if [ -z "$(which text2idngram)" ]; then
    echo "ERROR: text2idngram does not exist"
    EXIT 1
fi
if [ -z "$(which idngram2lm)" ]; then
    echo "ERROR: idngram2lm does not exist"
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

