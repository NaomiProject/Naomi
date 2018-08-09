# PocketSphinx setup

These instructions are for installing pocketsphinx on Debian 9 (Stretch). I will also test on Raspbian Stretch and update this message when finished. These instructions should translate to other distros pretty easily, just changing "apt install" for your package manager.

## test the microphone ("hello, can you hear me?")

You want to make sure that the level indicator at the bottom of the screen goes up to about 60% when you are speaking. Use alsamixer to adjust your recording and playback levels.

Also, play it back and make sure the audio does not contain any hissing or popping.

We will train PocketSphinx to transcribe this audio later in these instructions.
```
sudo apt install alsa-utils
alsamixer
arecord -vv -r16000 -fS16_LE -c1 -d3 test.wav
aplay test.wav
```
# Install PocketSphinx
## Build and install openfst:
```
sudo apt install gcc g++ make python-pip autoconf libtool
wget http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.6.7.tar.gz
tar -zxvf openfst-1.6.7.tar.gz
cd openfst-1.6.7
autoreconf -i
./configure --enable-static --enable-shared --enable-far --enable-lookahead-fsts --enable-const-fsts --enable-pdt --enable-ngram-fsts --enable-linear-fsts --prefix=/usr
make
sudo make install
cd
```

## Build and install mitlm-0.4.2:
```
sudo apt install git gfortran autoconf-archive
git clone https://github.com/mitlm/mitlm.git
cd mitlm
vi configure.ac add AC_CONFIG_MACRO_DIRS([m4])
vi Makefile.am  add ACLOCAL_AMFLAGS = -I m4
autoreconf -i
./configure
make
sudo make install
cd
```
## Build and install Phonetisaurus:
```
git clone https://github.com/AdolfVonKleist/Phonetisaurus.git
cd Phonetisaurus
./configure --enable-python
make
sudo make install
cd python
cp -iv ../.libs/Phonetisaurus.so ./
sudo python setup.py install
cd
```
## Build and install sphinxbase-0.8:

Here we download the latest sphinxbase from github, configure it, and make sure that alsa was picked up in the configuration by saving the output from configure to a log file, then search for "alsa". You should get a result like:
* checking alsa/asoundlib.h usability... yes
* checking alsa/asoundlib.h presence... yes
* checking for alsa/asoundlib.h... yes
Then we build and install the result.
```
sudo apt install swig libasound2-dev bison
git clone https://github.com/cmusphinx/sphinxbase.git
cd sphinxbase
./autogen.sh
./configure |& tee configure.log
grep -i 'alsa' configure.log
make
sudo make install
cd
```
## Build and install pocketsphinx-0.8:
```
git clone https://github.com/cmusphinx/pocketsphinx.git
cd pocketsphinx
./autogen.sh
./configure
make
sudo make install
cd
which pocketsphinx_continuous
```
## Install python PocketSphinx libary
Download the old .egg file, convert it to wheel, and install it with pip.
```
sudo pip install wheel
wget https://pypi.python.org/packages/e1/e8/448fb4ab687ecad1be8708d152eb7ed69455be7740fc5899255be2228b52/pocketsphinx-0.1.3-py2.7-linux-x86_64.egg#md5=1b4ce66e44f53d23c981e789f84edf29`
python -m wheel convert pocketsphinx-0.1.3-py2.7-linux-x86_64.egg
pip install ./pocketsphinx-0.1.3-cp27-none-linux_x86_64.whl
```
## Build and install CMUCLMTK
```
sudo apt install subversion
svn co https://svn.code.sf.net/p/cmusphinx/code/trunk/cmuclmtk/
cd cmuclmtk
./autogen.sh
make
sudo make install
sudo ldconfig
cd
sudo pip install cmuclmtk
```
## Get the CMUDict
```
mkdir CMUDict
cd CMUDict
wget https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict
cat cmudict.dict | perl -pe 's/([0-9]+)//;s/\s+/ /g;s/^\s+//;s/\s+$//; @_=split(/\s+/); $w=shift(@_);$_=$w."\t".join(" ",@_)."\n";' > cmudict.formatted.dict
phonetisaurus-train --lexicon cmudict.formatted.dict --seq2_del
```
## Test:
```
vi test_reference.txt
<s> hello can you hear me </s>
```
### Create test.vocab
```
text2wfreq < test_reference.txt | wfreq2vocab > test.vocab
```
### Create test.idngram
```
text2idngram -vocab test.vocab -idngram test.idngram < test_reference.txt
```
### Create test.lm
```
idngram2lm -vocab_type 0 -idngram test.idngram -vocab test.vocab -arpa test.lm
```
### Create test.formatted.dict
```
phonetisaurus-g2pfst --model=/home/jasper/CMUDict/train/model.fst --nbest=1 --beam=1000 --thresh=99.0 --accumulate=true --pmass=0.85 --nlog_probs=false --wordlist=./test.vocab > test.dict
cat test.dict | sed -rne '/^([[:lower:]])+\s/p' | perl -pe 's/([0-9])+//g;s/\s+/ /g;@_=split(/\s+/);$w=shift(@_);$_=$w."\t".join(" ",@_)."\n";' > test.formatted.dict
```
## Test with audio file:
`pocketsphinx_continuous -hmm ~/pocketsphinx/model/en-us/en-us -lm ./test.lm -dict ./test.formatted.dict -samprate 16000/8000/48000 -infile test.wav 2>/dev/null`

## Test with microphone:
`pocketsphinx_continuous -hmm ~/pocketsphinx/model/en-us/en-us -lm ./test.lm -dict ./test.formatted.dict -samprate 16000/8000/48000 -inmic yes 2>/dev/null`
