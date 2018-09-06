#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import feedparser
from getpass import getpass
import os
import paths
import pytz
import re
import sys
import yaml
# The following is necessary because when this program is run as a standalone
# program it can't do a relative import, so you have to add the current
# directory to the path.
if __name__ == '__main__' and __package__ is None:
    os.sys.path.append(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )
import i18n
import subprocess
from blessings import Terminal

t = None

# AaronC
# Get a value from the profile, whether it exists or not
# If the value does not exist in the profile, returns None
def get_profile_var(profile,*args):
    response = profile
    for arg in args:
        try:
            response = response[arg]
        except KeyError:
            response = None
            # break out of the for loop
            break
    return response
    
# AaronC - 
def format_prompt(icon,prompt):
    if(icon == "!"):
        prompt = (
            t.bold_white + '['
            + t.bold_cyan + '!'
            + t.bold_white + '] '
            + prompt
        )
    elif(icon == "?"):
        prompt = (
            t.bold_white + '['
            + t.bold_yellow + '?'
            + t.bold_white + '] '
            + prompt
        )
    return prompt

# AaronC - simple_input is a lot like raw_input, just adds
# a colon and space at the end. If a default value is
# passed in, then adds that to the end followed by two slashes.
# This used to be one of several standard ways of indicating
# a default. If you want to override the behavior, of course,
# then that can be done here.
# Part of the purpose is to provide a way of overriding
# raw_input easily without hunting down every reference
def simple_input(prompt, default = None):
    prompt += ": "
    if(default):
        prompt += default + "// "
    sys.stdout.write(prompt)
    response = raw_input()
    # if the user pressed enter without entering anything,
    # set the response to default
    if(default and not response):
         response = default
    return response.strip()

# AaronC - simple_request is more complicated, and populates
# the profile variable directly
def simple_request(profile, var, prompt, cleanInput=None):
    input = simple_input(prompt, get_profile_var(profile, var))
    if input:
        if cleanInput:
            input = cleanInput(input)
        profile[var] = input

# AaronC - This is currently used to clean phone numbers
def clean_number(s):
    return re.sub(r'[^0-9]', '', s)

# AaronC - This searches some standard places (/bin, /usr/bin, /usr/local/bin)
# for a program name.
# This could be updated to search the PATH, and also verify that execute
# permissions are set, but for right now this is a quick and dirty
# placeholder.
def CheckProgramExists(program):
    standardlocations = ['/usr/local/bin', '/usr/bin', '/bin']
    response = False
    for location in standardlocations:
        if(os.path.isfile(os.path.join(location, program))):
            response = True
    return response

# FIXME
# AaronC - Location. This uses weather underground for verification, which
# I am not sure is really cool being as how it is a .com and all.
# The good thing about using it is that you can either enter
# a zip code or the closest city. The odd bit is that it shows you a
# description of the location you have chosen, then stores the raw
# input. I would have expected it to be stored as a lat/lon or something
# especially since the weather plugin uses Yahoo weather rather than
# weather underground. Personally, I would prefer to use NOAA for weather
# in the US and the World Weather Information Service (but I am open to
# suggestions) for other locations, and allow others to add country/
# region specific weather sites as needed, but that is a whole other
# project.
# On the privacy side, I think it should be necessary to alert the user
# any time their information is going to be shared with a new website,
# and keep a list of authorized websites/services.
def verifyLocation(place):
    feed = feedparser.parse('http://rss.wunderground.com/auto/rss_full/' +
                            place)
    numEntries = len(feed['entries'])
    if numEntries == 0:
        return False
    else:
        print( 
            _("Location saved as ")
            + feed['feed']['description'][33:]
        )
        return True

# If value exists in list, return the index
# of that value, otherwise return None
def CheckForValue(value, list):
    try:
        temp = list.index(value)
    except ValueError:
        temp = None
    return temp

def run(profile):
    #
    # AustinC; Implemented new UX for the population process.
    # For population blessings is used to handle colors,
    # formatting, & and screen isolation.
    #
    # For plugin & general use elsewhere, blessings or
    # coloredformatting.py can be used.
    #
    global t, _
    t = Terminal()
    
    language = get_profile_var(profile,"language")
    if(not language):
        language = 'en-US'
        profile["language"] = language
    translations = i18n.parse_translations(paths.data('locale'))
    translator = i18n.GettextMixin(translations, profile)
    _ = translator.gettext        
    #
    # AustinC; can't use français due to the special char "ç"
    # it breaks due to it being out of range for ascii
    #
    languages = {
        u'en-US': u'EN-English',
        u'fr-FR': u'FR-Français',
        u'de-DE': u'DE-Deutsch'
    }
    once = False
    while not (
        (
            once
        )and(
            CheckForValue(language,languages.keys())
        )
    ):
        once = True
        print("")
        print("")
        print("")
        print("    " + t.bold_blue + _("Language Selector"))
        print("")
        print("")
        for key in languages.keys():
            print t.bold_white + "    " + languages[key]
        print("")
        temp = simple_input(
            format_prompt(
                "?",
                _('Select Language')
            ),
            language
        ).lower().strip()
        if(CheckForValue(temp[:2],[key[:2] for key in languages.keys()])):
            for key in languages.keys():
                if(temp[:2] == key[:2]):
                    language = key
                    break
        if(language.lower()[:2] == 'en'):
            language = 'en-US'
            affirmative = 'yes'
            negative = 'no'
        elif(language.lower()[:2] == 'fr'):
            language = 'fr-FR'
            affirmative = 'oui'
            negative = 'non'
        elif(language.lower()[:2] == 'de'):
            language = 'de-DE'
            affirmative = "ja"
            negative = "nein"

    profile['language'] = language
    translations = i18n.parse_translations(paths.data('locale'))
    translator = i18n.GettextMixin(translations, profile)
    _ = translator.gettext
    print("")
    print("")
    print("")
    print("    "+t.bold_blue(
        _("Hello, thank you for selecting me to be your personal assistant.")
    ))
    print("")
    print("    "+t.bold_blue(
        _("Let's populate your profile.")
    ))
    print("")
    print("    "+t.bold_blue(
        _("If, at any step, you would prefer not to enter the requested information")
    ))
    print("    "+t.bold_blue(
        _("just hit 'Enter' with a blank field to continue.")
    ))
    print("")

    # my name
    simple_request(
        profile,
        'keyword',
        format_prompt( 
            "?",
            _('First, what name would you like to call me by?').decode('utf-8')
        )
    )
    print("")
    print("")
    print("")

    # your name
    print("    " + t.bold_blue +
        _("Now please tell me a little about yourself.")
    )
    print("")
    simple_request(
        profile,
        "first_name",
        format_prompt( 
            "?",
            _("What is your first name?")
        )
    )
    print("")
    simple_request(
        profile,
        'last_name',
        format_prompt( 
            "?",
            _('What is your last name?').decode('utf-8')
        )
    )
    print("")
    print("")
    print("")

    # email
    
    print(
        "    "
        + t.bold_blue
        + _("I can use an email account to send notifications to you.")
    )
    print("")
    print("    " + _("Alternatively, you can skip this step"))
    # email
    try:
        temp = profile["email"]
    except KeyError:
        profile["email"] = {}
    # email imap
    profile["email"]["imap"]=simple_input(
        format_prompt( 
            "?",
            _('Please enter your imap server as "server[:port]"')
        ),
        get_profile_var(profile,"email","imap")
    )
    
    profile["email"]["address"]=simple_input(
        format_prompt( 
            "?",
            _('What is your email address?')
        ),
        get_profile_var(profile,"email","address")
    )
    
    # FIXME This needs to be anything but plaintext.
    # AaronC 2018-07-29 I've looked into this and the problem that needs to
    # be solved here is protection from a casual sort of hacker - like if
    # you are working on your configuration file and your friend is looking
    # over your shoulder and gets your password. I know that there are
    # standard ways of dealing with this. I wonder how Thunderbird/Firefox
    # deals with this.
    temp = getpass(
        format_prompt(
            "?",
            _('What is your email password?') + ': '
        )
    )
    if( temp ):
        profile['email']['password'] = temp
    print("")
    print("")
    print("")
    
    print(
        "    "
        + t.bold_blue
        + _("I can use your phone number to send notifications to you.")
    )
    print(
        "    "
        + _("Alternatively, you can skip this step")
    )
    print("")
    print(
        "    "
        + t.red
        + _("No country codes!")
        + t.bold_blue + " "
        + _("Any dashes or spaces will be removed for you")
    )
    print("")
    phone_number = clean_number(
        simple_input(
            format_prompt(
                "?",
                _("What is your Phone number?")
            ),
            get_profile_var(profile,'phone_number')
        )
    )
    profile['phone_number'] = phone_number

    # carrier
    if(profile['phone_number']):
        print("")
        print("")
        print("")
        # If the phone number is blank, it makes no sense to ask
        # for the carrier.
        print(
            "    "
            + t.bold_blue
            + _("What is your phone carrier?")
        )
        print(
            "    "
            + _("If you have a US phone number, ")
            + _("you can enter one of the following:")
        )
        print(
            "    'AT&T', 'Verizon', 'T-Mobile' "
            + t.red
            + "(" + _("without the quotes") +")."
        )
        print("")
        print(
            "    "
            + t.bold_blue
            + _("If your carrier isn't listed or you have an international")
        )
        print(
            "    "
            + _("number, go to") + " "
            + t.bold_yellow + "http://www.emailtextmessages.com"
        )
        print(
            "    "
            + t.bold_blue
            + _("and enter the email suffix for your carrier (e.g., for Virgin Mobile, enter ")
        )
        print("    " + _("'vmobl.com'; for T-Mobile Germany, enter 't-d1-sms.de')."))
        print("")
        carrier = simple_input(
            format_prompt( 
                "?",
                _("What is your Carrier? ")
            ),
            get_profile_var(profile,"carrier")
        )
        if carrier == 'AT&T':
            profile['carrier'] = 'txt.att.net'
        elif carrier == 'Verizon':
            profile['carrier'] = 'vtext.com'
        elif carrier == 'T-Mobile':
            profile['carrier'] = 'tmomail.net'
        else:
            profile['carrier'] = carrier
        print("")

    # Notifications
    # Used by hackernews and news plugins.
    # Neither of which attempt to send a text message,
    # both check to see if you have an email address
    # in your profile, then if you have "prefers_email"
    # selected, it will send an article to you via email,
    # otherwise it does not attempt to send anything to you.
    
    # if the user has entered an email address but no phone number
    # go ahead and assume "prefers email"
    if((profile['email']['address']) and not (profile['phone_number'])):
        profile["prefers_email"] = True
    # if both email address and phone number are configured, ask
    # which the user prefers
    elif((profile['phone_number']) and (profile['email']['address'])):
        print(
            "    "
            + t.bold_blue
            + _("Would you prefer to have notifications sent by")
        )
        print(
            "    "
            + _("email (E) or text message (T)?")
        )
        print("")
        if(get_profile_var(profile,"prefers_email")):
            temp = 'E'
        else:
            temp = "T"
        response = simple_input(
            format_prompt( 
                "?",
                _("Email (E) or Text message (T)?")
            ),
            temp
        )
        
        while not response or (response[:1] != 'E' and response[:1] != 'T'):
            print("")
            response = simple_input(
                t.red
                + _("Please choose email (E) or text message (T)!")
                + t.bold_white,
                response
            )
        profile['prefers_email'] = (response == 'E')
    else:
        # if no email address is configured, just set this to false
        profile['prefers_email'] = False

    # Weather
    print("")
    print("")
    print("")
    print(
        "    "
        + t.bold_blue
        + _("For weather information, please enter your 5-digit zipcode (e.g., 08544).")
    )
    print(
        "    "
        + _("If you are outside the US, insert the name of the nearest big town/city.")
    )
    print("")
    location = simple_input(
        format_prompt( 
            "?",
            _("What is your location?")
        ),
        get_profile_var(profile,"location")
    )
    
    while location and not verifyLocation(location):
        print(
            t.red
            + _("Weather not found.") + " "
            + _("Please try another location.")
        )
        location = simple_input(
            format_prompt( 
                "?",
                _("What is your location?")
            ),
            location
        )
    if location:
        profile['location'] = location
    print("")
    print("")
    print("")

    # timezone
    # FIXME AaronC 2018-07-26 Knowing the zip code, you should be
    # able to work out the time zone.
    # Also, sending me to a wikipedia page to configure this? Really?
    print(
        "    "
        + t.bold_blue
        + _("Please enter a timezone from the list located in the TZ*")
    )
    print(
        "    "
        + _("column at") + " "
        + t.bold_yellow
        + "http://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
    )
    print("    " + t.bold_blue + _("or none at all."))
    print("")
    tz = simple_input(
        format_prompt( 
            "?",
            _("What is your timezone?")
        ),
        get_profile_var(profile,"timezone")
    )
    while tz:
        try:
            pytz.timezone(tz)
            profile['timezone'] = tz
            break
        except pytz.exceptions.UnknownTimeZoneError:
            print(t.red+_("Not a valid timezone. Try again."))
            tz = simple_input(
                format_prompt( 
                    "?",
                    _("What is your timezone?")
                ),
                tz
            )
    print("")
    print("")
    print("")

    # Get a list of STT engines
    stt_engines = {
        "PocketSphinx": "sphinx",
        "DeepSpeech": "deepspeech-stt",
        "Google Voice": "google",
        "Watson": "watson-stt",
        "Kaldi": "kaldigstserver-stt",
        "Julius": "julius-stt"
    }

    print(
        "    "
        + t.bold_blue
        + _("If you would like to choose a specific speech to text(STT) engine, please specify which!")
    )
    print("")
    response = "PocketSphinx"
    for engine in stt_engines:
        if (get_profile_var(profile,'stt_engine')==stt_engines[engine]):
            response = engine
            break
    response = simple_input(
        "    "
        + _("Available implementations:") + " "
        + t.yellow + ("%s. " % stt_engines.keys()) + t.bold_white,
        response
    )
    print("")
    if (response in stt_engines.keys()):
        profile['stt_engine'] = response
    else:
        if response:
            print(
                t.red
                + _("Unrecognized option.")
            )
        print(
            t.bold_white
            + _("Setting speech to text engine to ")
            + t.yellow
            + "Pocketsphinx."
            + t.bold_white
        )
        profile['stt_engine'] = 'sphinx'
    print("")
    print("")
    print("")
    # Handle special cases here
    if(profile['stt_engine'] == 'google'):
        # Set the api key (I'm not sure this actually works anymore,
        # need to test)
        key = simple_input(
            format_prompt( 
                "!",
                _("Please enter your API key:")
            ),
            get_profile_var(profile,"keys","GOOGLE_SPEECH")
        )
        print("")
        print("")
        print("")
    if(profile['stt_engine'] == 'watson-stt'):
        profile["watson_stt"] = {}
        username = simple_input(
            format_prompt( 
                "!",
                _("Please enter your watson username:")
            )
        )
        profile["watson_stt"]["username"] = username
        # FIXME AaronC 2018-07-29 - another password. Not as crucial as
        # protecting the user's email password but still...
        profile["watson_stt"]["password"] = getpass(
            _("Please enter your watson password:")
        )
        print("")
        print("")
        print("")
    if(profile['stt_engine'] == 'kaldigstserver-stt'):
        try:
            temp = profile['kaldigstserver-stt']
        except KeyError:
            profile['kaldigstserver-stt'] = {}
        print(
            "    "
            + t.bold_blue
            + _("I need your Kaldi g-streamer server url to continue")
        )
        default = "http://localhost:8888/client/dynamic/recognize"
        print(
            "    ("
            + _("default is")
            + t.yellow + " %s)" % default
        )
        print("")
        temp = get_profile_var(profile,"kaldigstserver-stt","url")
        if(not temp):
            temp = default
        profile['kaldigstserver-stt']['url'] = simple_input(
            format_prompt( 
                "!",
                _("Please enter your server url:")
            ),
            temp
        )
        print("")
        print("")
        print("")
    if(profile['stt_engine'] == 'julius-stt'):
        # stt_engine: julius
        # julius:
        #     hmmdefs:  '/path/to/your/hmmdefs'
        #     tiedlist: '/path/to/your/tiedlist'
        #     lexicon:  '/path/to/your/lexicon.tgz'
        #     lexicon_archive_member: 'VoxForge/VoxForgeDict'
        #           only needed if lexicon is a tar/tar.gz archive
        try:
            temp = profile["julius"]
        except KeyError:
            profile["julius"] = {}
        # hmmdefs
        profile["julius"]["hmmdefs"] = simple_input(
            format_prompt( 
                "!",
                _("Enter path to julius hmm defs")
            ),
            get_profile_var(profile,"julius","hmmdefs")
        )
        # tiedlist
        profile["julius"]["tiedlist"] = simple_input(
            format_prompt( 
                "!",
                _("Enter path to julius tied list")
            ),
            get_profile_var(profile,"julius","tiedlist")
        )
        # lexicon
        profile["julius"]["lexicon"] = simple_input(
            format_prompt( 
                "!",
                _("Enter path to julius lexicon")
            ),
            get_profile_var(profile,"julius","lexicon")
        )
        # FIXME AaronC 2018-07-29 So I don't know if I need to check above to
        # see if the julius lexicon is a tar file or if I can just set this.
        # The instructions just say it is only needed if the lexicon is a tar
        # file, not that it will cause problems if included. I'm also not clear
        # if the above is a literal string or just indicates that the path to
        # something needs to be entered. Someone with experience setting up
        # Julius will need to finish this up.
        profile["julius"]["lexicon_archive_member"] = "VoxForge/VoxForgeDict"
        print("")
        print("")
        print("")
    else:
        try:
            temp = profile["pocketsphinx"]
        except KeyError:
            profile["pocketsphinx"] = {}
        # AaronC 2018-07-29 Since pocketsphinx/phonetisaurus is assumed, make
        # this the default at the end
        # is the phonetisaurus program phonetisaurus-g2p (old version)
        # or phonetisaurus-g2pfst?
        phonetisaurus_executable = get_profile_var(profile,'pocketsphinx','phonetisaurus_executable')
        once = False
        while not((once) and (phonetisaurus_executable)):
            once = True
            # Let's check some standard places (this is crunchier than actually
            # using "find" but should work in most cases):
            if(not phonetisaurus_executable):
                if(CheckProgramExists('phonetisaurus-g2pfst')):
                    phonetisaurus_executable = 'phonetisaurus-g2pfst'
                elif(CheckProgramExists('phonetisaurus-g2p')):
                    phonetisaurus_executable = 'phonetisaurus-g2p'
            phonetisaurus_executable = simple_input(
                format_prompt( 
                    "?",
                    _("What is the name of your phonetisaurus-g2p program?")
                ),
                phonetisaurus_executable
            )
        profile['pocketsphinx']['phonetisaurus_executable'] = phonetisaurus_executable
        print("")
        print("")
        print("")
        # We have the following things to configure:
        #  hmm_dir - the default for kara is "/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k"
        #          - if you install through the pocketsphinx-en-us debian apt package then it is "/usr/share/pocketsphinx/model/en-us/en-us"
        #          - if you install the latest pocketsphinx from source, it should be here: "~/pocketsphinx/model/en-us/en-us"
        #  fst_model -
        #          - the default for kara is "~/phonetisaurus/g014b2b.fst"
        #          - if you install the latest CMUDict, then it will be at "~/CMUDict/train/model.fst"
        hmm_dir=get_profile_var(profile,'pocketsphinx','hmm_dir')
        once = False
        while not(once and hmm_dir):
            once = True
            # The hmm_dir should be under the user's home directory
            # in the "~/pocketsphinx/model/en-us/en-us" directory
            if(not hmm_dir):
                if(os.path.isdir(os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
                ))):
                    hmm_dir = os.path.join(
                        os.path.expanduser("~"),
                        "pocketsphinx",
                        "model",
                        "en-us",
                        "en-us"
                    )
                elif(os.path.isdir("/usr/share/pocketsphinx/model/en-us/en-us")):
                    hmm_dir = "/usr/share/pocketsphinx/model/en-us/en-us"
                elif(os.path.isdir("/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k")):
                    hmm_dir = "/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k"
            temp = simple_input(
                format_prompt( 
                    "!",
                    _("Please enter the path to your hmm directory")
                ),
                hmm_dir
            )
            if( temp ):
                hmm_dir = temp
        profile["pocketsphinx"]["hmm_dir"] = hmm_dir
        # fst_model
        fst_model = get_profile_var(profile,"pocketsphinx","fst_model")
        once = False
        while not (once and fst_model):
            once = True
            if(not fst_model):
                if(phonetisaurus_executable == "phonetisaurus-g2pfst"):
                    if(os.path.isfile(os.path.join(
                        os.path.expanduser("~"),
                        "cmudict",
                        "train",
                        "model.fst"
                    ))):
                        fst_model = os.path.join(
                            os.path.expanduser("~"),
                            "cmudict",
                            "train",
                            "model.fst"
                        )
                elif(phonetisaurus_executable == "phonetisaurus-g2p"):
                    if(os.path.isfile(os.path.join(
                        os.path.expanduser("~"),
                        "phonetisaurus",
                        "g014b2b.fst"
                    ))):
                        fst_model = os.path.join(
                            os.path.expanduser("~"),
                            "phonetisaurus",
                            "g014b2b.fst"
                        )
            fst_model = simple_input(
                format_prompt( 
                    "!",
                    _("Please enter the path to your fst model")
                ),
                fst_model
            )
        profile["pocketsphinx"]["fst_model"] = fst_model
    print("")
    print("")
    print("")

    # Text to speech information
    tts_engines = {
        "eSpeak": "espeak-tts",
        "Festival": "festival-tts",
        "Flite": "flite-tts",
        "Pico": "pico-tts",
        "Google": "google-tts",
        "Ivona": "ivona-tts",
        "Mary": "mary-tts"
    }
    response = "Festival"
    for engine in tts_engines:
        if(get_profile_var(profile,"tts_engine")==tts_engines[engine]):
            response = engine
    print(
        "    "
        + t.bold_blue
        + _(
            "If you would like to choose a specific text to speech (TTS) engine,"
        )
    )
    print("    " + _("please specify which."))
    print("")
    response = simple_input(
        format_prompt(
            "?",
            t.bold_white + _("Available implementations: ")
            + t.yellow + ("%s. " % tts_engines.keys()) +t.bold_white
        ),
        response
    )
    if(response in tts_engines.keys()):
        profile['tts_engine'] = tts_engines[response]
    else:
        print(
            t.red+_("Unrecognized option.") +
            t.bold_white+_("Setting text to speech engine to") + " " +
            t.yellow+"Festival."
        )
        profile['tts_engine'] = 'festival-tts'
        print("")
        print("")
        print("")
    # Deal with special cases
    if(profile["tts_engine"] == "espeak-tts"):
        # tts_engine: espeak-tts
        print(t.bold_blue+"    If you would like to alter the espeak voice, you can use")
        print("    the following options in your config file:")
        print("")
        print("    espeak-tts:")
        print("        voice: 'default+m3'   # optional")
        print("        pitch_adjustment: 40  # optional")
        print("        words_per_minute: 160 # optional")
        print("")
        print("")
        print("")
    elif(profile["tts_engine"] == "festival-tts"):
        # tts_engine: festival-tts
        print(t.bold_blue+"    Use the festival command to set the default voice.")
        print("")
        print("")
        print("")
    elif(profile["tts_engine"] == "flite-tts"):
        try:
            temp = profile["flite-tts"]
        except KeyError:
            profile["flite-tts"] = {}
        voices = subprocess.check_output(['flite','-lv']).split(" ")[2:-1]
        print(
            "    "
            + _("Available voices: ")
            + t.yellow + "%s. " % voices
        )
        profile["flite-tts"]["voice"]=simple_input(
            format_prompt( 
                "?",
                _("Select a voice")
            ),
            get_profile_var(profile,"flite-tts","voice")
        )
        print("")
        print("")
        print("")
    elif( profile["tts_engine"]=="pico-tts" ):
        pass
    elif(profile["tts_engine"] == "ivona-tts"):
        print(
            "    "
            + t.bold_blue
            + _("You will now need to enter your Ivona account information.")
        )
        print("")
        print(
            "    "
            + _("You will need to create an account at")
        )
        print(
            "    " + t.yellow
            + "https://www.ivona.com/us/account/speechcloud/creation/"
            + " " + t.bold_blue + _("if you haven't already.")
        )
        print("")
        try:
            temp = profile["ivona-tts"]
        except KeyError:
            profile["ivona-tts"] = {}
        profile["ivona-tts"]["access_key"] = simple_input(
            format_prompt( 
                "?",
                _("What is your Access key?")
            ),
            get_profile_var(profile,"ivona-tts","access_key")
        )
        profile["ivona-tts"]["secret_key"] = simple_input(
            format_prompt( 
                "?",
                _("What is your Secret key?")
            ),
            get_profile_var(profile,"ivona-tts","secret_key")
        )
        # ivona-tts voice
        temp = get_profile_var(profile,"ivona-tts","voice")
        if(not temp):
            temp="Brian"
        profile["ivona-tts"]["voice"] = simple_input(
            format_prompt( 
                "?",
                _("Which voice do you want")+" "+t.yellow+_("(default is Brian)")+t.bold_white+"?"
            ),
            temp
        )
        print("")
        print("")
        print("")
    elif(profile["tts_engine"] == "mary-tts"):
        try:
            temp = profile["mary-tts"]
        except KeyError:
            profile["mary-tts"] = {}
        profile["mary-tts"]["server"] = simple_input(
            format_prompt( 
                "?",
                _("Server?")
            ),
            get_profile_var(profile,"mary-tts","server")
        )
        profile["mary-tts"]["port"] = simple_input(
            format_prompt( 
                "?",
                "Port?"
            ),
            get_profile_var(profile,"mary-tts","port")
        )
        profile["mary-tts"]["language"] = simple_input(
            format_prompt( 
                "?",
                _("Language?")
            ),
            get_profile_var(profile,"mary-tts","language")
        )
        profile["mary-tts"]["voice"] = simple_input(
            format_prompt( 
                "?",
                _("Voice?")
            ),
            get_profile_var(profile,"mary-tts","voice")
        )
        print("")
        print("")
        print("")
    # Getting information to beep or not beep
    print(
        "    "
        + t.bold_blue
        + _("I have two ways to let you know I've heard you; Beep or Voice.")
    )
    # If there are values for [active-stt][reply] and [active-stt][response]
    # then use them otherwise use beeps
    if(get_profile_var(profile, "active-stt", "reply")):
        temp = "V"
    else:
        temp = "B"
    response = simple_input(
        format_prompt( 
            "?",
            _("(B) for beeps or (V) for voice.")
        ),
        temp
    )
    while not response or (response.lower()[:1] != 'b' and response.lower()[:1] != 'v'):
        response = simple_input(
            t.red + _("Please choose beeps (B) or voice (V):") + t.bold_white
        )
    if(response.lower()[:1] is "v"):
        print("")
        print("")
        print("")
        print(
            "    "
            + t.bold_blue
            + _("Type the words I should say after hearing my wake word: %s") % profile["keyword"]
        )
        print("")
        areplyRespon = None
        while(areplyRespon.lower()[:1] != affirmative.lower()[:1]):
            areply = simple_input(
                format_prompt( 
                    "?",
                    "Reply"
                ),
                get_profile_var(profile,"active_stt","response")
            )
            print("")
            print(areply + t.bold_blue +" " + _("Is this correct?"))
            print("")
            while(not CheckForValue(areplyRespon.lower()[:1],[affirmative.lower()[:1],negative.lower()[:1]])):
                areplyRespon = simple_input(
                    format_prompt( 
                        "?",
                        affirmative.upper()[:1] + "/" + negative.upper()[:1] +"?"
                    )
                )
        profile['active_stt'] = {'reply': areply}
        print("")
        print("")
        print("")
        print(
            "    "
            + t.bold_blue
            + _("Type the words I should say after hearing a command")
        )
        aresponseRespon = None
        while(aresponseRespon.lower()[:1] != affirmative.lower()[:1]):
            aresponse = simple_input(
                format_prompt( 
                    "?",
                    _("Response")
                ),
                get_profile_var(profile,"active_stt","response")
            )
            print("")
            print(aresponse + t.bold_blue+" Is this correct?")
            print("")
            aresponseRespon = simple_input(
                format_prompt( 
                    "?",
                    affirmative.upper()[:1] + "/" + negative.upper()[:1] + "?"
                )
            )
        profile['active_stt'] = {'response': aresponse}
        print("")
        print("")
        print("")

    # write to profile
    print(
        "    "
        + t.bold_magenta + _("Writing to profile...")
    )
    if not os.path.exists(paths.CONFIG_PATH):
        os.makedirs(paths.CONFIG_PATH)
    outputFile = open(paths.config("profile.yml"), "w")
    yaml.dump(profile, outputFile, default_flow_style=False)
    print("")
    print("")
    print("")
    print("    " + t.bold_green + _("Done."))


if __name__ == "__main__":
    configfile = paths.config('profile.yml')
    if os.path.exists(configfile):
        with open(configfile, "r") as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    run(config)
