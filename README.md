Jasper2fork
=============
The current plan is to use discord.gg
Discord:  https://discord.gg/d4bK4 



Slack channel: https://jasper2fork.slack.com 
Email chrobione@gmail.com for access.


appear: https://appear.in/jasper2fork


So this is the fork of the J2 fork of thejasperproject, thank you for all the work to this point and hope to merge back up with yall.



Client code for the Jasper voice computing platform. Jasper is an open source platform for developing always-on, voice-controlled applications.


This fork is a work in progress and as such if you find something missing/broke/anything please make a pull request with tests would be nice, or file an issue.

There are plenty of things that need help.  If you have to ask your not looking at the code.

Documentation is the first thing.


If you have a jasper working install then you should only need to do the following:

`sudo pip install slugify mad`

and for msgfmt - install do `sudo apt install gettext`

There are more instructions coming for how to get multi-language going.



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
