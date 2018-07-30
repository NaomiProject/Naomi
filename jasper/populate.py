# -*- coding: utf-8 -*-
import feedparser
from getpass import getpass
import os
import paths
import pytz
import re
import yaml
if __name__ == '__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import i18n
# AaronC encrypt is going to be a placeholder for an actual
# symmetric cipher so passwords are not stored in plain text.
# from . import encrypt


def run():
    profile = {}
    # language
    # language = raw_input("\nWhat is your language ?" +
    #                     "available: en-US, fr-FR, de-DE : \n")
    language = ""
    while not language or (language.lower() != 'english' and
                           language.lower() != 'français' and
                           language.lower() != 'deutsche'):
        print("")
        print("English")
        print("Français")
        language = raw_input("Deutsche: ")
    if(language.lower() == 'english'):
        language = 'en-US'
    elif(language.lower() == 'français'):
        language = 'fr-FR'
    elif(language.lower() == 'deutsche'):
        language = 'de-DE'

    profile['language'] = language

    translations = i18n.parse_translations(paths.data('locale'))
    translator = i18n.GettextMixin(translations, profile)
    print("")
    print(translator.gettext("Hi i'm your Personnal Assistant."))
    print(translator.gettext("Welcome to the profile populator. "))
    print(translator.gettext("If, at any step, you'd prefer not to enter " +
                             "the requested information"))
    print(translator.gettext("just hit 'Enter' with a blank field to " +
                             "continue."))
    print("")

    def simple_request(var, cleanVar, cleanInput=None):
        input = raw_input(translator.gettext(cleanVar) + ": ")
        if input:
            if cleanInput:
                input = cleanInput(input)
            profile[var] = input

    # my name
    simple_request(
        'keyword',
        translator.gettext(
            'First, what name would you like to call me by?'
        )
    )
    print("")

    # your name
    print(translator.gettext("Now please tell me a little about yourself."))
    simple_request('first_name', translator.gettext('What is your first name'))
    simple_request('last_name', translator.gettext('What is your last name'))
    print("")

    # gmail
    print(translator.gettext(
        "I can use your GMail account to send notifications to you."
    ))
    print(translator.gettext(
          "Alternatively, " +
          "you can skip this step " +
          "(or just fill in the email address if you " +
          "want to receive email notifications) and setup a Mailgun " +
          "account, as at " +
          "http://jasperproject.github.io/documentation/" +
          "software/#mailgun.\n"))
    simple_request(
        'gmail_address',
        translator.gettext('Gmail address')
    )
    # FIXME This needs to be anything but plaintext.
    # AaronC 2018-07-29 I've looked into this and the problem that needs to
    # be solved here is a casual sort of hacker - like if you are working on
    # your configuration file and your spouse is looking over your shoulder to
    # get your password. I know that there are standard ways of dealing with
    # this. I wonder how Thunderbird/Firefox deals with this.
    profile['gmail_password'] = getpass()
    print("")

    # phone number
    def clean_number(s):
        return re.sub(r'[^0-9]', '', s)

    phone_number = clean_number(
        raw_input(
            translator.gettext(
                "Phone number (no country code). Any dashes or spaces will " +
                "be removed for you: "
            )
        )
    )
    profile['phone_number'] = phone_number
    print("")

    # carrier
    print(translator.gettext("Phone carrier (for sending text notifications)."))
    print(translator.gettext("If you have a US phone number, you can enter " +
          "one of the following: 'AT&T', 'Verizon', 'T-Mobile' " +
          "(without the quotes). " +
          "If your carrier isn't listed or you have an international " +
          "number, go to http://www.emailtextmessages.com and enter the " +
          "email suffix for your carrier (e.g., for Virgin Mobile, enter " +
          "'vmobl.com'; for T-Mobile Germany, enter 't-d1-sms.de')."))
    carrier = raw_input(translator.gettext('Carrier: '))
    if carrier == 'AT&T':
        profile['carrier'] = 'txt.att.net'
    elif carrier == 'Verizon':
        profile['carrier'] = 'vtext.com'
    elif carrier == 'T-Mobile':
        profile['carrier'] = 'tmomail.net'
    else:
        profile['carrier'] = carrier
    print("")

    # location
    def verifyLocation(place):
        feed = feedparser.parse('http://rss.wunderground.com/auto/rss_full/' +
                                place)
        numEntries = len(feed['entries'])
        if numEntries == 0:
            return False
        else:
            print(translator.gettext("Location saved as ") +
                  feed['feed']['description'][33:])
            return True

    print(translator.gettext("Location should be a 5-digit US zipcode " +
          "(e.g., 08544). If you are outside the US, insert the name of " +
          "your nearest big town/city.  For weather requests."))
    location = raw_input(translator.gettext("Location: "))
    while location and not verifyLocation(location):
        print(translator.gettext("Weather not found. " +
                                 "Please try another location."))
        location = raw_input(translator.gettext("Location: "))
    if location:
        profile['location'] = location
    print("")

    # timezone
    # FIXME AaronC 2018-07-26 Knowing the zip code, you should be
    # able to work out the time zone.
    # Also, sending me to a wikipedia page to configure this? Really?
    print(translator.gettext(
          "Please enter a timezone from the list located in the TZ* " +
          "column at http://en.wikipedia.org/wiki/" +
          "List_of_tz_database_time_zones, or none at all."))
    tz = raw_input(translator.gettext("Timezone: "))
    while tz:
        try:
            pytz.timezone(tz)
            profile['timezone'] = tz
            break
        except pytz.exceptions.UnknownTimeZoneError:
            print(translator.gettext("Not a valid timezone. Try again."))
            tz = raw_input("Timezone: ")
    print("")

    response = raw_input(translator.gettext(
        "Would you prefer to have notifications sent by " +
        "email (E) or text message (T)? "
    ))
    while not response or (response != 'E' and response != 'T'):
        response = raw_input(translator.gettext(
            "Please choose email (E) or text message (T): "
        ))
    profile['prefers_email'] = (response == 'E')
    print("")

    stt_engines = {
        "PocketSphinx": "sphinx",
        "Google Voice": "google",
        "Watson": "watson",
        "Kaldi": "kaldigstserver-stt",
        "Julius": "julius"
    }

    # This searches some standard places (/bin, /usr/bin, /usr/local/bin)
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

    print(translator.gettext(
        "If you would like to choose a specific speech to text " +
        "(STT) engine, please specify which."
    ))
    response = raw_input(
        translator.gettext(
            "Available implementations: %s. " +
            "(Press Enter to default to PocketSphinx): "
        ) % stt_engines.keys()
    )
    if (response in stt_engines):
        profile['stt_engine'] = stt_engines[response]
    else:
        print(translator.gettext(
            "Unrecognized option. " +
            "Setting speech to text engine to Pocketsphinx."
        ))
        profile['stt_engine'] = 'sphinx'
    # Handle special cases here
    if(profile['stt_engine'] == 'google'):
        # Set the api key (I'm not sure this actually works anymore,
        # need to test)
        key = raw_input(translator.gettext("Please enter your API key: "))
        profile["keys"] = {"GOOGLE_SPEECH": key}
    if(profile['stt_engine'] == 'watson'):
        profile["watson_stt"] = {}
        username = raw_input(translator.gettext("Enter your watson username:"))
        profile["watson_stt"]["username"] = username
        # FIXME AaronC 2018-07-29 - another password. Not as crucial as
        # protecting the user's email password but still...
        profile["watson_stt"]["password"] = getpass()
    if(profile['stt_engine'] == 'kaldigstserver-stt'):
        profile['kaldigstserver-stt'] = {}
        profile['kaldigstserver-stt']['url'] = raw_input(
            translator.gettext(
                "Enter your Kaldi g-streamer searver url " +
                "(default is http://localhost:8888/client/dynamic/recognize)"
            )
        )
    if(profile['stt_engine'] == 'julius'):
        # stt_engine: julius
        # julius:
        #     hmmdefs:  '/path/to/your/hmmdefs'
        #     tiedlist: '/path/to/your/tiedlist'
        #     lexicon:  '/path/to/your/lexicon.tgz'
        #     lexicon_archive_member: 'VoxForge/VoxForgeDict'
        #           only needed if lexicon is a tar/tar.gz archive
        profile["julius"] = {}
        profile["julius"]["hmmdefs"] = raw_input(
            translator.gettext("Enter path to julius hmm defs:")
        )
        profile["julius"]["tiedlist"] = raw_input(
            translator.gettext("Enter path to julius tied list:")
        )
        profile["julius"]["lexicon"] = raw_input(
            translator.gettext("Enter path to julius lexicon:")
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
        profile["pocketsphinx"] = {}
        # AaronC 2018-07-29 Since pocketsphinx/phonetisaurus is assumed, make
        # this the default at the end
        # is the phonetisaurus program phonetisaurus-g2p (old version)
        # or phonetisaurus-g2pfst?
        phonetisaurus_executable = ''
        while not(phonetisaurus_executable):
            # Let's check some standard places (this is crunchier than actually
            # using "find" but should work in most cases):
            if(CheckProgramExists('phonetisaurus-g2pfst')):
                phonetisaurus_executable = 'phonetisaurus-g2pfst'
            elif(CheckProgramExists('phonetisaurus-g2p')):
                phonetisaurus_executable = 'phonetisaurus-g2p'
            else:
                # AaronC 2018-07-29
                # Ask the user
                # I could force one of those choices, but I would like to leave
                # it open for the user to select a different option because
                # they may have renamed the executable. Of course, this
                # greatly increates the possibility of the user fat-fingering
                # the name at this point.
                # Might be good to add an "are you sure?" below if this
                # response is not one of the two standard responses.
                print(translator.gettext(
                    "I cannot locate phonetisaurus-g2p(fst) " +
                    "in any of the standard locations."
                ))
                print(translator.gettext(
                    "What is the name of your phonetisaurus-g2p program?"
                ))
                phonetisaurus_executable = raw_input(translator.gettext(
                    "(either phonetisaurus-g2p or phonetisaurus-g2pfst, " +
                    "try using the find command)"
                ))
        profile['pocketsphinx']['phonetisaurus_executable'] = phonetisaurus_executable
        # We have the following things to configure:
        #  hmm_dir - the default for jasper is "/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k"
        #          - if you install through the pocketsphinx-en-us debian apt package then it is "/usr/share/pocketsphinx/model/en-us/en-us"
        #          - if you install the latest pocketsphinx from source, it should be here: "~/pocketsphinx/model/en-us/en-us"
        #  fst_model -
        #          - the default for jasper is "~/phonetisaurus/g014b2b.fst"
        #          - if you install the latest CMUDict, then it will be at "~/CMUDict/train/model.fst"
        hmm_dir = ""
        while not(hmm_dir):
            if(phonetisaurus_executable == "phonetisaurus-g2pfst"):
                # The hmm_dir should be under the user's home directory
                # in the "~/pocketsphinx/model/en-us/en-us" directory
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
            elif(phonetisaurus_executable == "phonetisaurus-g2p"):
                if(os.path.isdir("/usr/share/pocketsphinx/model/en-us/en-us")):
                    hmm_dir = "/usr/share/pocketsphinx/model/en-us/en-us"
                elif(os.path.isdir("/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k")):
                    hmm_dir = "/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k"
            if not(hmm_dir):
                print(translator.gettext(
                    "I could not find your hmm directory in any " +
                    "of the standard places"
                ))
                hmm_dir = raw_input(translator.gettext(
                    "Please enter the path to your hmm directory:"
                ))
        profile["pocketsphinx"]["hmm_dir"] = hmm_dir
        fst_model = ""
        while not(fst_model):
            if(phonetisaurus_executable == "phonetisaurus-g2pfst"):
                if(os.path.isfile(os.path.join(
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
            else:
                print(translator.gettext(
                    "I could not find your fst model " +
                    "(usually either g014b2b.fst or model.fst)"
                ))
                fst_model = raw_input(translator.gettext(
                    "Please enter the path to your fst model:"
                ))
        profile["pocketsphinx"]["fst_model"] = fst_model
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
    print(translator.gettext(
        "If you would like to choose a specific text to speech (TTS) engine, " +
        "please specify which."
    ))
    response = raw_input(translator.gettext(
        "Available implementations: %s. (Press Enter to default to Festival): "
    ) % tts_engines.keys())
    if(response in tts_engines.keys()):
        profile['tts_engine'] = tts_engines[response]
    else:
        print(translator.gettext(
            "Unrecognized option. Setting text to speech engine to Festival."
        ))
        profile['tts_engine'] = 'festival-tts'
    # Deal with special cases
    if(profile["tts_engine"] == "espeak-tts"):
        # tts_engine: espeak-tts
        print(
            "If you would like to alter the espeak voice, you can use " +
            "the following options in your config file:"
        )
        print("espeak-tts:")
        print("    voice: 'default+m3'   # optional")
        print("    pitch_adjustment: 40  # optional")
        print("    words_per_minute: 160 # optional")
    elif(profile["tts_engine"] == "festival-tts"):
        # tts_engine: festival-tts
        print("Use the festival command to set the default voice.")
    elif(profile["tts_engine"] == "flite-tts"):
        print("You can set the default voice in the config file as so:")
        print("tts_engine: flite-tts")
        print("flite-tts:")
        print("    voice:'slt'")
    # elif( profile["tts_engine"]=="pico-tts" ):
    #    # there is nothing to configure, apparently
    elif(profile["tts_engine"] == "ivona-tts"):
        print("You will now need to enter your Ivona account information.")
        print(
            "You will need to create an account at " +
            "https://www.ivona.com/us/account/speechcloud/creation/ " +
            "if you haven't already."
        )
        profile["ivona-tts"] = {}
        profile["ivona-tts"]["access_key"] = raw_input("Access key:")
        profile["ivona-tts"]["secret_key"] = raw_input("Secret key:")
        profile["ivona-tts"]["voice"] = raw_input("Voice (default is Brian):")
    elif(profile["tts_engine"] == "mary-tts"):
        profile["mary-tts"] = {}
        profile["mary-tts"]["server"] = raw_input("Server:")
        profile["mary-tts"]["port"] = raw_input("Port:")
        profile["mary-tts"]["language"] = raw_input("Language:")
        profile["mary-tts"]["voice"] = raw_input("Voice:")
    # Getting information to beep or not beep
    print(translator.gettext(
        "Jasper's active listener has two modes Beep or Voice."
    ))
    response = raw_input(translator.gettext(
        "Please Choose (B) for beeps or (V) for voice. "
    ))
    while not response or (response != 'B' and response != 'V'):
        response = raw_input(translator.gettext(
            "Please choose beeps (B) or voice (V): "
        ))
    if(response is not "B"):
        print(translator.gettext(
            "Type the words that jasper will respond with " +
            "after its name being called."
        ))
        areply = raw_input("Reply: ")
        print(areply + " Is this correct?")
        areplyRespon = raw_input("Y/N?")
        while not(areplyRespon.upper() == 'Y' or areplyRespon.upper() == 'N'):
            areplyRespon = raw_input("Y/N?")
        if(areplyRespon != "Y"):
            areply = raw_input("Reply: ")
        profile['active_stt'] = {'reply': areply}
        print("Type the words that jasper will say after hearing you.")
        aresponse = raw_input("Response: ")
        print(aresponse + "\n is this correct?")
        aresponseRespon = raw_input("Y/N?")
        while(aresponseRespon != 'Y' and aresponseRespon != 'N'):
            aresponseRespon = raw_input("Y/N?")
        if(aresponseRespon is not "Y"):
            aresponse = raw_input("Response: ")
        profile['active_stt'] = {'response': aresponse}

    # write to profile
    print("Writing to profile...")
    if not os.path.exists(paths.CONFIG_PATH):
        os.makedirs(paths.CONFIG_PATH)
    outputFile = open(paths.config("profile.yml"), "w")
    yaml.dump(profile, outputFile, default_flow_style=False)
    print("Done.")


if __name__ == "__main__":
    run()
