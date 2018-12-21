#!/bin/bash

#########################################
# Installing python and necessary packages
# for Naomi. This script will install python
# into the ~/.naomi/local/bin directory and
# install naomi & requirements in their
# respective directories.
#########################################
# Assume this program is in the main Naomi directory
# so we can save and return to it.
export NAOMI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "NAOMI_DIR = $NAOMI_DIR"
echo "Updating apt, preparing to install libssl-dev, gettext, portaudio19-dev and libasound2-dev"
# install dependencies
sudo apt-get update
# libssl-dev required to get the python _ssl module working
sudo apt-get install libssl-dev gettext portaudio19-dev libasound2-dev -y

# installing python 2.7.13
echo 'Installing python 3.5.3 to ~/.naomi/local'
mkdir -p ~/.naomi/local
cd ~/.naomi/local
wget https://www.python.org/ftp/python/3.5.3/Python-3.5.3.tgz
tar xvzf Python-3.5.3.tgz
cd Python-3.5.3
./configure
make
make altinstall prefix=~/.naomi/local  # specify local installation directory
ln -s ~/.naomi/local/bin/python3.5 ~/.naomi/local/bin/python
cd ..  # ~/.naomi/local

# install setuptools and pip for package management
echo 'Installing setuptools'
wget https://pypi.python.org/packages/source/s/setuptools/setuptools-0.6c11.tar.gz#md5=7df2a529a074f613b509fb44feefe74e
tar xvzf setuptools-0.6c11.tar.gz
cd setuptools-0.6c11 # ~/.naomi/local/setuptools-0.6c11
~/.naomi/local/bin/python setup.py install  # specify the path to the python you installed above
cd .. # ~/.naomi/local

# The old version of pip expects to access pypi.org using http. PyPi now
# requires ssl for all connections.
wget https://bootstrap.pypa.io/get-pip.py
~/.naomi/local/bin/python get-pip.py  # specify the path to the python you installed above

# install naomi & dependancies
echo "Returning to $NAOMI_DIR"
cd $NAOMI_DIR
~/.naomi/local/bin/pip install -r python_requirements.txt
./compile_translations.sh

# start the naomi setup process
echo "#!/bin/bash" > Naomi
echo "~/.naomi/local/bin/python $NAOMI_DIR/Naomi.py \$\@" >> Naomi
chmod a+x Naomi
echo "In the future, run $NAOMI_DIR/Naomi to start Naomi"
./Naomi --repopulate

