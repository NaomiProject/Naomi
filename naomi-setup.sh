#!/bin/bash

#########################################
# Installing python and necessary packages
# for Naomi. This script will install python
# into the ~/.naomi/local/bin directory and
# install naomi & requirements in their
# respective directories.
#########################################
OPTION="0"
for var in "$@"; do
    if [ "$var" = "--virtualenv" ]; then
        OPTION="1"
    fi
    if [ "$var" = "--local" ]; then
        OPTION="2"
    fi
    if [ "$var" = "--primary" ]; then
        OPTION="3"
    fi
    if [ "$var" = "--help" ]; then
        echo "USAGE: $0 [--virtualenv | --local | --primary | --help]"
        echo
        echo "  --virtualenv - install Naomi using a virtualenv environment for Naomi"
        echo "                 (this is the recommended choice. You will need to issue"
        echo "                 'workon Naomi' before installing additional libraries"
        echo "                 for Naomi)"
        echo
        echo "  --local      - download, compile and install a special copy of Python 3"
        echo "                 for Naomi (does not work for all distros)"
        echo
        echo "  --primary    - use your primary Python 3 environment"
        echo "                 (this can be dangerous, it can lead to a broken python"
        echo "                 environment on your system, which other software may"
        echo "                 depend on. This is the simplest setup, but only recommended"
        echo "                 when Naomi is the primary program you intend to run on this"
        echo "                 computer. You will probably need to use the 'pip3' command"
        echo "                 to install additional libraries for Naomi.)"
        echo "                 USE AT YOUR OWN RISK!"
        echo
        echo "  --help       - Print this message and exit"
        exit 0
    fi
done
if [ $OPTION = "0" ]; then
    echo 'There are three methods to install Naomi:'
    echo
    echo '1) Use virtualenvwrapper to create a virtual Python 3 environment for Naomi (recommended)'
    echo '2) Download, compile, and install a local copy of Python for Naomi (may not work for some users)'
    echo '3) Use your primary Python 3 environment (this can be dangerous and can break other software on your system. It is only recommended for machines you intend to devote to running Naomi, like a virtual machine or Raspberry Pi)'
    echo
    while [ $OPTION != "1" ] && [ $OPTION != "2" ] && [ $OPTION != "3" ]; do
        read -e -p 'Please select: ' OPTION
        if [ $OPTION != "1" ] && [ $OPTION != "2" ] && [ $OPTION != "3" ]; then
            echo "Please choose 1, 2 or 3"
        fi
    done
fi
# Assume this program is in the main Naomi directory
# so we can save and return to it.
export NAOMI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "NAOMI_DIR = $NAOMI_DIR"
APT=0
if command -v apt-get > /dev/null 2>&1 ; then
    APT=1
fi
if [ $APT -eq 1 ]; then
    echo "Updating apt, preparing to install gettext, portaudio19-dev and libasound2-dev"
    echo "This operation may require your sudo password"
    # install dependencies
    sudo apt-get update
    # libssl-dev required to get the python _ssl module working
    sudo apt-get install gettext portaudio19-dev libasound2-dev -y
else
    echo "Please ensure that gettext, portaudio and libasound2 are installed on your system"
fi
if [ $OPTION == "1" ]; then
    echo 'VirtualEnv setup'
    if [ $APT -eq 1 ]; then
        echo 'Making sure you have the latest python, pip, python3 and pip3 installed on your system'
        sudo apt-get install python python-pip python3 python3-pip
    else
        echo "Please ensure that python, pip, python3 and pip3 are installed on your system"
    fi
    pip install --user virtualenvwrapper
    echo 'sourcing virtualenvwrapper.sh'
    #export VIRTUALENVWRAPPER_PYTHON=`which python3`
    export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv
    source ~/.local/bin/virtualenvwrapper.sh
    echo 'checking if Naomi virtualenv exists'
    workon Naomi > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo 'Naomi virtualenv does not exist. Creating.'
        PATH=$PATH:~/.local/bin mkvirtualenv -p python3 Naomi
        workon Naomi
    fi
    if [ `which pip` = $HOME/.virtualenvs/Naomi/bin/pip ]; then
        echo 'in the Naomi virtualenv'
        pip install -r python_requirements.txt
        deactivate
    else
        echo "Something went wrong, not in virtual environment..." >&2
        exit 1
    fi
    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    #echo "export VIRTUALENVWRAPPER_PYTHON=\`which python3\`" >> Naomi
    echo "export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv" >> Naomi
    echo "source ~/.local/bin/virtualenvwrapper.sh" >> Naomi
    echo "workon Naomi" >> Naomi
    echo "python $NAOMI_DIR/Naomi.py \$@" >> Naomi
    echo "deactivate" >> Naomi
fi
if [ $OPTION == "2" ] ; then
    if [ $APT -eq "1" ] ; then
        echo "Making sure you have GnuPG and dirmngr installed"
        sudo apt-get install libssl-dev libncurses5-dev gnupg dirmngr
    else
        echo "Please make sure you have libssl-dev, libncurses5-dev, GnuPG and dirmngr installed"
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
    gpg --list-keys $KEYID || gpg --keyserver keys.gnupg.net --recv-keys $KEYID
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

    # install naomi & dependancies
    echo "Returning to $NAOMI_DIR"
    cd $NAOMI_DIR
    ~/.naomi/local/bin/pip install -r python_requirements.txt

    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "~/.naomi/local/bin/python $NAOMI_DIR/Naomi.py \$@" >> Naomi
fi
if [ $OPTION == "3" ] ; then
    if [ $APT -eq 1 ]; then
        echo 'Making sure you have the latest python3 and pip3 installed on your system'
        sudo apt-get install python3 python3-pip
    else
        echo "Please ensure that python3 and pip3 are installed on your system"
    fi
    pip3 install -r python_requirements.txt
    # start the naomi setup process
    echo "#!/bin/bash" > Naomi
    echo "python3 $NAOMI_DIR/Naomi.py \$@" >> Naomi
fi
./compile_translations.sh
chmod a+x Naomi
echo "In the future, run $NAOMI_DIR/Naomi to start Naomi"
./Naomi --repopulate
