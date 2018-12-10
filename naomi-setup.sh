#!/bin/bash

#########################################
# Installing python and necessary packages for Naomi.
# This script will install python into the ~/local/bin
# directory, and install naomi & requirments
# in their respective directories
#########################################

# installing python 2.7.3
mkdir -p ~/local
wget http://www.python.org/ftp/python/2.7.3/Python-2.7.3.tgz
tar xvzf Python-2.7.3.tgz
cd Python-2.7.3
./configure
make
make altinstall prefix=~/local  # specify local installation directory
ln -s ~/local/bin/python2.7 ~/local/bin/python
cd ..

# install setuptools and pip for package management
wget http://pypi.python.org/packages/source/s/setuptools/setuptools-0.6c11.tar.gz#md5=7df2a529a074f613b509fb44feefe74e
tar xvzf setuptools-0.6c11.tar.gz
cd setuptools-0.6c11
~/local/bin/python setup.py install  # specify the path to the python you installed above
cd ..
wget http://pypi.python.org/packages/source/p/pip/pip-1.2.1.tar.gz#md5=db8a6d8a4564d3dc7f337ebed67b1a85
tar xvzf pip-1.2.1.tar.gz
cd pip-1.2.1
~/local/bin/python setup.py install  # specify the path to the python you installed above

# install framework
#cd ~
#apt-get update
#apt-get install nano python-pip python-pyaudio python3-pyaudio -y
#pip install pyalsaaudio -y

# install naomi & dependancies
#cd ~
#wget https://github.com/NaomiProject/Naomi/archive/v2.1.tar.gz
#tar xvzf v2.1.tar.gz
#mv v2.1 Naomi
~/Naomi/pip install -r python_requirements.txt


# start the naomi setup process
cd Naomi
python Populate.py
