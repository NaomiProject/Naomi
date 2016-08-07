# Jasper2fork
[![Build Status](https://travis-ci.org/chrobione/Jasper2fork.svg?branch=jasper-dev)](https://travis-ci.org/chrobione/Jasper2fork) [![Coverage Status](https://img.shields.io/coveralls/chrobione/Jasper2fork.svg)](https://coveralls.io/r/chrobione/Jasper2fork) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/ee172c51010b469491bf437538cfa5ec)](https://www.codacy.com/app/chrobione/Jasper2fork?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=chrobione/Jasper2fork&amp;utm_campaign=Badge_Grade)
=============
The current plan is to use [discord](https://discord.gg/VEQmm) and Github for the day to day comms.

This is the fork of the J2 fork of thejasperproject, thank you for all the work to this point and hope to merge back up with yall on the main project.

Client code for the Jasper voice computing platform. Jasper is an open source platform for developing always-on, voice-controlled applications.

This fork is a work in progress and as such if you find something missing/broke/anything please make a pull request with tests would be nice, or file an issue.

There are plenty of things that need help.  If you have to ask your not looking at the code.

The documentation is the first thing.


If you have a jasper working install then you should only need to do the following:

sudo pip install --upgrade setuptools .
sudo pip install -r Jasper2fork/python_requirements.txt .

For more information, see the [WIKI](https://github.com/chrobione/Jasper2fork/wiki)



Here is a sample of the ~/.jasper/profile.yml
```
#J2 and jasper-dev branch profile.yml full example.
# Celluar Carrier http://www.emailtextmessages.com for more info exampl is Verizon.
carrier: vtext.com
# First name how the computer will address you
first_name: Yourname
# Last or Surname
last_name: Yourlastname

# Warning GMAIL CONFIG IS UNSECURE PLAIN TEXT STORED PASSWORD
gmail_address: email@gmail.com
gmail_password: xxxxxxxx
# This for weather forecast can acces City or zipcode
weather:
  location: 'POSTALCODE'
# Phone number you can receive text messages on.  
phone_number: 'xxxxxxxxxxx'

# This sends alerts. false = text message. true = email message.
prefers_email: false

# Time zone so when you ask for the time it tells you correctly
timezone: America/Denver

# Passive engine configuration (keyword detection)
#stt_passive_engine: x

# Speech To Text engine with witai-stt example
stt_engine: witai-stt
witai-stt:
  access_token:    X

# Text To Speech Config default is espeak-tts
# uncomment to use
#tts_engine: mary-tts

#mary-tts:
#  server: 'tts.mattcurry.com'
#  port: '59125'
#  language: 'en_US'
#  voice: 'cmu-slt-hsmm'

# Audio configuration
# uncomment to use
#audio_engine: pyaudio

#Mic configuration
#input_device:

#Speak out configuration
#output_device:

# Wolfram Alpha Integration
#keys:
  #WOLFRAMALPHA:   X
```
