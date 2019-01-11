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

for var in "$@"; do
    if [ "$var" = "--virtualenv" ]; then
        OPTION="1"
    fi
    if [ "$var" = "--local-compile" ]; then
        OPTION="2"
    fi
    if [ "$var" = "--system" ]; then
        OPTION="3"
    fi
    if [ "$var" = "--help" ]; then
        echo "USAGE: $0 [--virtualenv | --local | --primary | --help]"
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
echo "NAOMI_DIR = $NAOMI_DIR"

if [ $APT -eq 1 ]; then
    SUDO_COMMAND "sudo apt-get update"
    # install dependencies
    SUDO_COMMAND "sudo apt-get install gettext portaudio19-dev libasound2-dev -y"
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
if [ $OPTION = "1" ]; then
    echo 'VirtualEnv setup'
    if [ $APT -eq 1 ]; then
        echo 'Making sure you have the latest python, pip, python3 and pip3 installed on your system'
        SUDO_COMMAND "sudo apt-get install python python-pip python3 python3-pip"
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
fi
if [ $OPTION = "2" ]; then
    if [ $APT -eq "1" ] ; then
        # libssl-dev required to get the python _ssl module working
        echo "Making sure you have GnuPG and dirmngr installed"
        SUDO_COMMAND "sudo apt-get install libssl-dev libncurses5-dev gnupg dirmngr"
    else
        ERROR=""
        if [[ $(CHECK_PROGRAM gpg) -ne "0" ]]; then
            ERROR="${ERROR} gnupg program gpg not found${NL}"
        fi
        if [[ $(CHECK_PROGRAM dirmngr) -ne "0" ]]; then
            ERROR="${ERROR} dirmngr program dirmngr not found${NL}"
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
        fi
    fi
    # installing python 3.5.3
    echo 'Installing python 3.5.3 to ~/.naomi/local'
    mkdir -p ~/.naomi/local
    cd ~/.naomi/local
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
    make altinstall prefix=~/.naomi/local  # specify local installation directory
    ln -s ~/.naomi/local/bin/python3.5 ~/.naomi/local/bin/python
    cd ..  # ~/.naomi/local

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
    ~/.naomi/local/bin/python setup.py install  # specify the path to the python you installed above
    cd .. # ~/.naomi/local

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
    cd $VERNAME # ~/.naomi/local/pip-18.1
    ~/.naomi/local/bin/python setup.py install  # specify the path to the python you installed above

    # install naomi & dependencies
    echo "Returning to $NAOMI_DIR"
    cd $NAOMI_DIR
    ~/.naomi/local/bin/pip install -r python_requirements.txt

    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "~/.naomi/local/bin/python $NAOMI_DIR/Naomi.py \$@" >> Naomi
fi
if [ $OPTION = "3" ]; then
    if [ $APT -eq 1 ]; then
        echo 'Making sure you have the latest python3 and pip3 installed on your system'
        SUDO_COMMAND "sudo apt-get install python3 python3-pip"
    else
        ERROR=""
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
    pip3 install -r python_requirements.txt
    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "python3 $NAOMI_DIR/Naomi.py \$@" >> Naomi
fi
if [ $OPTION = "4" ]; then
    echo 'Exiting'
    exit 0
fi
./compile_translations.sh
chmod a+x Naomi
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
    echo "  ~/.naomi/local/bin/python"
    echo "  ~/.naomi/local/bin/pip"
    echo
fi
echo "In the future, run $NAOMI_DIR/Naomi to start Naomi"
echo
./Naomi --repopulate
