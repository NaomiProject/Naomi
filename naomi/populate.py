#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import audioop
from blessings import Terminal
import collections
import feedparser
from getpass import getpass
import logging
import math
import os
import paths
import pytz
import re
import subprocess
import sys
import tempfile
import wave
import yaml
from . import i18n
# Import pluginstore so we can load and query plugins directly
from . import pluginstore
from . import audioengine


# AaronC 2018-09-14
# Colors
# This returns to whatever the default color is in the terminal
def normal_text(text=""):
    return t.normal + text

# this is for instructions
def instruction_text(text=""):
    return t.bold_blue + text

# This is for the brackets surrounding the icon
def icon_text(text=""):
    return t.bold_cyan + text

# This is for question text
def question_text(text=""):
    return t.bold_blue + text

# This is for the question icon
def question_icon(text=""):
    return t.bold_yellow + text

# This is for alert text
def alert_text(text=""):
    return t.bold_red + text

# This is for the alert icon
def alert_icon(text=""):
    return t.bold_cyan + text

# This is for listing choices available to choose from
def selection_text(text=""):
    return t.bold_cyan + text

# This is for displaying the default choice when there is a default
def default_text(text=""):
    return t.normal + text

# This is for the prompt after the default text
def default_prompt(text="// "):
    return t.bold_blue + text

# This is the color for the text as the user is entering a choice
def input_text(text=""):
    return t.normal + text

# This is text for a url
def url_text(text=""):
    return t.bold_cyan + t.underline + text + t.normal

# This is for a status message
def status_text(text=""):
    return t.bold_magenta + text

# This is a positive alert
def success_text(text=""):
    return t.bold_green + text

# AaronC
def _snr(input_bits, threshold, frames):
    rms = audioop.rms(b''.join(frames), int(input_bits / 8))
    if ((threshold > 0) and (rms > threshold)):
        return 20.0 * math.log(rms / threshold, 10)
    else:
        return 0

# Get a value from the profile, whether it exists or not
# If the value does not exist in the profile, returns None
def get_profile_var(profile, *args):
    response = profile
    for arg in args:
        try:
            response = response[arg]
        except KeyError:
            response = None
            # break out of the for loop
            break
    return response


def format_prompt(icon, prompt):
    if(icon == "!"):
        prompt = (
            icon_text('[')
            + alert_icon('!')
            + icon_text('] ')
            + question_text(prompt)
        )
    elif(icon == "?"):
        prompt = (
            icon_text('[')
            + question_icon('?')
            + icon_text('] ')
            + question_text(prompt)
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
def simple_input(prompt, default=None):
    prompt += ": "
    if(default):
        prompt += default_text(default) + default_prompt() + input_text()
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
    input_str = simple_input(prompt, get_profile_var(profile, var))
    if input_str:
        if cleanInput:
            input_str = cleanInput(input_str)
        profile[var] = input_str


# AaronC - This is currently used to clean phone numbers
def clean_number(s):
    return re.sub(r'[^0-9]', '', s)


# AaronC - This searches some standard places (/bin, /usr/bin, /usr/local/bin)
# for a program name.
# This could be updated to search the PATH, and also verify that execute
# permissions are set, but for right now this is a quick and dirty
# placeholder.
def check_program_exists(program):
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
def verify_location(place):
    feed = feedparser.parse('http://rss.wunderground.com/auto/rss_full/' +
                            place)
    numEntries = len(feed['entries'])
    if numEntries == 0:
        return False
    else:
        print(
            success_text(
                _("Location saved as") + " "
                + feed['feed']['description'][33:]
            )
        )
        return True


# If value exists in list, return the index
# of that value (+ 1 so that the first item
# does not return zero which is interpreted
# as false), otherwise return None
def check_for_value(_value, _list):
    try:
        temp = _list.index(_value) + 1
    except ValueError:
        temp = None
    return temp


def separator():
    print("")
    print("")
    print("")

def select_language(profile):
    global _, affirmative, negative
    language = get_profile_var(profile, "language")
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
            check_for_value(language, languages.keys())
        )
    ):
        once = True
        print("")
        print("")
        print("")
        print("    " + instruction_text(_("Language Selector")))
        print("")
        print("")
        for key in languages.keys():
            print "    " + selection_text(languages[key])
        print("")
        temp = simple_input(
            format_prompt(
                "?",
                _('Select Language')
            ),
            language
        ).lower().strip()
        if(check_for_value(temp[:2], [key[:2] for key in languages.keys()])):
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


def greet_user():
    print("")
    print("")
    print("")
    print(
        "    " + instruction_text(
            _("Hello, thank you for selecting me to be your personal assistant.")
        )
    )
    print("")
    print(
        "    " + instruction_text(
            _("Let's populate your profile.")
        )
    )
    print("")
    print(
        "    " + instruction_text(
            _("If, at any step, you would prefer not to enter the requested information")
        )
    )
    print(
        "    " + instruction_text(
            _("just hit 'Enter' with a blank field to continue.")
        )
    )
    print("")


def get_wakeword(profile):
    # my name
    simple_request(
        profile,
        'keyword',
        format_prompt(
            "?",
            _('First, what name would you like to call me by?').decode('utf-8')
        )
    )


def get_user_name(profile):
    # your name
    print(
        "    " + instruction_text(
            _("Now please tell me a little about yourself.")
        )
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


def get_email_info(profile):
    # email
    print(
        "    " + instruction_text(
            _("I can use an email account to send notifications to you.")
        )
    )
    print("    " + _("Alternatively, you can skip this step"))
    print("")
    # email
    try:
        temp = profile["email"]
    except KeyError:
        profile["email"] = {}
    # email imap
    profile["email"]["imap"] = simple_input(
        format_prompt(
            "?",
            _('Please enter your imap server as "server[:port]"')
        ),
        get_profile_var(profile, "email", "imap")
    )

    profile["email"]["address"] = simple_input(
        format_prompt(
            "?",
            _('What is your email address?')
        ),
        get_profile_var(profile, "email", "address")
    )

    # FIXME This needs to be anything but plaintext.
    # AaronC 2018-07-29 I've looked into this and the problem that needs to
    # be solved here is protection from a casual sort of hacker - like if
    # you are working on your configuration file and your friend is looking
    # over your shoulder and gets your password.
    # I suggest creating an encrypt/decrypt function that takes
    # both a string to encrypt/decrypt and an encryption function
    # name. Store the encryption function name with the password
    # so it can be decrypted using the same function used to encrypt
    # it.
    # This should allow the encryption method to be improved
    # incrementally while not forcing people to re-enter credentials
    # every time a new encryption method is added.
    prompt = _("What is your email password?") + ": "
    if(get_profile_var(profile,"email","password")):
        prompt += default_text(
            _("(just press enter to keep current password)")
        ) + default_prompt()
    temp = getpass(
        format_prompt(
            "?",
            prompt
        )
    )
    if(temp):
        profile['email']['password'] = temp


def get_phone_info(profile):
    print(
        "    " + instruction_text(
            _("I can use your phone number to send notifications to you.")
        )
    )
    print(
        "    "
        + _("Alternatively, you can skip this step")
    )
    print("")
    print(
        "    " + alert_text(
            _("No country codes!")
        ) + " " + instruction_text(
            _("Any dashes or spaces will be removed for you")
        )
    )
    print("")
    phone_number = clean_number(
        simple_input(
            format_prompt(
                "?",
                _("What is your Phone number?")
            ),
            get_profile_var(profile, 'phone_number')
        )
    )
    profile['phone_number'] = phone_number

    # carrier
    if(profile['phone_number']):
        separator()
        # If the phone number is blank, it makes no sense to ask
        # for the carrier.
        print(
            "    " + instruction_text(
                _("What is your phone carrier?")
            )
        )
        print(
            "    " + instruction_text(
                _("If you have a US phone number, ")
                + _("you can enter one of the following:")
            )
        )
        print(
            selection_text("    'AT&T', 'Verizon', 'T-Mobile' ") + alert_text(
                "(" + _("without the quotes") + ")."
            )
        )
        print("")
        print(
            "    " + instruction_text(
                _("If your carrier isn't listed or you have an international")
            )
        )
        print(
            "    " + instruction_text(
                _("number, go to") + " "
            ) + url_text("http://www.emailtextmessages.com")
        )
        print(
            "    " + instruction_text(
                _("and enter the email suffix for your carrier (e.g., for Virgin Mobile, enter ")
            )
        )
        print("    " + instruction_text(
                _("'vmobl.com'; for T-Mobile Germany, enter 't-d1-sms.de').")
            )
        )
        print("")
        carrier = simple_input(
            format_prompt(
                "?",
                _("What is your Carrier? ")
            ),
            get_profile_var(profile, "carrier")
        )
        if carrier == 'AT&T':
            profile['carrier'] = 'txt.att.net'
        elif carrier == 'Verizon':
            profile['carrier'] = 'vtext.com'
        elif carrier == 'T-Mobile':
            profile['carrier'] = 'tmomail.net'
        else:
            profile['carrier'] = carrier


def get_notification_info(profile):
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
            "    " + instruction_text(
                _("Would you prefer to have notifications sent by")
            )
        )
        print(
            "    " + instruction_text(
                _("email (E) or text message (T)?")
            )
        )
        print("")
        if(get_profile_var(profile, "prefers_email")):
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
                alert_text(
                    _("Please choose email (E) or text message (T)!")
                ),
                response
            )
        profile['prefers_email'] = (response == 'E')
    else:
        # if no email address is configured, just set this to false
        profile['prefers_email'] = False


def get_weather_location(profile):
    # Weather
    print(
        "    " + instruction_text(
            _("For weather information, please enter your 5-digit zipcode (e.g., 08544).")
        )
    )
    print(
        "    " + instruction_text(
            _("If you are outside the US, insert the name of the nearest big town/city.")
        )
    )
    print("")
    location = simple_input(
        format_prompt(
            "?",
            _("What is your location?")
        ),
        get_profile_var(profile, "location")
    )

    while location and not verify_location(location):
        print(
            alert_text(
                _("Weather not found.")
            ) + " " + instruction_text(
                _("Please try another location.")
            )
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


def get_timezone(profile):
        # timezone
    # FIXME AaronC 2018-07-26 Knowing the zip code, you should be
    # able to work out the time zone.
    # Also, sending me to a wikipedia page to configure this? Really?
    print(
        "    " + instruction_text(
            _("Please enter a timezone from the list located in the TZ*")
        )
    )
    print(
        "    " + instruction_text(
            _("column at")
        ) + " " + url_text(
            "http://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
        )
    )
    print("    " + instruction_text(_("or none at all.")))
    print("")
    tz = simple_input(
        format_prompt(
            "?",
            _("What is your timezone?")
        ),
        get_profile_var(profile, "timezone")
    )
    while tz:
        try:
            pytz.timezone(tz)
            profile['timezone'] = tz
            break
        except pytz.exceptions.UnknownTimeZoneError:
            print(alert_text(_("Not a valid timezone. Try again.")))
            tz = simple_input(
                format_prompt(
                    "?",
                    _("What is your timezone?")
                ),
                tz
            )


def get_stt_engine(profile):
    # Get a list of STT engines
    stt_engines = {
        "PocketSphinx": "sphinx",
        "DeepSpeech": "deepspeech-stt",
        "Wit.AI": "witai-stt",
        "Google Voice": "google",
        "Watson": "watson-stt",
        "Kaldi": "kaldigstserver-stt",
        "Julius": "julius-stt"
    }

    print(
        "    " + instruction_text(
            _("Please select a speech to text engine.")
        )
    )
    print("")
    try:
        response=stt_engines.keys()[stt_engines.values().index(get_profile_var(profile,'active_stt','engine'))]
    except (KeyError, ValueError):
        response = "PocketSphinx"
    once = False
    while not ((once) and (response in stt_engines.keys())):
        once = True
        response = simple_input(
            "    " + instruction_text(
                _("Available choices:")
            ) + " " + selection_text(
                ("%s. " % stt_engines.keys())
            ),
            response
        )
        print("")
        try:
            profile['active_stt']['engine'] = stt_engines[response]
        except KeyError:
            print(
                alert_text(
                    _("Unrecognized option.")
                )
            )
    print("")
    # Handle special cases here
    if(profile['active_stt']['engine'] == 'google'):
        # Set the api key (I'm not sure this actually works anymore,
        # need to test)
        key = simple_input(
            format_prompt(
                "!",
                _("Please enter your API key:")
            ),
            get_profile_var(profile, "keys", "GOOGLE_SPEECH")
        )
        print("")
        print("")
        print("")
    if(profile['active_stt']['engine'] == 'watson-stt'):
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
    if(profile['active_stt']['engine'] == 'kaldigstserver-stt'):
        try:
            temp = profile['kaldigstserver-stt']
        except KeyError:
            profile['kaldigstserver-stt'] = {}
        print(
            "    " + instruction_text(
                _("I need your Kaldi g-streamer server url to continue")
            )
        )
        default = "http://localhost:8888/client/dynamic/recognize"
        print(
            "    " + instruction_text(
                "(" + _("default is") + " "
            ) + url_text(
                "%s" % default
            ) + instruction_text(
                ")"
            )
        )
        print("")
        temp = get_profile_var(profile, "kaldigstserver-stt", "url")
        if(not temp):
            temp = default
        profile['kaldigstserver-stt']['url'] = simple_input(
            format_prompt(
                "!",
                _("Please enter your server url:")
            ),
            temp
        )
    if(profile['active_stt']['engine'] == 'julius-stt'):
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
            get_profile_var(profile, "julius", "hmmdefs")
        )
        # tiedlist
        profile["julius"]["tiedlist"] = simple_input(
            format_prompt(
                "!",
                _("Enter path to julius tied list")
            ),
            get_profile_var(profile, "julius", "tiedlist")
        )
        # lexicon
        profile["julius"]["lexicon"] = simple_input(
            format_prompt(
                "!",
                _("Enter path to julius lexicon")
            ),
            get_profile_var(profile, "julius", "lexicon")
        )
        # FIXME AaronC 2018-07-29 So I don't know if I need to check above to
        # see if the julius lexicon is a tar file or if I can just set this.
        # The instructions just say it is only needed if the lexicon is a tar
        # file, not that it will cause problems if included. I'm also not clear
        # if the above is a literal string or just indicates that the path to
        # something needs to be entered. Someone with experience setting up
        # Julius will need to finish this up.
        profile["julius"]["lexicon_archive_member"] = "VoxForge/VoxForgeDict"
    else:
        try:
            temp = profile["pocketsphinx"]
        except KeyError:
            profile["pocketsphinx"] = {}
        # AaronC 2018-07-29 Since pocketsphinx/phonetisaurus is assumed, make
        # this the default at the end
        # is the phonetisaurus program phonetisaurus-g2p (old version)
        # or phonetisaurus-g2pfst?
        phonetisaurus_executable = get_profile_var(
            profile,
            'pocketsphinx',
            'phonetisaurus_executable'
        )
        once = False
        while not((once) and (phonetisaurus_executable)):
            once = True
            # Let's check some standard places (this is crunchier than actually
            # using "find" but should work in most cases):
            if(not phonetisaurus_executable):
                if(check_program_exists('phonetisaurus-g2pfst')):
                    phonetisaurus_executable = 'phonetisaurus-g2pfst'
                elif(check_program_exists('phonetisaurus-g2p')):
                    phonetisaurus_executable = 'phonetisaurus-g2p'
            phonetisaurus_executable = simple_input(
                format_prompt(
                    "?",
                    _("What is the name of your phonetisaurus-g2p program?")
                ),
                phonetisaurus_executable
            )
        profile['pocketsphinx']['phonetisaurus_executable'] = phonetisaurus_executable
        # We have the following things to configure:
        #  hmm_dir - the default is "/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k"
        #          - if you install through the pocketsphinx-en-us debian apt package then it is "/usr/share/pocketsphinx/model/en-us/en-us"
        #          - if you install the latest pocketsphinx from source, it should be here: "~/pocketsphinx/model/en-us/en-us"
        #  fst_model -
        #          - the default is "~/phonetisaurus/g014b2b.fst"
        #          - if you install the latest CMUDict, then it will be at "~/CMUDict/train/model.fst"
        hmm_dir = get_profile_var(profile, 'pocketsphinx', 'hmm_dir')
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
            if(temp):
                hmm_dir = temp
        profile["pocketsphinx"]["hmm_dir"] = hmm_dir
        # fst_model
        fst_model = get_profile_var(profile, "pocketsphinx", "fst_model")
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


def get_tts_engine(profile):
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
    try:
        response=tts_engines.keys()[tts_engines.values().index(get_profile_var(profile,'tts_engine'))]
    except (KeyError, ValueError):
        response = "Festival"
    print(
        "    " + instruction_text(
            _("Please select a text to speech (TTS) engine.")
        )
    )
    print("")
    once = False
    while not ((once) and (response in tts_engines.keys())):
        once = True
        response = simple_input(
            format_prompt(
                "?",
                _("Available implementations: ") + selection_text(
                    "%s. " % tts_engines.keys()
                )
            ),
            response
        )
        try:
            profile['tts_engine'] = tts_engines[response]
        except KeyError:
            print(alert_text(_("Unrecognized option.")))
    print("")
    # Deal with special cases
    if(profile["tts_engine"] == "espeak-tts"):
        # tts_engine: espeak-tts
        print(
            "    " + instruction_text(
                _("If you would like to alter the espeak voice, you can use")
            )
        )
        print(
            "    " + instruction_text(
                _("the following options in your config file:")
            )
        )
        print("")
        print("    espeak-tts:")
        print("        voice: 'default+m3'   # optional")
        print("        pitch_adjustment: 40  # optional")
        print("        words_per_minute: 160 # optional")
    elif(profile["tts_engine"] == "festival-tts"):
        # tts_engine: festival-tts
        print(
            "    " + instruction_text(
                _("Use the festival command to set the default voice.")
            )
        )
    elif(profile["tts_engine"] == "flite-tts"):
        try:
            temp = profile["flite-tts"]
        except KeyError:
            profile["flite-tts"] = {}
        voices = subprocess.check_output(['flite', '-lv']).split(" ")[2:-1]
        print(
            "    " + instruction_text(
                _("Available voices:")
            )+ " " + selection_text(
                "%s. " % voices
            )
        )
        profile["flite-tts"]["voice"] = simple_input(
            format_prompt(
                "?",
                _("Select a voice")
            ),
            get_profile_var(profile, "flite-tts", "voice")
        )
    elif(profile["tts_engine"] == "pico-tts"):
        pass
    elif(profile["tts_engine"] == "ivona-tts"):
        print(
            "    " + instruction_text(
                _("You will now need to enter your Ivona account information.")
            )
        )
        print("")
        print(
            "    " + instruction_text(
                _("You will need to create an account at")
            )
        )
        print(
            "    " + url_text(
                "https://www.ivona.com/us/account/speechcloud/creation/"
            ) + " " + instruction_text(
                _("if you haven't already.")
            )
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
            get_profile_var(profile, "ivona-tts", "access_key")
        )
        profile["ivona-tts"]["secret_key"] = simple_input(
            format_prompt(
                "?",
                _("What is your Secret key?")
            ),
            get_profile_var(profile, "ivona-tts", "secret_key")
        )
        # ivona-tts voice
        temp = get_profile_var(profile, "ivona-tts", "voice")
        if(not temp):
            temp = "Brian"
        profile["ivona-tts"]["voice"] = simple_input(
            format_prompt(
                "?",
                _("Which voice do you want") + " " + default_text(
                    _("(default is Brian)")
                ) + question_text("?")
            ),
            temp
        )
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
            get_profile_var(profile, "mary-tts", "server")
        )
        profile["mary-tts"]["port"] = simple_input(
            format_prompt(
                "?",
                "Port?"
            ),
            get_profile_var(profile, "mary-tts", "port")
        )
        profile["mary-tts"]["language"] = simple_input(
            format_prompt(
                "?",
                _("Language?")
            ),
            get_profile_var(profile, "mary-tts", "language")
        )
        profile["mary-tts"]["voice"] = simple_input(
            format_prompt(
                "?",
                _("Voice?")
            ),
            get_profile_var(profile, "mary-tts", "voice")
        )


def get_beep_or_voice(profile):
    # Getting information to beep or not beep
    print(
        "    " + instruction_text(
            _("I have two ways to let you know I've heard you; Beep or Voice.")
        )
    )
    # If there are values for [active_stt][reply] and [active_stt][response]
    # then use them otherwise use beeps
    if(get_profile_var(profile, "active_stt", "reply")):
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
    while(
        (not response)
        or (response.lower()[:1] != 'b' and response.lower()[:1] != 'v')
    ):
        response = simple_input(
            alert_text(
                _("Please choose beeps (B) or voice (V)")
            )
        )
    if(response.lower()[:1] == "v"):
        print("")
        print("")
        print("")
        print(
            "    " + instruction_text(
                _("Type the words I should say after hearing my wake word: %s") % profile["keyword"]
            )
        )
        print("")
        areplyRespon = None
        while((not areplyRespon) or (areplyRespon.lower()[:1] != affirmative.lower()[:1])):
            areply = simple_input(
                format_prompt(
                    "?",
                    _("Reply")
                ),
                get_profile_var(profile, "active_stt", "reply")
            )
            print("")
            print(areply + " " + instruction_text(_("Is this correct?")))
            print("")
            areplyRespon = None
            while((not areplyRespon) or (not check_for_value(areplyRespon.lower()[:1], [affirmative.lower()[:1], negative.lower()[:1]]))):
                areplyRespon = simple_input(
                    format_prompt(
                        "?",
                        affirmative.upper()[:1] + "/" + negative.upper()[:1] + "?"
                    )
                )
        profile['active_stt']['reply'] = areply
        print("")
        print("")
        print("")
        print(
            "    " + instruction_text(
                _("Type the words I should say after hearing a command")
            )
        )
        aresponseRespon = None
        while((not aresponseRespon) or (aresponseRespon.lower()[:1] != affirmative.lower()[:1])):
            aresponse = simple_input(
                format_prompt(
                    "?",
                    _("Response")
                ),
                get_profile_var(profile, "active_stt", "response")
            )
            print("")
            print(aresponse + " " + instruction_text(_("Is this correct?")))
            print("")
            aresponseRespon = None
            while((not aresponseRespon) or (not check_for_value(aresponseRespon.lower()[:1], [affirmative.lower()[:1], negative.lower()[:1]]))):
                aresponseRespon = simple_input(
                    format_prompt(
                        "?",
                        affirmative.upper()[:1] + "/" + negative.upper()[:1] + "?"
                    )
                )
        profile['active_stt']['response'] = aresponse
    else:
        # If beeps are selected, must remove both reply and response
        profile['active_stt']['reply'] = ""
        profile['active_stt']['response'] = ""


def select_audio_engine(profile):
    # Audio Engine
    global audioengine_plugins
    audioengine_plugins=pluginstore.PluginStore(
        [os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )]
    )
    audioengine_plugins.detect_plugins()
    audioengines = [ae_info.name for ae_info in audioengine_plugins.get_plugins_by_category(category='audioengine')]

    print(instruction_text(_("Please select an audio engine.")))
    try:
        response = audioengines[audioengines.index(get_profile_var(profile,'audio_engine'))]
    except (ValueError):
        response = "pyaudio"
    once = False
    while not ((once) and (response in audioengines)):
        once=True
        response = simple_input(
            "    " + _("Available implementations:") + " " + selection_text(
                ("%s. " % audioengines)
            ),
            response
        )
    profile['audio_engine'] = response


def get_output_device(profile):
    # AaronC 2018-09-14 Initialize AudioEngine
    ae_info = audioengine_plugins.get_plugin(
        profile['audio_engine'],
        category='audioengine'
    )
    # AaronC 2018-09-14 Get a list of available output devices
    audio_engine = ae_info.plugin_class(ae_info, profile)
    output_devices = [device.slug for device in audio_engine.get_devices(
        device_type=audioengine.DEVICE_TYPE_OUTPUT
    )]
    output_device = get_profile_var(profile,"audio","output_device")
    if not output_device:
        output_device = audio_engine.get_default_device(output=True)
    heard = ""
    once = False
    while not ((once) and (heard == affirmative.lower()[:1])):
        print(instruction_text(_("Please choose an output device")))
        while not ((once) and (output_device in output_devices)):
            once = True
            output_device = simple_input(
                _("Available output devices:") + " " + selection_text(
                    ", ".join(output_devices)
                ),
                output_device
            )
        profile["audio"]["output_device"] = output_device
        # try playing a sound
        # FIXME Set the following defaults to what is in the
        # configuration file
        output_chunksize = 1024
        output_add_padding = False
        
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data","audio","beep_lo.wav")
        if(os.path.isfile(filename)):
            print(instruction_text(_("Testing device by playing a sound")))
            actual_output_device = audio_engine.get_device_by_slug(output_device)
            actual_output_device.play_file(
                filename,
                chunksize=output_chunksize,
                add_padding=output_add_padding
            )
            heard = simple_input(
                _("Were you able to hear the beep (%s/%s)?") % (affirmative.upper()[:1],negative.upper()[:1])
            ).lower().strip()[:1]
            if not (heard == affirmative.lower()[:1]):
                print(
                    instruction_text(
                        _("The volume on your device may be too low. You should be able to use 'alsamixer' to set the volume level.")
                    )
                )
                heard = simple_input(
                    instruction_text(
                        _("Do you want to continue and try to fix the volume later?")
                    )
                )
                if not (heard == affirmative.lower()[:1]):
                    once = False
        else:
            print(
                alert_text(
                    _("Can't locate wav file: %s") % filename
                )
            )
            print(
                instruction_text(
                    _("Skipping test")
                )
            )
            heard = affirmative.lower()[:1]


def get_input_device(profile):
    # AaronC 2018-09-14 Initialize AudioEngine
    ae_info = audioengine_plugins.get_plugin(
        profile['audio_engine'],
        category='audioengine'
    )
    # AaronC 2018-09-14 Get a list of available output devices
    audio_engine = ae_info.plugin_class(ae_info, profile)
    # AaronC 2018-09-14 Get a list of available input devices
    input_devices = [device.slug for device in audio_engine.get_devices(
        device_type=audioengine.DEVICE_TYPE_INPUT)]
    input_device = get_profile_var(profile,"audio","input_device")
    if not input_device:
        input_device = audio_engine.get_default_device(input=True)
    heard = ""
    once = False
    while not ((once) and (heard == affirmative.lower()[:1])):
        print(instruction_text(_("Please choose an input device")))
        while not ((once) and (input_device in input_devices)):
            once = True
            input_device = simple_input(
                _("Available input devices:") + " " + selection_text(
                    ", ".join(input_devices)
                ),
                input_device
            )
        profile["audio"]["input_device"] = input_device
        # try recording a sample
        while not(heard == affirmative.lower()[:1]):
            print(
                _("I will test your selection by recording your voice and playing it back to you.")
            )
            # FIXME AaronC Sept 16 2018
            # The following are defaults. They should be read
            # from the proper locations in the profile file if
            # they have been set.
            threshold = 10 # 10 dB
            input_chunks = 1024
            input_bits = 16
            input_channels = 1
            input_rate = 16000

            output_chunksize = 1024
            output_add_padding = False

            actual_input_device = audio_engine.get_device_by_slug(profile["audio"]["input_device"])
            actual_output_device = audio_engine.get_device_by_slug(profile["audio"]["output_device"])
            frames = collections.deque([],30)
            recording = False
            recording_frames = []
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data","audio","beep_hi.wav")
            if(os.path.isfile(filename)):
                actual_output_device.play_file(
                    filename,
                    chunksize=output_chunksize,
                    add_padding=output_add_padding
                )
            print(
                _("Please speak into the mic now")
            )
            for frame in actual_input_device.record(
                input_chunks,
                input_bits,
                input_channels,
                input_rate
            ):
                frames.append(frame)
                if not recording:
                    snr = _snr(input_bits, threshold, [frame])
                    if snr >= threshold:
                        print(
                            _("Started recording")
                        )
                        recording = True
                        recording_frames = list(frames)[-10:]
                    elif len(frames) >= frames.maxlen:
                        # Threshold not reached. Update.
                        soundlevel = float(audioop.rms("".join(frames), 2))
                        if (soundlevel < threshold):
                            threshold = soundlevel
                            print(
                                _("No sound detected. Setting threshold to %s") % threshold
                            )
                else:
                    recording_frames.append(frame)
                    if len(recording_frames) > 20:
                        # Check if we are below threshold again
                        last_snr = _snr(input_bits, threshold, recording_frames[-10:])
                        if (last_snr <= threshold) or (len(recording_frames) > 60):
                            # stop recording
                            recording = False
                            print(
                                _("Recorded %d frames") % len(recording_frames)
                            )
                            break
            if len(recording_frames) > 20:
                once = False
                replay = "y"
                while not ((once) and (replay != affirmative.lower()[:1])):
                    once = True
                    with tempfile.NamedTemporaryFile(mode='w+b') as f:
                        wav_fp = wave.open(f, 'wb')
                        wav_fp.setnchannels(input_channels)
                        wav_fp.setsampwidth(int(input_bits / 8))
                        wav_fp.setframerate(input_rate)
                        fragment = "".join(frames)
                        wav_fp.writeframes(fragment)
                        wav_fp.close()
                        actual_output_device.play_file(
                            f.name,
                            chunksize=output_chunksize,
                            add_padding=output_add_padding
                        )
                    heard = simple_input(
                        _("Did you hear yourself (%s/%s)?") % (affirmative.upper()[:1], negative.upper()[:1])
                    ).strip().lower()[:1]
                    if (heard == affirmative.lower()[:1]):
                        replay = negative.lower()[:1]
                    else:
                        replay = simple_input(
                            _("Replay?")
                        ).strip().lower()[:1]
                        if (replay == negative.lower()[:1]):
                            heard = simple_input(
                                instruction_text(
                                    _("Do you want to skip this test and continue?")
                                )
                            ).strip().lower()[:1]
                            if (heard == affirmative.lower()[:1]):
                                replay = negative.lower()[:1]
                            else:
                                once = False


def run(profile):
    #
    # AustinC; Implemented new UX for the population process.
    # For population blessings is used to handle colors,
    # formatting, & and screen isolation.
    #
    # For plugin & general use elsewhere, blessings or
    # coloredformatting.py can be used.
    #
    _logger = logging.getLogger(__name__)

    global t, _, negative, affirmative, audio_engine_plugins
    
    t = Terminal()

    select_language(profile)
    separator()
    
    greet_user()
    separator()
    
    get_wakeword(profile)
    separator()

    get_user_name(profile)
    separator()

    get_email_info(profile)
    separator()
    
    get_phone_info(profile)
    separator()
    
    get_notification_info(profile)
    separator()
    
    get_weather_location(profile)
    separator()
    
    get_timezone(profile)
    separator()
    
    get_stt_engine(profile)
    separator()

    get_tts_engine(profile)
    separator()
    
    get_beep_or_voice(profile)
    separator()
    
    select_audio_engine(profile)
    separator()
    
    get_output_device(profile)
    separator()
    
    get_input_device(profile)
    separator()
    
    # write to profile
    print(
        "    " + status_text(
            _("Writing to profile...")
        )
    )
    if not os.path.exists(paths.CONFIG_PATH):
        os.makedirs(paths.CONFIG_PATH)
    outputFile = open(paths.config("profile.yml"), "w")
    yaml.dump(profile, outputFile, default_flow_style=False)
    print("")
    print("")
    print("")
    print("    " + success_text(_("Done.")) + normal_text())


if __name__ == "__main__":
    print("This program can no longer be run directly.")
    print("Please run the Populate.py program from the")
    print("Naomi root directory.")
    subprocess.call(
        os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "Populate.py"
        )
    )
