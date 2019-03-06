#!/usr/bin/env python2
# -*- coding: utf-8 -*-
try:
    import audioop
    from blessings import Terminal
    import collections
    import feedparser
    from getpass import getpass
    import math
    import os
    from . import paths
    from . import profile
    import pytz
    import re
    from . import run_command
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

# properties
t = Terminal()
# given values in select_language()
_ = None
affirmative = ""
negative = ""

audioengine_plugins = None


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
def choices_text(text=""):
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


def format_prompt(icon, prompt):
    if(icon == "!"):
        prompt = "".join([
            icon_text('['),
            alert_icon('!'),
            icon_text('] '),
            question_text(prompt)
        ])
    elif(icon == "?"):
        prompt = "".join([
            icon_text('['),
            question_icon('?'),
            icon_text('] '),
            question_text(prompt)
        ])
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
        prompt += default_text(default) + default_prompt()
    prompt += input_text()
    # don't use print here so no automatic carriage return
    # sys.stdout.write(prompt)
    response = input(prompt)
    # if the user pressed enter without entering anything,
    # set the response to default
    if(default and not response):
        response = default
    return response.strip()


# AaronC - simple_request is more complicated, and populates
# the profile variable directly
def simple_request(path, prompt, cleanInput=None):
    input_str = simple_input(prompt, profile.get_profile_var(path))
    if input_str:
        if cleanInput:
            input_str = cleanInput(input_str)
        profile.set_profile_var(path, input_str)


# AaronC Sept 18 2018 This uses affirmative/negative to ask
# a yes/no question. Returns True for yes and False for no.
def simple_yes_no(prompt):
    response = ""
    while(response not in (affirmative.lower()[:1], negative.lower()[:1])):
        response = simple_input(
            format_prompt(
                "?",
                prompt + instruction_text(" (") + choices_text(
                    affirmative.upper()[:1]
                ) + instruction_text("/") + choices_text(
                    negative.upper()[:1]
                ) + instruction_text(")")
            )
        ).strip().lower()[:1]
        if response not in (affirmative.lower()[:1], negative.lower()[:1]):
            print(alert_text("Please select '{}' or '{}'.").config(
                affirmative.upper()[:1],
                negative.upper()[:1]
            ))
    if response == affirmative.lower()[:1]:
        return True
    else:
        return False


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
            success_text(
                " ".join([
                    _("Location saved as"),
                    feed['feed']['description'][33:]
                ])
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


def select_language():
    global _, affirmative, negative
    #
    # AustinC; can't use français due to the special char "ç"
    # it breaks due to it being out of range for ascii
    #
    languages = {
        u'EN-English': 'en-US',
        u'FR-Français': 'fr-FR',
        u'DE-Deutsch': 'de-DE'
    }
    language = profile.get_profile_var(["language"], "en-US")
    selected_language = list(languages.keys())[
        list(languages.values()).index(language)
    ]
    translations = i18n.parse_translations(paths.data('locale'))
    translator = i18n.GettextMixin(translations, profile.get_profile())
    _ = translator.gettext
    once = False
    while not (
        (
            once
        )and(
            check_for_value(
                selected_language.strip().lower(),
                [x[:len(selected_language)].lower() for x in languages.keys()]
            )
        )
    ):
        once = True
        print("    " + instruction_text(_("Language Selector")))
        print("")
        print("")
        for language in languages.keys():
            print("    {}".format(language))
        print("")
        selected_language = simple_input(
            format_prompt(
                "?",
                _('Select Language')
            ),
            selected_language
        ).strip().lower()
        if(len(selected_language) > 0):
            if(check_for_value(
                selected_language,
                [x[
                    :len(selected_language)
                ].lower() for x in list(
                    languages.keys()
                )]
            )):
                language = languages[
                    list(languages.keys())[[x[
                        :len(selected_language)
                    ].lower() for x in list(
                        languages.keys()
                    )].index(selected_language)]
                ]
                if(language == 'fr-FR'):
                    affirmative = 'oui'
                    negative = 'non'
                elif(language == 'de-DE'):
                    affirmative = "ja"
                    negative = "nein"
                else:
                    affirmative = 'yes'
                    negative = 'no'

    profile.set_profile_var(['language'], language)
    translations = i18n.parse_translations(paths.data('locale'))
    translator = i18n.GettextMixin(translations, profile.get_profile())
    _ = translator.gettext


# check and make sure an audio engine is configured before allowing
# populate.py to continue.
def precheck():
    global _, affirmative, negative
    audioengines = get_audio_engines()
    while(len(audioengines) < 1):
        print(
            alert_text(
                _("You do not appear to have any audio engines configured.")
            )
        )
        print("You should either install the pyaudio or pyalsaaudio")
        print("python modules. Otherwise Naomi will be unable to speak")
        print("or listen.")
        print("")
        print("Both programs have prerequisites that can most likely")
        print("be installed using your package manager")
        if not simple_yes_no(_("Would you like me to check again?")):
            print("Can't continue, so quitting")
            quit()
        audioengines = get_audio_engines()


def greet_user():
    print("    " + instruction_text(
        _("Hello, thank you for selecting me to be your personal assistant.")
    ))
    print("")
    print(
        "    " + instruction_text(
            _("Let's populate your profile.")
        )
    )
    print("")
    print(
        "    " + instruction_text("".join([
            _("If, at any step, you would prefer not"),
            _("to enter the requested information")
        ]))
    )
    print(
        "    " + instruction_text(
            _("just hit 'Enter' with a blank field to continue.")
        )
    )
    print("")


def get_wakeword():
    # my name
    keyword = profile.get_profile_var(["keyword"], "Naomi")
    profile.set_profile_var(
        ["keyword"],
        simple_input(
            format_prompt(
                "?",
                _("First, what name would you like to call me by?")
            ),
            keyword
        )
    )


def get_user_name():
    # your name
    print(
        "    " + instruction_text(
            _("Now please tell me a little about yourself.")
        )
    )
    print("")
    simple_request(
        ["first_name"],
        format_prompt(
            "?",
            _("What is your first name?")
        )
    )
    print("")
    simple_request(
        ['last_name'],
        format_prompt(
            "?",
            _('What is your last name?')
        )
    )


def get_email_info():
    # email
    print(
        "    " + instruction_text(
            _("I can use an email account to send notifications to you.")
        )
    )
    print("    " + _("Alternatively, you can skip this step"))
    print("")
    # email
    profile.set_profile_var(
        ["email", "imap"],
        simple_input(
            format_prompt(
                "?",
                _('Please enter your imap server as "server[:port]"')
            ),
            profile.get_profile_var(["email", "imap"])
        )
    )

    profile.set_profile_var(
        ["email", "address"],
        simple_input(
            format_prompt(
                "?",
                _('What is your email address?')
            ),
            profile.get_profile_var(["email", "address"])
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
    if(profile.get_profile_var(["email", "address"])):
        prompt = _("What is your email password?") + ": "
        if(profile.get_profile_var(["email", "password"])):
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
            profile.set_profile_var(['email', 'password'], temp)


def get_phone_info():
    print(
        "    " + instruction_text(
            _("I can use your phone number to send notifications to you.")
        )
    )
    print("".join([
        "    ",
        _("Alternatively, you can skip this step")
    ]))
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
            profile.get_profile_var(['phone_number'])
        )
    )
    profile.set_profile_var(['phone_number'], phone_number)

    # carrier
    if(profile.get_profile_var(['phone_number'])):
        separator()
        # If the phone number is blank, it makes no sense to ask
        # for the carrier.
        print(
            "    " + instruction_text(
                _("What is your phone carrier?")
            )
        )
        print(
            "    " + instruction_text(" ".join([
                _("If you have a US phone number,"),
                _("you can enter one of the following:")
            ]))
        )
        print(
            choices_text("    'AT&T', 'Verizon', 'T-Mobile' ") + alert_text(
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
            "    " + instruction_text(" ".join([
                _("and enter the email suffix for your carrier"),
                _("(e.g., for Virgin Mobile, enter 'vmobl.com';"),
                ""
            ]))
        )
        print(
            "    " + instruction_text(
                _("for T-Mobile Germany, enter 't-d1-sms.de').")
            )
        )
        print("")
        carrier = simple_input(
            format_prompt(
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
            profile.get_profile_var(
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
        ) and profile.get_profile_var(
            ['email', 'address']
        )
    ):
        email_choice = _("email").lower()[:1]
        text_choice = _("text").lower()[:1]
        print(
            "    " + instruction_text(
                _("Would you prefer to have notifications sent by")
            )
        )
        print(
            "    " + instruction_text(
                _("email ({e}) or text message ({t})?").format(
                    e=email_choice.upper(),
                    t=text_choice.upper()
                )
            )
        )
        print("")
        if(profile.get_profile_var(["prefers_email"])):
            temp = email_choice
        else:
            temp = text_choice
        response = simple_input(
            format_prompt(
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
            response = simple_input(
                alert_text(
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
        "    " + instruction_text(" ".join([
            _("For weather information, please enter your 5-digit zipcode"),
            _("(e.g., 08544).")
        ]))
    )
    print(
        "    " + instruction_text(" ".join([
            _("If you are outside the US,"),
            _("insert the name of the nearest big town/city.")
        ]))
    )
    print("")
    location = simple_input(
        format_prompt(
            "?",
            _("What is your location?")
        ),
        profile.get_profile_var(["weather", "location"])
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
        profile.set_profile_var(['weather', 'location'], location)


def get_timezone():
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
    tz = profile.get_profile_var(["timezone"])
    if not tz:
        try:
            tz = run_command.run_command(["/bin/cat", "/etc/timezone"])
        except OSError:
            tz = None
    tz = simple_input(
        format_prompt(
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
            print(alert_text(_("Not a valid timezone. Try again.")))
            tz = simple_input(
                format_prompt(
                    "?",
                    _("What is your timezone?")
                ),
                tz
            )


def get_stt_engine():
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
    response = list(stt_engines.keys())[
        list(stt_engines.values()).index(
            profile.get_profile_var(
                ["active_stt", "engine"],
                "sphinx"
            )
        )
    ]
    once = False
    while not ((once) and (response in stt_engines.keys())):
        once = True
        response = simple_input(
            "    " + instruction_text(
                _("Available choices:")
            ) + " " + choices_text(
                ("%s. " % list(stt_engines.keys()))
            ),
            response
        )
        print("")
        try:
            profile.set_profile_var(
                ['active_stt', 'engine'],
                stt_engines[response]
            )
        except KeyError:
            print(
                alert_text(
                    _("Unrecognized option.")
                )
            )
    print("")
    # Handle special cases here
    if(profile.get_profile_var(['active_stt', 'engine']) == 'google'):
        # Set the api key (I'm not sure this actually works anymore,
        # need to test)
        profile.set_profile_var(
            ['keys', 'GOOGLE_SPEECH'],
            simple_input(
                format_prompt(
                    "!",
                    _("Please enter your API key:")
                ),
                profile.get_profile_var(["keys", "GOOGLE_SPEECH"])
            )
        )
    elif(profile.get_profile_var(['active_stt', 'engine']) == 'watson-stt'):
        username = simple_input(
            format_prompt(
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
    elif(
        profile.get_profile_var(
            ['active_stt', 'engine']
        ) == 'kaldigstserver-stt'
    ):
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
        temp = profile.get_profile_var(["kaldigstserver-stt", "url"])
        if(not temp):
            temp = default
        profile.set_profile_var(
            ['kaldigstserver-stt', 'url'],
            simple_input(
                format_prompt(
                    "!",
                    _("Please enter your server url:")
                ),
                temp
            )
        )
    elif(profile.get_profile_var(['active_stt', 'engine']) == 'julius-stt'):
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
            simple_input(
                format_prompt(
                    "!",
                    _("Enter path to julius hmm defs")
                ),
                profile.get_profile_var(["julius", "hmmdefs"])
            )
        )
        # tiedlist
        profile.set_profile_var(
            ["julius", "tiedlist"],
            simple_input(
                format_prompt(
                    "!",
                    _("Enter path to julius tied list")
                ),
                profile.get_profile_var(["julius", "tiedlist"])
            )
        )
        # lexicon
        profile.set_profile_var(
            ["julius", "lexicon"],
            simple_input(
                format_prompt(
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
    elif(profile.get_profile_var(['active_stt', 'engine']) == 'witai-stt'):
        witai_token = simple_input(
            format_prompt(
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
            phonetisaurus_executable = simple_input(
                format_prompt(
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
            hmm_dir = simple_input(
                format_prompt(
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
            fst_model = simple_input(
                format_prompt(
                    "!",
                    _("Please enter the path to your fst model")
                ),
                fst_model
            )
            profile.set_profile_var(
                ["pocketsphinx", "fst_model"],
                fst_model
            )


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
    try:
        response = list(tts_engines.keys())[
            list(tts_engines.values()).index(
                profile.get_profile_var(
                    ['tts_engine']
                )
            )
        ]
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
                _("Available implementations: ") + choices_text(
                    "%s. " % list(tts_engines.keys())
                )
            ),
            response
        )
        try:
            profile.set_profile_var(['tts_engine'], tts_engines[response])
        except KeyError:
            print(alert_text(_("Unrecognized option.")))
    print("")
    # Deal with special cases
    if(profile.get_profile_var(["tts_engine"]) == "espeak-tts"):
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
    elif(profile.get_profile_var(["tts_engine"]) == "festival-tts"):
        # tts_engine: festival-tts
        print(
            "    " + instruction_text(
                _("Use the festival command to set the default voice.")
            )
        )
    elif(profile.get_profile_var(["tts_engine"]) == "flite-tts"):
        try:
            voices = run_command.run_command(['flite', '-lv']).split(" ")[2:-1]
            print(
                "    " + instruction_text(
                    _("Available voices:")
                ) + " " + choices_text(
                    "%s. " % voices
                )
            )
            voice = profile.get_profile_var(["flite-tts", "voice"])
            if not voice:
                try:
                    voice = voices[voices.index("slt")]
                except ValueError:
                    voice = None
            profile.set_profile_var(
                ["flite-tts", "voice"],
                simple_input(
                    format_prompt(
                        "?",
                        _("Select a voice")
                    ),
                    voice
                )
            )
        except OSError:
            print(alert_text(_("FLite does not appear to be installed")))
            print(instruction_text(_("Please install it using:")))
            print("  $ " + success_text("sudo apt install flite"))
            print(instruction_text(
                _("then re-run Naomi with the --repopulate flag")
            ))
            print("  $ " + success_text("./Naomi.py --repopulate"))
    elif(profile.get_profile_var(["tts_engine"]) == "pico-tts"):
        pass
    elif(profile.get_profile_var(["tts_engine"]) == "ivona-tts"):
        print(
            "    " + instruction_text(
                _("You will now need to enter your Ivona account information.")
            )
        )
        print("")
        url = url_text(
            "https://www.ivona.com/us/account/speechcloud/creation/"
        )
        print(
            "    " + instruction_text(
                _("You will need to create an account at %s") % url_text(url)
            )
        )
        print(
            " " + instruction_text(
                _("if you haven't already.")
            )
        )
        print("")
        profile.set_profile_var(
            ["ivona-tts", "access_key"],
            simple_input(
                format_prompt(
                    "?",
                    _("What is your Access key?")
                ),
                profile.get_profile_var(["ivona-tts", "access_key"])
            )
        )
        profile.set_profile_var(
            ["ivona-tts", "secret_key"],
            simple_input(
                format_prompt(
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
            simple_input(
                format_prompt(
                    "?",
                    _("Which voice do you want") + " " + default_text(
                        _("(default is Brian)")
                    ) + question_text("?")
                ),
                temp
            )
        )
    elif(profile.get_profile_var(["tts_engine"]) == "mary-tts"):
        profile.set_profile_var(
            ["mary-tts", "server"],
            simple_input(
                format_prompt(
                    "?",
                    _("Server?")
                ),
                profile.get_profile_var(["mary-tts", "server"])
            )
        )
        profile.set_profile_var(
            ["mary-tts", "port"],
            simple_input(
                format_prompt(
                    "?",
                    "Port?"
                ),
                profile.get_profile_var(["mary-tts", "port"])
            )
        )
        profile.set_profile_var(
            ["mary-tts", "language"],
            simple_input(
                format_prompt(
                    "?",
                    _("Language?")
                ),
                profile.get_profile_var(["mary-tts", "language"])
            )
        )
        profile.set_profile_var(
            ["mary-tts", "voice"],
            simple_input(
                format_prompt(
                    "?",
                    _("Voice?")
                ),
                profile.get_profile_var(["mary-tts", "voice"])
            )
        )


def get_beep_or_voice():
    # Getting information to beep or not beep
    print(
        "    " + instruction_text(
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
        _("{beep} for beeps or {voice} for voice.").format(
            beep=choices_text() + beep_choice + instruction_text(),
            voice=choices_text() + voice_choice + instruction_text()
        )
    )
    response = simple_input(
        format_prompt(
            "?",
            _("({beep}) for beeps or ({voice}) for voice.").format(
                beep=choices_text() + beep_choice + instruction_text(),
                voice=choices_text() + voice_choice + instruction_text()
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
        response = simple_input(
            alert_text(
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
            "    " + instruction_text(
                _("Type the words I should say after hearing my wake word: %s")
                % profile.get_profile_var(["keyword"])
            )
        )
        print("")
        areplyRespon = None
        while(not areplyRespon):
            areply = simple_input(
                format_prompt(
                    "?",
                    _("Reply")
                ),
                profile.get_profile_var(["active_stt", "reply"])
            )
            areplyRespon = None
            while(areplyRespon is None):
                print("")
                areplyRespon = simple_yes_no(
                    areply + " - " + _("Is this correct?")
                )
        profile.set_profile_var(['active_stt', 'reply'], areply)
        separator()
        print(
            "    " + instruction_text(
                _("Type the words I should say after hearing a command")
            )
        )
        aresponseRespon = None
        while(not aresponseRespon):
            aresponse = simple_input(
                format_prompt(
                    "?",
                    _("Response")
                ),
                profile.get_profile_var(["active_stt", "response"])
            )
            print("")
            aresponseRespon = None
            while(aresponseRespon is None):
                aresponseRespon = simple_yes_no(
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
    audioengine_plugins = pluginstore.PluginStore(
        [os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "plugins",
            "audioengine"
        )]
    )
    audioengine_plugins.detect_plugins()
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

    print(instruction_text(_("Please select an audio engine.")))
    try:
        response = audioengines[
            audioengines.index(
                profile.get_profile_var(['audio_engine'])
            )
        ]
    except (ValueError):
        response = "pyaudio"
    once = False
    while not ((once) and (response in audioengines)):
        audioengines = get_audio_engines()
        once = True
        response = simple_input(
            "    " + _("Available implementations:") + " " + choices_text(
                ("%s" % audioengines)
            ) + instruction_text("."),
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
    output_devices = [device.slug for device in audio_engine.get_devices(
        device_type=audioengine.DEVICE_TYPE_OUTPUT
    )]
    output_device_slug = profile.get_profile_var(["audio", "output_device"])
    if not output_device_slug:
        output_device_slug = audio_engine.get_default_device(output=True).slug
    heard = None
    once = False
    while not (once and heard):
        print(instruction_text(_("Please choose an output device")))
        while not ((once) and (output_device_slug in output_devices)):
            once = True
            output_device_slug = simple_input(
                instruction_text(
                    _("Available output devices:") + " "
                ) + choices_text(
                    ", ".join(output_devices)
                ),
                output_device_slug
            )
        profile.set_profile_var(["audio", "output_device"], output_device_slug)
        # try playing a sound
        # FIXME Set the following defaults to what is in the
        # configuration file
        output_chunksize = profile.get_profile_var(
            ['output_chunksize'],
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
            print(instruction_text(_("Testing device by playing a sound")))
            output_device = audio_engine.get_device_by_slug(output_device_slug)
            try:
                output_device.play_file(
                    filename,
                    chunksize=output_chunksize,
                    add_padding=output_add_padding
                )
                heard = simple_yes_no(
                    _("Were you able to hear the beep?")
                )
                if not (heard):
                    print(
                        instruction_text(" ".join(
                            _("The volume on your device may be too low."),
                            _("You should be able to use 'alsamixer'"),
                            _("to set the volume level.")
                        ))
                    )
                    heard = simple_yes_no(
                        instruction_text(
                            _("Do you want to continue now and fix the volume later?")
                        )
                    )
                    if not (heard):
                        once = False
            except audioengine.UnsupportedFormat as e:
                print(alert_text(str(e)))
                print(
                    instruction_text(
                        _("Output format not supported on this device.")
                    )
                )
                print(
                    instruction_text(
                        _("Please choose a different device.")
                    )
                )
                print("")
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
        print(instruction_text(_("Please choose an input device")))
        once = True
        input_device_slug = simple_input(
            _("Available input devices:") + " " + choices_text(
                ", ".join(input_devices)
            ),
            input_device_slug
        )
        profile.set_profile_var(["audio", "input_device"], input_device_slug)
        # try recording a sample
        test = simple_yes_no(
            _("Would you like me to test your selection by recording your voice and playing it back to you?")
        )
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
                instruction_text(
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
                            alert_text(
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
                        soundlevel = float(audioop.rms("".join(frames), 2))
                        if (soundlevel < threshold):
                            print(alert_text(" ".join(
                                _("No sound detected."),
                                _("Setting threshold from {t} to {s}").format(
                                    t=threshold,
                                    s=soundlevel
                                )
                            )))
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
                                success_text(
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
                    heard = simple_yes_no(
                        _("Did you hear yourself?")
                    )
                    if (heard):
                        replay = False
                        once = True
                    else:
                        replay = simple_yes_no(
                            _("Replay?")
                        )
                        if (not replay):
                            skip = simple_yes_no(
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
    #
    # AustinC; Implemented new UX for the population process.
    # For population blessings is used to handle colors,
    # formatting, & and screen isolation.
    #
    # For plugin & general use elsewhere, blessings or
    # coloredformatting.py can be used.
    #
    select_language()
    separator()

    precheck()
    separator()

    greet_user()
    separator()

    get_wakeword()
    separator()

    get_user_name()
    separator()

    get_email_info()
    separator()

    get_phone_info()
    separator()

    get_notification_info()
    separator()

    get_weather_location()
    separator()

    get_timezone()
    separator()

    get_stt_engine()
    separator()

    get_tts_engine()
    separator()

    get_beep_or_voice()
    separator()

    select_audio_engine()
    separator()

    get_output_device()
    separator()

    get_input_device()
    separator()

    # write to profile
    print(
        "    " + status_text(
            _("Writing to profile...")
        )
    )
    profile.save_profile()
    separator()
    print("    " + success_text(_("Done.")) + normal_text())


if __name__ == "__main__":
    print("This program can no longer be run directly.")
    print("Please run the Populate.py program from the")
    print("Naomi root directory.")
