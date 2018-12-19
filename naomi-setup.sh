#!/bin/bash

#########################################
# Installing python and necessary packages
# for Naomi. This script will install python
# into the ~/local/bin directory and install
# naomi & requirements in their respective
# directories.
#########################################
# Assume this program is in the main Naomi directory
# so we can save and return to it.
export NAOMI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "NAOMI_DIR = $NAOMI_DIR"
# install dependencies
sudo apt-get update
# libssl1.0-dev required to get the python _ssl module working
sudo apt-get install libssl-dev portaudio19-dev libasound2-dev -y

# installing python 2.7.13
echo 'Installing python 2.7.13 to ~/.naomi/local'
mkdir -p ~/.naomi/local
cd ~/.naomi/local
wget http://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz
tar xvzf Python-2.7.13.tgz
cd Python-2.7.13
./configure
make
make altinstall prefix=~/.naomi/local  # specify local installation directory
ln -s ~/.naomi/local/bin/python2.7 ~/.naomi/local/bin/python
cd ..  # ~/.naomi/local
# install setuptools and pip for package management
echo 'Installing setuptools'
wget http://pypi.python.org/packages/source/s/setuptools/setuptools-0.6c11.tar.gz#md5=7df2a529a074f613b509fb44feefe74e
tar xvzf setuptools-0.6c11.tar.gz
cd setuptools-0.6c11 # ~/.naomi/local/setuptools-0.6c11
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
echo "~/.naomi/local/bin/python $NAOMI_DIR/Naomi.py $@" >> Naomi
chmod a+x Naomi
./Naomi

