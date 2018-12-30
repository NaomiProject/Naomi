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
sudo apt-get install libssl-dev gettext libncurses5-dev portaudio19-dev libasound2-dev -y

# installing python 3.5.3
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
wget https://files.pythonhosted.org/packages/37/1b/b25507861991beeade31473868463dad0e58b1978c209de27384ae541b0b/setuptools-40.6.3.zip
unzip setuptools-40.6.3.zip
cd setuptools-40.6.3
~/.naomi/local/bin/python setup.py install  # specify the path to the python you installed above
cd .. # ~/.naomi/local

# The old version of pip expects to access pypi.org using http. PyPi now
# requires ssl for all connections.
wget https://files.pythonhosted.org/packages/45/ae/8a0ad77defb7cc903f09e551d88b443304a9bd6e6f124e75c0fbbf6de8f7/pip-18.1.tar.gz
tar xvzf pip-18.1.tar.gz
cd pip-18.1 # ~/.naomi/local/pip-18.1
~/.naomi/local/bin/python setup.py install  # specify the path to the python you installed above

# install naomi & dependancies
echo "Returning to $NAOMI_DIR"
cd $NAOMI_DIR
~/.naomi/local/bin/pip install -r python_requirements.txt
./compile_translations.sh

# start the naomi setup process
echo "#!/bin/bash" > Naomi
echo "~/.naomi/local/bin/python $NAOMI_DIR/Naomi.py \$@" >> Naomi
chmod a+x Naomi
echo "In the future, run $NAOMI_DIR/Naomi to start Naomi"
./Naomi --repopulate

