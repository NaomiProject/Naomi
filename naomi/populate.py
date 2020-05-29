#!/usr/bin/env python2
# -*- coding: utf-8 -*-
try:
    import audioop
    from blessings import Terminal
    import collections
    from . import commandline
    import feedparser
    from getpass import getpass
    import math
    import os
    from . import paths
    import platform
    from . import profile
    import pytz
    import re
    from .run_command import run_command
    import tempfile
    import wave
    from . import i18n
    # Import pluginstore so we can load and query plugins directly
    from . import pluginstore
    from . import audioengine
except SystemError:
    print("This program can no longer be run directly.")
    print("Please run the Populate.py program from the")
    print("Naomi root directory.")
    quit()


# AaronC = for detecting audio. Switch to using VAD engine.
def _snr(input_bits, threshold, frames):
    rms = audioop.rms(b''.join(frames), int(input_bits / 8))
    if ((threshold > 0) and (rms > threshold)):
        return 20.0 * math.log(rms / threshold, 10)
    else:
        return 0


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
    feed = feedparser.parse(
        'http://rss.wunderground.com/auto/rss_full/' + place
    )
    numEntries = len(feed['entries'])
    if numEntries == 0:
        return False
    else:
        print(
            interface.success_text(
                " ".join([
                    _("Location saved as"),
                    feed['feed']['description'][33:]
                ])
            )
        )
        return True


# check and make sure the user has walked through the instructions
# and configured both a STT and TTS engine.
# check and make sure an audio engine is configured before allowing
# populate.py to continue.
def precheck():
    global _, affirmative, negative
    if not profile.check_profile_var_exists(["active_stt", "engine"]):
        if(not interface.simple_yes_no(
            _("Have you set up at least one stt (speech to text) engine?")
        )):
            print(interface.instruction_text(" ".join([
                _("You will need to choose and configure at least"),
                _("one stt engine. Instructions are available at")
            ])))
            print(interface.url_text(
                "https://projectnaomi.com/docs/configuration/stt.html")
            )
            print(interface.instruction_text(" ".join([_(
                "Please re-run Naomi after you have configured an STT engine."
            )])))
            quit()
    if not profile.check_profile_var_exists(["tts_engine"]):
        if(not interface.simple_yes_no(
            _("Have you set up at least one tts (text to speech) engine?")
        )):
            print(interface.instruction_text(" ".join([
                _("You will need to choose and configure at least"),
                _("one tts engine. Instructions are available at")
            ])))
            print(interface.url_text(
                "https://projectnaomi.com/docs/configuration/tts.html"
            ))
            print(interface.instruction_text(" ".join([
                _("Please re-run Naomi after you have configured a TTS engine.")
            ])))
            quit()
    audioengines = get_audio_engines()
    while(len(audioengines) < 1):
        print(
            interface.alert_text(
                _("You do not appear to have any audio engines configured.")
            )
        )
        print(interface.default_text())
        print(_("You should either install the pyaudio or pyalsaaudio"))
        print(_("python modules. Otherwise Naomi will be unable to speak"))
        print(_("or listen."))
        print("")
        print(_("Both programs have prerequisites that can most likely"))
        print(_("be installed using your package manager"))
        if not interface.simple_yes_no(_("Would you like me to check again?")):
            print(_("Can't continue, so quitting"))
            quit()
        audioengines = get_audio_engines()


def greet_user():
    print("    " + interface.instruction_text(
        _("Hello, thank you for selecting me to be your personal assistant.")
    ))
    print("")
    print(
        "    " + interface.instruction_text(
            _("Let's populate your profile.")
        )
    )
    print("")
    print(
        "    " + interface.instruction_text(" ".join([
            _("If, at any step, you would prefer not"),
            _("to enter the requested information")
        ]))
    )
    print(
        "    " + interface.instruction_text(_("just hit '"))
               + interface.strong_text(_("Enter"))
               + interface.instruction_text(_("' with a blank field to continue."))
    )
    print("")


def get_wakeword():
    # my name
    keyword = profile.get_profile_var(["keyword"], ["Naomi"])
    profile.set_profile_var(
        ["keyword"],
        interface.simple_input(
            interface.format_prompt(
                "?",
                _("First, what name would you like to call me by?")
            ),
            keyword, True
        )
    )


def get_user_name():
    # your name
    print(
        "    " + interface.instruction_text(
            _("Now please tell me a little about yourself.")
        )
    )
    print("")
    interface.simple_request(
        ["first_name"],
        interface.format_prompt(
            "?",
            _("What is your first name?")
        )
    )
    print("")
    interface.simple_request(
        ['last_name'],
        interface.format_prompt(
            "?",
            _('What is your last name?')
        )
    )


def get_email_info():
    # email
    print(
        "    " + interface.instruction_text(
            _("I can use an email account to send notifications to you.")
        )
    )
    print("    " + _("Alternatively, you can skip this step"))
    print("")
    # email
    profile.set_profile_var(
        ["email", "imap"],
        interface.simple_input(
            interface.format_prompt(
                "?",
                _('Please enter your imap server as "server[:port]"')
            ),
            profile.get_profile_var(["email", "imap"])
        )
    )

    profile.set_profile_password(
        ["email", "address"],
        interface.simple_input(
            interface.format_prompt(
                "?",
                _('What is your email address?')
            ),
            profile.get_profile_password(["email", "address"])
        )
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
    if(profile.get_profile_password(["email", "address"])):
        prompt = _("What is your email password?") + ": "
        if (profile.get_profile_password(["email", "password"])):
            prompt += interface.default_text(
                _("(just press enter to keep current password)")
            ) + interface.default_prompt()
        temp = interface.simple_password(
            interface.format_prompt(
                "?",
                prompt
            )
        )
        if(temp):
            profile.set_profile_password(['email', 'password'], temp)


def get_phone_info():
    print(
        "    " + interface.instruction_text(
            _("I can use your phone number to send notifications to you.")
        )
    )
    print("".join([
        "    ",
        _("Alternatively, you can skip this step")
    ]))
    print("")
    print(
        "    " + interface.alert_text(
            _("No country codes!")
        ) + " " + interface.instruction_text(
            _("Any dashes or spaces will be removed for you")
        )
    )
    print("")
    phone_number = clean_number(
        interface.simple_input(
            interface.format_prompt(
                "?",
                _("What is your Phone number?")
            ),
            profile.get_profile_var(['phone_number'])
        )
    )
    profile.set_profile_var(['phone_number'], phone_number)

    # carrier
    if(profile.get_profile_var(['phone_number'])):
        interface.separator()
        # If the phone number is blank, it makes no sense to ask
        # for the carrier.
        print(
            "    " + interface.instruction_text(
                _("What is your phone carrier?")
            )
        )
        print(
            "    " + interface.instruction_text(" ".join([
                _("If you have a US phone number,"),
                _("you can enter one of the following:")
            ]))
        )
        print(
            interface.choices_text(
                "    'AT&T', 'Verizon', 'T-Mobile' "
            ) + interface.alert_text(
                "(" + _("without the quotes") + ")."
            )
        )
        print("")
        print(
            "    " + interface.instruction_text(
                _("If your carrier isn't listed or you have an international")
            )
        )
        print(
            "    " + interface.instruction_text(
                _("number, go to") + " "
            ) + interface.url_text("http://www.emailtextmessages.com")
        )
        print(
            "    " + interface.instruction_text(" ".join([
                _("and enter the email suffix for your carrier"),
                _("(e.g., for Virgin Mobile, enter 'vmobl.com';"),
                ""
            ]))
        )
        print(
            "    " + interface.instruction_text(
                _("for T-Mobile Germany, enter 't-d1-sms.de').")
            )
        )
        print("")
        carrier = interface.simple_input(
            interface.format_prompt(
                "?",
                _("What is your Carrier? ")
            ),
            profile.get_profile_var(["carrier"])
        )
        if carrier == 'AT&T':
            profile.set_profile_var(['carrier'], 'txt.att.net')
        elif carrier == 'Verizon':
            profile.set_profile_var(['carrier'], 'vtext.com')
        elif carrier == 'T-Mobile':
            profile.set_profile_var(['carrier'], 'tmomail.net')
        else:
            profile.set_profile_var(['carrier'], carrier)


def get_notification_info():
    # Notifications
    # Used by hackernews and news plugins.
    # Neither of which attempt to send a text message,
    # both check to see if you have an email address
    # in your profile, then if you have "prefers_email"
    # selected, it will send an article to you via email,
    # otherwise it does not attempt to send anything to you.

    # if the user has entered an email address but no phone number
    # go ahead and assume "prefers email"
    if(
        (
            profile.get_profile_password(
                ['email', 'address']
            )
        ) and not (
            profile.get_profile_var(
                ['phone_number']
            )
        )
    ):
        profile.set_profile_var(["prefers_email"], True)
    # if both email address and phone number are configured, ask
    # which the user prefers
    elif(
        profile.get_profile_var(
            ['phone_number']
        ) and profile.get_profile_password(
            ['email', 'address']
        )
    ):
        email_choice = _("email").lower()[:1]
        text_choice = _("text").lower()[:1]
        print(
            "    " + interface.instruction_text(
                _("How would you prefer to have notifications sent?")
            )
        )
        print("")
        if(profile.get_profile_var(["prefers_email"])):
            temp = email_choice
        else:
            temp = text_choice
        response = interface.simple_input(
            interface.format_prompt(
                "?",
                _("Email ({e}) or Text message ({t})?").format(
                    e=email_choice.upper(),
                    t=text_choice.upper()
                )
            ),
            temp
        ).lower()

        while not response or (
            (
                response[:1] != email_choice
            )and(
                response[:1] != text_choice
            )
        ):
            print("")
            response = interface.simple_input(
                interface.alert_text(
                    _(
                        "Please choose email ({e}) or text message ({t})!"
                    ).format(
                        e=email_choice.upper(),
                        t=text_choice.upper()
                    )
                ),
                response
            )
        profile.set_profile_var(
            ['prefers_email'],
            (response.lower()[:1] == email_choice)
        )
    else:
        # if no email address is configured, just set this to false
        profile.set_profile_var(['prefers_email'], False)


def get_weather_location():
    # Weather
    print(
        "    " + interface.instruction_text(" ".join([
            _("For weather information, please enter your 5-digit zipcode"),
            _("(e.g., 08544).")
        ]))
    )
    print(
        "    " + interface.instruction_text(" ".join([
            _("If you are outside the US,"),
            _("insert the name of the nearest big town/city.")
        ]))
    )
    print("")
    location = interface.simple_input(
        interface.format_prompt(
            "?",
            _("What is your location?")
        ),
        profile.get_profile_var(["weather", "location"])
    )

    while location and not verify_location(location):
        print(
            interface.alert_text(
                _("Weather not found.")
            ) + " " + interface.instruction_text(
                _("Please try another location.")
            )
        )
        location = interface.simple_input(
            interface.format_prompt(
                "?",
                _("What is your location?")
            ),
            location
        )
    if location:
        profile.set_profile_var(['weather', 'location'], location)


def get_timezone():
    # timezone
    # FIXME AaronC 2018-07-26 Knowing the zip code, you should be
    # able to work out the time zone.
    # Also, sending me to a wikipedia page to configure this? Really?
    print(
        "    " + interface.instruction_text(
            _("Please enter a timezone from the list located in the TZ*")
        )
    )
    print(
        "    " + interface.instruction_text(
            _("column at")
        ) + " " + interface.url_text(
            "http://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
        )
    )
    print("    " + interface.instruction_text(_("or none at all.")))
    print("")
    tz = profile.get_profile_var(["timezone"])
    if not tz:
        try:
            tz = run_command(
                ["/bin/cat", "/etc/timezone"],
                capture=1
            ).stdout.decode('utf-8').strip()
        except OSError:
            tz = None
    tz = interface.simple_input(
        interface.format_prompt(
            "?",
            _("What is your timezone?")
        ),
        tz
    )
    while tz:
        try:
            pytz.timezone(tz)
            profile.set_profile_var(['timezone'], tz)
            break
        except pytz.exceptions.UnknownTimeZoneError:
            print(interface.alert_text(_("Not a valid timezone. Try again.")))
            tz = interface.simple_input(
                interface.format_prompt(
                    "?",
                    _("What is your timezone?")
                ),
                tz
            )


# All three of these speech to text engines
# pull from the same group of stt engines
def get_passive_stt_engine():
    print(
        interface.instruction_text(
            """
The passive speech to text engine listens to everything you say scanning for
its keyphrase. It also will pick up some loud noises. Thus, the passive speech
to text engine may hear things in your home that are not meant for or addressed
to your personal assistant. We strongly recommend that you use a local speech
to text engine such as PocketSphinx, DeepSpeech, Kaldi or Julius.

Of these, Naomi's support for PocketSphinx is the best developed and easiest to
set up. Pocketsphinx will run directly on a Raspberry Pi and uses statistics to
calculate the best match between what it hears and a list of words. It is very
fast and lightweight, but not very accurate."""
        )
    )
    profile.set_profile_var(
        ['passive_stt', 'engine'],
        get_stt_engine(
            _("Please select a passive speech to text engine"),
            profile.get_profile_var(
                ["passive_stt", "engine"],
                profile.get_profile_var(
                    ["active_stt", "engine"],
                    "sphinx"
                )
            )
        )
    )


def get_active_stt_engine():
    print(
        interface.instruction_text(
            """
The active speech to text engine will only listen to audio once the passive
speech to text engine reports hearing the keyword. Thus, almost everything
this engine processes will be audio that is addressed towards your
personal assistant.

We still recommend a local speech to text engine, but at this level,
DeepSpeech, Kaldi or Julius might be a better choice. DeepSpeech
and Julius can run directly on a Raspberry Pi, although they will be slower
than PocketSphinx, resulting in some significant pauses. Kaldi may require you
to set up an additional server for speech to text processing.

Google Cloud STT is very accurate and easy to set up but does require that you
open a google account and set up credit card payments (in case you run over
your free allotment) and, of course, send audio from your home to Google for
processing. Only use Google Cloud STT if you are comfortable with Google
personell having access to things spoken in your home.
"""
        )
    )
    profile.set_profile_var(
        ['active_stt', 'engine'],
        get_stt_engine(
            _("Please select an active speech to text engine"),
            profile.get_profile_var(
                ["active_stt", "engine"],
                "sphinx"
            )
        )
    )


def get_special_stt_engine():
    print(
        interface.instruction_text(
            """
The special speech to text engine is used in place of the active speech to text
engine in special circumstances where a specific domain of words can be used,
such as when controlling an mpd player, or playing a guessing game or text
adventure. Because of the small domain, we strongly recommend a local speech to
text engine. PocketSphinx should give good results here. We are currently
working to train DeepSpeech, Kaldi and Julius for smaller domains."""
        )
    )
    profile.set_profile_var(
        ['special_stt', 'engine'],
        get_stt_engine(
            _("Please select a special speech to text engine"),
            profile.get_profile_var(
                ["special_stt", "engine"],
                profile.get_profile_var(
                    ["active_stt", "engine"],
                    "sphinx"
                )
            )
        )
    )


def get_stt_engine(prompt, default):
    # Get a list of STT engines
    stt_engines = {
        "PocketSphinx": "sphinx",
        "DeepSpeech": "deepspeech-stt",
        "Wit.AI": "witai-stt",
        "Google Voice": "google-stt",
        "Watson": "watson-stt",
        "Kaldi": "kaldigstserver-stt",
        "Julius": "julius-stt"
    }

    print(
        "    " + interface.strong_text(prompt)
    )
    print("")
    temp = list(stt_engines.keys())[
        list(stt_engines.values()).index(
            default
        )
    ]
    once = False
    while not ((once) and (temp in stt_engines.keys())):
        once = True
        temp = interface.simple_input(
            "    " + interface.instruction_text(
                _("Available choices:")
            ) + " " + interface.choices_text(
                ("%s. " % list(stt_engines.keys()))
            ),
            temp
        )
        try:
            response = stt_engines[temp]
        except KeyError:
            print(
                interface.alert_text(
                    _("Unrecognized option.")
                )
            )

    print("")
    # Handle special cases here
    if(response == 'google-stt'):
        pass
    elif(response == 'watson-stt'):
        username = interface.simple_input(
            interface.format_prompt(
                "!",
                _("Please enter your watson username:")
            )
        )
        profile.set_profile_var(["watson_stt", "username"], username)
        # FIXME AaronC 2018-07-29 - another password. Not as crucial as
        # protecting the user's email password but still...
        profile.set_profile_var(
            ["watson_stt", "password"],
            getpass(
                _("Please enter your watson password:")
            )
        )
    elif(response == 'kaldigstserver-stt'):
        print(
            "    " + interface.instruction_text(
                _("I need your Kaldi g-streamer server url to continue")
            )
        )
        default = "http://localhost:8888/client/dynamic/recognize"
        print(
            "    " + interface.instruction_text(
                "(" + _("default is") + " "
            ) + interface.url_text(
                "%s" % default
            ) + interface.instruction_text(
                ")"
            )
        )
        print("")
        temp = profile.get_profile_var(["kaldigstserver-stt", "url"])
        if(not temp):
            temp = default
        profile.set_profile_var(
            ['kaldigstserver-stt', 'url'],
            interface.simple_input(
                interface.format_prompt(
                    "!",
                    _("Please enter your server url:")
                ),
                temp
            )
        )
    elif(response == 'julius-stt'):
        # stt_engine: julius
        # julius:
        #     hmmdefs:  '/path/to/your/hmmdefs'
        #     tiedlist: '/path/to/your/tiedlist'
        #     lexicon:  '/path/to/your/lexicon.tgz'
        #     lexicon_archive_member: 'VoxForge/VoxForgeDict'
        #           only needed if lexicon is a tar/tar.gz archive
        # hmmdefs
        profile.set_profile_var(
            ["julius", "hmmdefs"],
            interface.simple_input(
                interface.format_prompt(
                    "!",
                    _("Enter path to julius hmm defs")
                ),
                profile.get_profile_var(["julius", "hmmdefs"])
            )
        )
        # tiedlist
        profile.set_profile_var(
            ["julius", "tiedlist"],
            interface.simple_input(
                interface.format_prompt(
                    "!",
                    _("Enter path to julius tied list")
                ),
                profile.get_profile_var(["julius", "tiedlist"])
            )
        )
        # lexicon
        profile.set_profile_var(
            ["julius", "lexicon"],
            interface.simple_input(
                interface.format_prompt(
                    "!",
                    _("Enter path to julius lexicon")
                ),
                profile.get_profile_var(["julius", "lexicon"])
            )
        )
        # FIXME AaronC 2018-07-29 So I don't know if I need to check above to
        # see if the julius lexicon is a tar file or if I can just set this.
        # The instructions just say it is only needed if the lexicon is a tar
        # file, not that it will cause problems if included. I'm also not clear
        # if the above is a literal string or just indicates that the path to
        # something needs to be entered. Someone with experience setting up
        # Julius will need to finish this up.
        profile.set_profile_var(
            ["julius", "lexicon_archive_member"],
            "VoxForge/VoxForgeDict"
        )
    elif(response == 'witai-stt'):
        witai_token = interface.simple_input(
            interface.format_prompt(
                "!",
                _("Please enter your Wit.AI token")
            ),
            profile.get_profile_var(["witai-stt", "access_token"])
        )
        profile.set_profile_var(["witai-stt", "access_token"], witai_token)
    else:
        # AaronC 2018-07-29 Since pocketsphinx/phonetisaurus is assumed, make
        # this the default at the end
        # is the phonetisaurus program phonetisaurus-g2p (old version)
        # or phonetisaurus-g2pfst?
        phonetisaurus_executable = profile.get_profile_var(
            ['pocketsphinx', 'phonetisaurus_executable']
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
            phonetisaurus_executable = interface.simple_input(
                interface.format_prompt(
                    "?",
                    _("What is the name of your phonetisaurus-g2p program?")
                ),
                phonetisaurus_executable
            )
        profile.set_profile_var(
            ['pocketsphinx', 'phonetisaurus_executable'],
            phonetisaurus_executable
        )
        # We have the following things to configure:
        #  hmm_dir - the default is
        #     "/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k"
        #          - if you install through the pocketsphinx-en-us debian apt
        #            package then it is
        #     "/usr/share/pocketsphinx/model/en-us/en-us"
        #          - if you install the latest pocketsphinx from source,
        #            it should be here:
        #     "~/pocketsphinx-python/pocketsphinx/model/en-us/en-us"
        #  fst_model -
        #          - the default is "~/phonetisaurus/g014b2b.fst"
        #          - if you install the latest CMUDict, then it will be at
        #            "~/CMUDict/train/model.fst"
        hmm_dir = profile.get_profile_var(['pocketsphinx', 'hmm_dir'])
        once = False
        while not(once and hmm_dir):
            once = True
            # The hmm_dir should be under the user's home directory
            # in the "~/pocketsphinx/model/en-us/en-us" directory
            if(not hmm_dir):
                if(os.path.isdir(os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx-python",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
                ))):
                    hmm_dir = os.path.join(
                        os.path.expanduser("~"),
                        "pocketsphinx-python",
                        "pocketsphinx",
                        "model",
                        "en-us",
                        "en-us"
                    )
                elif(os.path.isdir(os.path.join(
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
                elif(os.path.isdir(os.path.join(
                        "/",
                        "usr",
                        "share",
                        "pocketsphinx",
                        "model",
                        "en-us",
                        "en-us"
                ))):
                    hmm_dir = os.path.join(
                        "/",
                        "usr",
                        "share",
                        "pocketsphinx",
                        "model",
                        "en-us",
                        "en-us"
                    )
                elif(
                    os.path.isdir(os.path.join(
                        "/",
                        "usr",
                        "local",
                        "share",
                        "pocketsphinx",
                        "model",
                        "hmm",
                        "en_US",
                        "hub4wsj_sc_8k"
                    ))
                ):
                    hmm_dir = os.path.join(
                        "/",
                        "usr",
                        "local",
                        "share",
                        "pocketsphinx",
                        "model",
                        "hmm",
                        "en_US",
                        "hub4wsj_sc_8k"
                    )
            hmm_dir = interface.simple_input(
                interface.format_prompt(
                    "!",
                    _("Please enter the path to your hmm directory")
                ),
                hmm_dir
            )
            profile.set_profile_var(["pocketsphinx", "hmm_dir"], hmm_dir)
        # fst_model
        fst_model = profile.get_profile_var(["pocketsphinx", "fst_model"])
        once = False
        while not (once and fst_model):
            once = True
            if(os.path.isfile(os.path.join(
                os.path.expanduser("~"),
                "pocketsphinx-python",
                "pocketsphinx",
                "model",
                "en-us",
                "train",
                "model.fst"
            ))):
                fst_model = os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx-python",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "train",
                    "model.fst"
                )
            elif(os.path.isfile(os.path.join(
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
            elif(os.path.isfile(os.path.join(
                os.path.expanduser("~"),
                "CMUDict",
                "train",
                "model.fst"
            ))):
                fst_model = os.path.join(
                    os.path.expanduser("~"),
                    "CMUDict",
                    "train",
                    "model.fst"
                )
            elif(os.path.isfile(os.path.join(
                os.path.expanduser("~"),
                "phonetisaurus",
                "g014b2b.fst"
            ))):
                fst_model = os.path.join(
                    os.path.expanduser("~"),
                    "phonetisaurus",
                    "g014b2b.fst"
                )
            fst_model = interface.simple_input(
                interface.format_prompt(
                    "!",
                    _("Please enter the path to your fst model")
                ),
                fst_model
            )
            profile.set_profile_var(
                ["pocketsphinx", "fst_model"],
                fst_model
            )
    return response


def get_tts_engine():
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
    # Prepare the tts_plugins object so we can
    # instantiate and test the chosen plugin.
    tts_plugins = pluginstore.PluginStore()
    tts_plugins.detect_plugins("tts")
    voice_chosen = False
    while not voice_chosen:
        try:
            response = list(tts_engines.keys())[
                list(tts_engines.values()).index(
                    profile.get_profile_var(
                        ['tts_engine']
                    )
                )
            ]
        except (KeyError, ValueError):
            response = "Flite"
        print(
            "    " + interface.instruction_text(
                _("Please select a text to speech (TTS) engine.")
            )
        )
        print("")
        once = False
        while not ((once) and (response in tts_engines)):
            once = True
            response = interface.simple_input(
                interface.format_prompt(
                    "?",
                    _("Available implementations: ") + interface.choices_text(
                        "%s. " % list(tts_engines.keys())
                    )
                ),
                response
            )
            try:
                profile.set_profile_var(['tts_engine'], tts_engines[response])
            except KeyError:
                print(interface.alert_text(_("Unrecognized option.")))
        print("")
        # Deal with special cases
        if(profile.get_profile_var(["tts_engine"]) == "espeak-tts"):
            # tts_engine: espeak-tts
            voice_chosen = True
            print(
                "    " + interface.instruction_text(
                    _("If you would like to alter the espeak voice,")
                )
            )
            print(
                "    " + interface.instruction_text(
                    _("you can use the following options in your config file:")
                )
            )
            print("")
            print("    espeak-tts:")
            print("        voice: 'default+m3'   # optional")
            print("        pitch_adjustment: 40  # optional")
            print("        words_per_minute: 160 # optional")
        elif(profile.get_profile_var(["tts_engine"]) == "festival-tts"):
            # tts_engine: festival-tts
            voice_chosen = True
            print(
                "    " + interface.instruction_text(
                    _("Use the festival command to set the default voice.")
                )
            )
        elif(profile.get_profile_var(["tts_engine"]) == "flite-tts"):
            try:
                # pdb.set_trace()
                flite_info = tts_plugins.get_plugin(
                    'flite-tts',
                    category='tts'
                )
                flite_plugin = flite_info.plugin_class(
                    flite_info,
                    {"flite-tts": {"voice": "slt"}}
                )
                voices = flite_plugin.get_voices()
                print(
                    "    " + interface.instruction_text(
                        _("Available voices:")
                    ) + " " + interface.choices_text(
                        "%s. " % voices
                    )
                )
                voice = profile.get_profile_var(["flite-tts", "voice"])
                if not voice:
                    try:
                        voice = voices[voices.index("slt")]
                    except ValueError:
                        voice = None
                voice = interface.simple_input(
                    interface.format_prompt(
                        "?",
                        _("Select a voice")
                    ),
                    voice
                )
                # Test the voice
                ae_info = audioengine_plugins.get_plugin(
                    profile.get_profile_var(['audio_engine']),
                    category='audioengine'
                )
                audio_engine = ae_info.plugin_class(
                    ae_info,
                    profile.get_profile()
                )
                output_device_slug = profile.get_profile_var(
                    ["audio", "output_device"]
                )
                output_device = audio_engine.get_device_by_slug(
                    output_device_slug
                )
                with tempfile.SpooledTemporaryFile() as f:
                    f.write(
                        flite_plugin.say(
                            _('Is this the voice you would like me to use?'),
                            voice
                        )
                    )
                    f.seek(0)
                    output_device.play_fp(f)
                if interface.simple_yes_no(
                    _("Is this the voice you would like me to use?")
                ):
                    profile.set_profile_var(
                        ["flite-tts", "voice"],
                        voice
                    )
                    voice_chosen = True
            except OSError:
                print(interface.alert_text(
                    _("FLite does not appear to be installed")
                ))
                print(interface.instruction_text(_("Please install it using:")))
                print("  $ " + interface.success_text("sudo apt install flite"))
                print(interface.instruction_text(
                    _("then re-run Naomi with the --repopulate flag")
                ))
                print(" ".join([
                    "  $ ",
                    interface.success_text("./Naomi.py --repopulate")
                ]))
        elif(profile.get_profile_var(["tts_engine"]) == "pico-tts"):
            voice_chosen = True
        elif(profile.get_profile_var(["tts_engine"]) == "google-tts"):
            voice_chosen = True
        elif(profile.get_profile_var(["tts_engine"]) == "ivona-tts"):
            voice_chosen = True
            print(
                "    " + interface.instruction_text(" ".join([
                    _("You will now need to enter"),
                    _("your Ivona account information.")
                ]))
            )
            print("")
            url = interface.url_text(
                "https://www.ivona.com/us/account/speechcloud/creation/"
            )
            print(
                "    " + interface.instruction_text(
                    _("You will need to create an account at {}").format(
                        interface.url_text(url)
                    )
                )
            )
            print(
                " " + interface.instruction_text(
                    _("if you haven't already.")
                )
            )
            print("")
            profile.set_profile_var(
                ["ivona-tts", "access_key"],
                interface.simple_input(
                    interface.format_prompt(
                        "?",
                        _("What is your Access key?")
                    ),
                    profile.get_profile_var(["ivona-tts", "access_key"])
                )
            )
            profile.set_profile_var(
                ["ivona-tts", "secret_key"],
                interface.simple_input(
                    interface.format_prompt(
                        "?",
                        _("What is your Secret key?")
                    ),
                    profile.get_profile_var(["ivona-tts", "secret_key"])
                )
            )
            # ivona-tts voice
            temp = profile.get_profile_var(["ivona-tts", "voice"])
            if(not temp):
                temp = "Brian"
            profile.set_profile_var(
                ["ivona-tts", "voice"],
                interface.simple_input(
                    interface.format_prompt(
                        "?",
                        " ".join([
                            _("Which voice do you want"),
                            interface.default_text(
                                _("(default is Brian)")
                            ) + interface.question_text("?")
                        ])
                    ),
                    temp
                )
            )
        elif(profile.get_profile_var(["tts_engine"]) == "mary-tts"):
            voice_chosen = True
            profile.set_profile_var(
                ["mary-tts", "server"],
                interface.simple_input(
                    interface.format_prompt(
                        "?",
                        _("Server?")
                    ),
                    profile.get_profile_var(["mary-tts", "server"])
                )
            )
            profile.set_profile_var(
                ["mary-tts", "port"],
                interface.simple_input(
                    interface.format_prompt(
                        "?",
                        "Port?"
                    ),
                    profile.get_profile_var(["mary-tts", "port"])
                )
            )
            profile.set_profile_var(
                ["mary-tts", "language"],
                interface.simple_input(
                    interface.format_prompt(
                        "?",
                        _("Language?")
                    ),
                    profile.get_profile_var(["mary-tts", "language"])
                )
            )
            profile.set_profile_var(
                ["mary-tts", "voice"],
                interface.simple_input(
                    interface.format_prompt(
                        "?",
                        _("Voice?")
                    ),
                    profile.get_profile_var(["mary-tts", "voice"])
                )
            )


def get_beep_or_voice():
    # Getting information to beep or not beep
    print(
        "    " + interface.instruction_text(
            _("I have two ways to let you know I've heard you; Beep or Voice.")
        )
    )
    # If there are values for [active_stt][reply] and [active_stt][response]
    # then use them otherwise use beeps
    voice_choice = _("voice").lower()[:1]
    beep_choice = _("beep").lower()[:1]
    if(profile.get_profile_var(["active_stt", "reply"])):
        temp = voice_choice
    else:
        temp = beep_choice
    print(
        "    " + _("{beep} for beeps or {voice} for voice.").format(
            beep="".join([
                interface.choices_text(),
                beep_choice,
                interface.instruction_text()
            ]),
            voice="".join([
                interface.choices_text(),
                voice_choice,
                interface.instruction_text()
            ])
        )
    )
    print("")
    response = interface.simple_input(
        interface.format_prompt(
            "?",
            _("({beep}) for beeps or ({voice}) for voice.").format(
                beep="".join([
                    interface.choices_text(),
                    beep_choice,
                    interface.instruction_text()
                ]),
                voice="".join([
                    interface.choices_text(),
                    voice_choice,
                    interface.instruction_text()
                ])
            )
        ),
        temp
    )
    while(
        (
            not response
        )or(
            (
                response.lower()[:1] != beep_choice
            )and(
                response.lower()[:1] != voice_choice
            )
        )
    ):
        response = interface.simple_input(
            interface.alert_text(
                _("Please choose beeps ({b}) or voice ({v})").format(
                    b=beep_choice.upper(),
                    v=voice_choice.upper()
                )
            )
        )
    if(response.lower()[:1] == voice_choice):
        print("")
        print("")
        print("")
        print(
            "    " + interface.instruction_text(
                _("Type the words I should say after hearing my wake word: %s")
                % profile.get_profile_var(["keyword"])
            )
        )
        print("")
        areplyRespon = None
        while(not areplyRespon):
            areply = interface.simple_input(
                interface.format_prompt(
                    "?",
                    _("Reply")
                ),
                profile.get_profile_var(["active_stt", "reply"])
            )
            areplyRespon = None
            while(areplyRespon is None):
                print("")
                areplyRespon = interface.simple_yes_no(
                    areply + " - " + _("Is this correct?")
                )
        profile.set_profile_var(['active_stt', 'reply'], areply)
        interface.separator()
        print(
            "    " + interface.instruction_text(
                _("Type the words I should say after hearing a command")
            )
        )
        aresponseRespon = None
        while(not aresponseRespon):
            aresponse = interface.simple_input(
                interface.format_prompt(
                    "?",
                    _("Response")
                ),
                profile.get_profile_var(["active_stt", "response"])
            )
            print("")
            aresponseRespon = None
            while(aresponseRespon is None):
                aresponseRespon = interface.simple_yes_no(
                    aresponse + " - " + _("Is this correct?")
                )
        profile.set_profile_var(['active_stt', 'response'], aresponse)
    else:
        # If beeps are selected, must remove both reply and response
        profile.set_profile_var(['active_stt', 'reply'], "")
        profile.set_profile_var(['active_stt', 'response'], "")


# Return a list of currently installed audio engines.
def get_audio_engines():
    global audioengine_plugins
    audioengine_plugins = pluginstore.PluginStore()
    audioengine_plugins.detect_plugins("audioengine")
    audioengines = [
        ae_info.name
        for ae_info
        in audioengine_plugins.get_plugins_by_category(
            category='audioengine'
        )
    ]
    return audioengines


def select_audio_engine():
    # Audio Engine
    audioengines = get_audio_engines()

    print(interface.instruction_text(_("Please select an audio engine.")))
    try:
        default = "pyaudio"
        if re.match(r'linux', platform.system().lower()):
            default = "alsa"
        if default not in audioengines:
            default = audioengines[0]
        response = audioengines[
            audioengines.index(
                profile.get_profile_var(['audio_engine'], default)
            )
        ]
    except (ValueError):
        response = audioengines[0]
    once = False
    while not ((once) and (response in audioengines)):
        audioengines = get_audio_engines()
        once = True
        response = interface.simple_input(
            " ".join([
                "   ",
                _("Available implementations:"),
                interface.choices_text(
                    ("{}".format(audioengines))
                ),
                interface.instruction_text(".")
            ]),
            response
        )
    profile.set_profile_var(['audio_engine'], response)


def get_output_device():
    # AaronC 2018-09-14 Initialize AudioEngine
    ae_info = audioengine_plugins.get_plugin(
        profile.get_profile_var(['audio_engine']),
        category='audioengine'
    )
    # AaronC 2018-09-14 Get a list of available output devices
    audio_engine = ae_info.plugin_class(ae_info, profile.get_profile())
    output_devices = []
    print(interface.instruction_text("Checking devices for compatibility"))
    for output_device_slug in [
        device.slug for device in audio_engine.get_devices(
            device_type=audioengine.DEVICE_TYPE_OUTPUT
        )
    ]:
        output_device = audio_engine.get_device_by_slug(output_device_slug)
        if output_device.supports_format(16, 1, 16000, output=True):
            output_devices.append(output_device_slug)

    output_device_slug = profile.get_profile_var(["audio", "output_device"])
    if not output_device_slug:
        output_device_slug = audio_engine.get_default_device(output=True).slug
    heard = None
    once = False
    while not (once and heard):
        print(interface.instruction_text(_("Please choose an output device")))
        while not ((once) and (output_device_slug in output_devices)):
            once = True
            output_device_slug = interface.simple_input(
                interface.instruction_text(
                    _("Available output devices:") + " "
                ) + interface.choices_text(
                    ", ".join(output_devices)
                ),
                output_device_slug
            )
        profile.set_profile_var(["audio", "output_device"], output_device_slug)
        # try playing a sound
        # FIXME Set the following defaults to what is in the
        # configuration file
        output_chunksize = profile.get_profile_var(
            ['audio', 'output_chunksize'],
            1024
        )
        output_add_padding = profile.get_profile_var(
            ['audio', 'output_padding'],
            False
        )
        filename = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "data",
            "audio",
            "beep_lo.wav"
        )
        if(os.path.isfile(filename)):
            print(interface.instruction_text(
                _("Testing device by playing a sound")
            ))
            output_device = audio_engine.get_device_by_slug(output_device_slug)
            output_device.play_file(
                filename,
                chunksize=output_chunksize,
                add_padding=output_add_padding
            )
            heard = interface.simple_yes_no(
                _("Were you able to hear the beep?")
            )
            try:
                if not (heard):
                    print(
                        interface.instruction_text(" ".join([
                            _("The volume on your device may be too low."),
                            _("You should be able to use 'alsamixer'"),
                            _("to set the volume level.")
                        ]))
                    )
                    heard = interface.simple_yes_no(
                        interface.instruction_text(
                            " ".join([
                                _("Do you want to continue now"),
                                _("and fix the volume later?")
                            ])
                        )
                    )
                    if not (heard):
                        once = False
            except audioengine.UnsupportedFormat as e:
                print(interface.alert_text(str(e)))
                print(
                    interface.instruction_text(
                        _("Output format not supported on this device.")
                    )
                )
                print(
                    interface.instruction_text(
                        _("Please choose a different device.")
                    )
                )
                print("")
                once = False
        else:
            print(
                interface.alert_text(
                    _("Can't locate wav file: %s") % filename
                )
            )
            print(
                interface.instruction_text(
                    _("Skipping test")
                )
            )
            heard = True


def get_input_device():
    # AaronC 2018-09-14 Initialize AudioEngine
    ae_info = audioengine_plugins.get_plugin(
        profile.get_profile_var(['audio_engine']),
        category='audioengine'
    )
    # AaronC 2018-09-14 Get a list of available output devices
    audio_engine = ae_info.plugin_class(ae_info, profile.get_profile())
    # AaronC 2018-09-14 Get a list of available input devices
    input_devices = [device.slug for device in audio_engine.get_devices(
        device_type=audioengine.DEVICE_TYPE_INPUT)]
    input_device_slug = profile.get_profile_var(["audio", "input_device"])
    if not input_device_slug:
        input_device_slug = audio_engine.get_default_device(output=False).slug
    once = False
    while not (once):
        print(interface.instruction_text(_("Please choose an input device")))
        once = True
        input_device_slug = interface.simple_input(
            _("Available input devices:") + " " + interface.choices_text(
                ", ".join(input_devices)
            ),
            input_device_slug
        )
        profile.set_profile_var(["audio", "input_device"], input_device_slug)
        # try recording a sample
        test = interface.simple_yes_no(" ".join([
            _("Would you like me to test your selection"),
            _("by recording your voice and playing it back to you?")
        ]))
        while test:
            test = False
            # FIXME AaronC Sept 16 2018
            # The following are defaults. They should be read
            # from the proper locations in the profile file if
            # they have been set.
            threshold = 10  # 10 dB
            input_chunks = profile.get_profile_var(
                ['audio', 'input_chunksize'],
                1024
            )
            input_bits = profile.get_profile_var(
                ['audio', 'input_samplewidth'],
                16
            )
            input_channels = profile.get_profile_var(
                ['audio', 'input_channels'],
                1
            )
            input_rate = profile.get_profile_var(
                ['audio', 'input_samplerate'],
                16000
            )

            output_chunksize = profile.get_profile_var(
                ['audio', 'output_chunksize'],
                1024
            )
            output_add_padding = profile.get_profile_var(
                ['audio', 'output_padding'],
                False
            )
            input_device = audio_engine.get_device_by_slug(
                profile.get_profile_var(['audio', 'input_device'])
            )
            output_device = audio_engine.get_device_by_slug(
                profile.get_profile_var(["audio", "output_device"])
            )
            frames = collections.deque([], 30)
            recording = False
            recording_frames = []
            filename = os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ),
                "data",
                "audio",
                "beep_hi.wav"
            )
            if(os.path.isfile(filename)):
                output_device.play_file(
                    filename,
                    chunksize=output_chunksize,
                    add_padding=output_add_padding
                )
            print(
                interface.instruction_text(
                    _("Please speak into the mic now")
                )
            )
            for frame in input_device.record(
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
                            interface.alert_text(
                                _("Sound detected - recording")
                            )
                        )
                        recording = True
                        if len(frames) > 30:
                            recording_frames = list(frames)[-30:]
                        else:
                            recording_frames = list(frames)
                    elif len(frames) >= frames.maxlen:
                        # Threshold not reached. Update.
                        soundlevel = float(audioop.rms(b"".join(frames), 2))
                        if (soundlevel < threshold):
                            print(interface.alert_text(" ".join([
                                _("No sound detected."),
                                _("Setting threshold from {t} to {s}").format(
                                    t=threshold,
                                    s=soundlevel
                                )
                            ])))
                            threshold = soundlevel
                else:
                    recording_frames.append(frame)
                    if len(recording_frames) > 20:
                        # Check if we are below threshold again
                        last_snr = _snr(
                            input_bits,
                            threshold,
                            recording_frames[-10:]
                        )
                        if((
                            last_snr <= threshold
                        )or(
                            len(recording_frames) > 60
                        )):
                            # stop recording
                            recording = False
                            print(
                                interface.success_text(
                                    _("Recorded %d frames")
                                    % len(recording_frames)
                                )
                            )
                            break
            if len(recording_frames) > 20:
                once = False
                replay = True
                while (replay):
                    once = True
                    with tempfile.NamedTemporaryFile(mode='w+b') as f:
                        wav_fp = wave.open(f, 'wb')
                        wav_fp.setnchannels(input_channels)
                        wav_fp.setsampwidth(int(input_bits / 8))
                        wav_fp.setframerate(input_rate)
                        fragment = b"".join(frames)
                        wav_fp.writeframes(fragment)
                        wav_fp.close()
                        output_device.play_file(
                            f.name,
                            chunksize=output_chunksize,
                            add_padding=output_add_padding
                        )
                    heard = interface.simple_yes_no(
                        _("Did you hear yourself?")
                    )
                    if (heard):
                        replay = False
                        once = True
                    else:
                        replay = interface.simple_yes_no(
                            _("Replay?")
                        )
                        if (not replay):
                            skip = interface.simple_yes_no(
                                _("Do you want to skip this test and continue?")
                            )
                            if (skip):
                                replay = False
                                heard = True
                                once = True
                                test = False
                            else:
                                replay = False
                                heard = True
                                once = False
                                test = False


def run():
    global _, affirmative, negative
    #
    # AustinC; Implemented new UX for the population process.
    # For population blessings is used to handle colors,
    # formatting, & and screen isolation.
    #
    # For plugin & general use elsewhere, blessings or
    # coloredformatting.py can be used.
    #
    # select_language()
    interface.get_language()
    interface.separator()
    translations = i18n.parse_translations(paths.data('locale'))
    translator = i18n.GettextMixin(translations)
    _ = translator.gettext

    precheck()
    interface.separator()

    greet_user()
    interface.separator()

    # get_wakeword()
    # interface.separator()

    # select_audio_engine()
    # interface.separator()

    # get_output_device()
    # interface.separator()

    # get_input_device()
    # interface.separator()

    # get_passive_stt_engine()
    # interface.separator()

    # get_active_stt_engine()
    # interface.separator()

    # get_special_stt_engine()
    # interface.separator()

    # get_tts_engine()
    # interface.separator()

    get_beep_or_voice()
    interface.separator()

    # get_user_name()
    # interface.separator()

    # get_email_info()
    # interface.separator()

    # get_phone_info()
    # interface.separator()

    # get_notification_info()
    # interface.separator()

    # comment out the following two lines as the weather location service
    # at weather underground has now been shut down. AaronC 2019-03-25
    # get_weather_location()
    # interface.separator()

    # get_timezone()
    # interface.separator()

    # write to profile
    # profile.save_profile()

    interface.separator()
    print(
        interface.normal_text()
    )


# properties
t = Terminal()
# given values in select_language()
_ = None
affirmative = ""
negative = ""
audioengine_plugins = None
try:
    interface = commandline.commandline()
except FileNotFoundError:
    # Here I am catching what should be that the
    # profile.yml file is not found.
    # The first call to commandline() would have
    # set up a temporary profile in the catch in
    # profile.get_profile(), so this second
    # call should work now and set up the commandline
    # object so we can interact with the user
    # Eventually, once all the settings have been
    # pulled into the settings system, we won't need
    # to explicitely run populate.run() anymore,
    # the settings will be requested just because they
    # are missing.
    interface = commandline.commandline()

if __name__ == "__main__":
    print("This program can no longer be run directly.")
    print("Please run the Populate.py program from the")
    print("Naomi root directory.")
