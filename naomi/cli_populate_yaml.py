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
from blessings import Terminal
# AaronC; encrypt is going to be a placeholder for an actual
# symmetric cipher so passwords are not stored in plain text.
# from . import encrypt



def run():
    #
    # AustinC; Implemented new UX for the population process.
    # For population blessings is used to handle colors,
    # formatting, & and screen isolation.
    #
    # For plugin & general use elsewhere, blessings or
    # coloredformatting.py can be used.
    #
    t = Terminal()
    with t.fullscreen():
        
        profile = {}
        language = ""
        
        #
        # AustinC; can't use français due to the special char "ç"
        # it breaks due to it being out of range for ascii
        #
        while not language or (language.lower() != 'en-english' and
                           language.lower() != 'fr-french' and
                           language.lower() != 'de-deutsch'):

            print("")
            print("")
            print("")
            print t.bold_blue("    Naomi Language Selector")
            print("")
            print("")
            print t.bold_white("    EN-English")
            print t.bold_white("    FR-French")
            print t.bold_white("    DE-Deutsch")
            print("")
            language = raw_input(t.bold_white + '[' +
                                 t.bold_yellow + '?' +
                                 t.bold_white + ']' +
                                 ' Select Language: ')
        if(language.lower() == 'en-english'):
            language = 'en-US'
        elif(language.lower() == 'fr-french'):
            language = 'fr-FR'
        elif(language.lower() == 'de-deutsch'):
            language = 'de-DE'
        #else:
            #print("TESTERROR")
            #t.red + ">>"
            #t.bold_white + "Sorry, that is not a valid anwser."

        profile['language'] = language

        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations, profile)
        print("")
        print("")
        print("")
        print t.bold_blue(translator.gettext("    Hello, I'm Naomi, your Personnal Assistant."))
        print("")
        print t.bold_blue(translator.gettext("    Welcome to the profile populator."))
        print("")
        print t.bold_blue(translator.gettext("    If, at any step, you would prefer not to enter " +
                                 "the requested information"))
        print t.bold_blue(translator.gettext("    just hit 'Enter' with a blank field to " +
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
                t.bold_white + '[' +
                t.bold_yellow + '?' +
                t.bold_white + ']' +
                ' First, what name would you like to call me by?'
            )
        )
        print("")
        print("")
        print("")

        # your name
        print(translator.gettext(t.bold_blue("    Now please tell me a little about yourself.")))
        print("")
        simple_request('first_name', translator.gettext(
                                                        t.bold_white + '[' +
                                                        t.bold_yellow + '?' +
                                                        t.bold_white + ']' +
                                                        ' What is your first name?'))
        print("")
        simple_request('last_name', translator.gettext(
                                                        t.bold_white + '[' +
                                                        t.bold_yellow + '?' +
                                                        t.bold_white + ']' +
                                                        ' What is your last name?'))
        print("")
        print("")
        print("")

        # gmail
        print(translator.gettext(t.bold_blue +
            "    I can use your Gmail account to send notifications to you."
        ))
        print("")
        print(translator.gettext("    Alternatively, you can skip this step "))
        print(translator.gettext("    (or just fill in the email address if you " +
                                 "want to receive email notifications)"))
        print(translator.gettext("    and setup a Mailgun account, as at "))
        print(translator.gettext(t.bold_yellow + "    http://naomiproject.github.io/documentation/" +
                                                 "software/#mailgun.\n"))
        simple_request(
            'gmail_address',
            translator.gettext(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                ' What is your Gmail address? '))
        
        # FIXME This needs to be anything but plaintext.
        # AaronC 2018-07-29 I've looked into this and the problem that needs to
        # be solved here is a casual sort of hacker - like if you are working on
        # your configuration file and your spouse is looking over your shoulder to
        # get your password. I know that there are standard ways of dealing with
        # this. I wonder how Thunderbird/Firefox deals with this.
        profile['gmail_password'] = getpass()
        print("")
        print("")
        print("")

        # phone number
        def clean_number(s):
            return re.sub(r'[^0-9]', '', s)
        
        print(translator.gettext(t.bold_blue +
            "    I can use your phone number to send notifications to you."
        ))
        print(translator.gettext("    Alternatively, you can skip this step "))
        print("")
        print(translator.gettext(t.red+"    No country codes!"+t.bold_blue+" Any dashes or spaces will be removed for you"))
        print("")
        phone_number = clean_number(
            raw_input(
                translator.gettext(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " What is your Phone number? "
                )
            )
        )
        profile['phone_number'] = phone_number
        print("")
        print("")
        print("")

        # carrier
        print(translator.gettext(t.bold_blue+"    What is your phone carrier (for sending text notifications)."))
        print(translator.gettext("    If you have a US phone number, you can enter one of the following:"))
        print(translator.gettext("    'AT&T', 'Verizon', 'T-Mobile' "+t.red+"(without the quotes)."))
        print("")
        print(translator.gettext(t.bold_blue+"    If your carrier isn't listed or you have an international"))
        print(translator.gettext("    number, go to "+t.bold_yellow+"http://www.emailtextmessages.com"))
        print(translator.gettext(t.bold_blue+"    and enter the email suffix for your carrier (e.g., for Virgin Mobile, enter "))
        print(translator.gettext("    'vmobl.com'; for T-Mobile Germany, enter 't-d1-sms.de')."))
        print("")
        carrier = raw_input(translator.gettext(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " What is your Carrier? "))
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

        print("")
        print("")
        print("")
        print(translator.gettext(t.bold_blue+"    For weather information, please enter your 5-digit zipcode (e.g., 08544)."))
        print(translator.gettext("    If you are outside the US, insert the name of the nearest big town/city."))
        print("")
        location = raw_input(translator.gettext(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " What is your location? "))
        
        while location and not verifyLocation(location):
            print(translator.gettext(t.red+"Weather not found. " +
                                     "Please try another location."))
            location = raw_input(translator.gettext(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " What is your location? "))
        if location:
            profile['location'] = location
        print("")
        print("")
        print("")

        # timezone
        # FIXME AaronC 2018-07-26 Knowing the zip code, you should be
        # able to work out the time zone.
        # Also, sending me to a wikipedia page to configure this? Really?
        print(translator.gettext(t.bold_blue+"    Please enter a timezone from the list located in the TZ*"))
        print(translator.gettext("    column at "+t.bold_yellow+"http://en.wikipedia.org/wiki/List_of_tz_database_time_zones"))
        print(translator.gettext(t.bold_blue+"    or none at all."))
        print("")
        tz = raw_input(translator.gettext(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " What is your timezone? "))
        while tz:
            try:
                pytz.timezone(tz)
                profile['timezone'] = tz
                break
            except pytz.exceptions.UnknownTimeZoneError:
                print(translator.gettext(t.red+"Not a valid timezone. Try again."))
                tz = raw_input(translator.gettext(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " What is your timezone? "))
        print("")
        print("")
        print("")
        
        print(translator.gettext(t.bold_blue+"    Would you prefer to have notifications sent by"))
        print(translator.gettext("    email (E) or text message (T)?"))
        print("")
        response = raw_input(translator.gettext(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " Email (E) or Text message (T)? "))
        
        while not response or (response != 'E' and response != 'T'):
            print("")
            response = raw_input(translator.gettext(t.red+
                "Please choose email (E) or text message (T)! "+t.bold_white
            ))
        profile['prefers_email'] = (response == 'E')
        print("")
        print("")
        print("")

        stt_engines = {
            "PocketSphinx": "sphinx",
            "Google Voice": "google",
            "Watson": "watson-stt",
            "Kaldi": "kaldigstserver-stt",
            "Julius": "julius-stt"
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
    
        print(translator.gettext(t.bold_blue+"    If you would like to choose a specific speech to text(STT) engine, please specify which!"))
        print("")
        print(translator.gettext("    Available implementations: " +t.yellow+"%s. ")% stt_engines.keys())
        print("")
        response = raw_input(
            translator.gettext(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " (Press Enter to default to PocketSphinx): "
            )
        )
        print("")
        if (response in stt_engines):
            profile['stt_engine'] = stt_engines[response]
        else:
            print(translator.gettext(
                t.red+"Unrecognized option. " +
                t.bold_white+"Setting speech to text engine to "+t.yellow+"Pocketsphinx."+t.bold_white
            ))
            profile['stt_engine'] = 'sphinx'
        print("")
        print("")
        print("")
        # Handle special cases here
        if(profile['stt_engine'] == 'google'):
            # Set the api key (I'm not sure this actually works anymore,
            # need to test)
            key = raw_input(translator.gettext(
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                " Please enter your API key: "))
            profile["keys"] = {"GOOGLE_SPEECH": key}
            print("")
            print("")
            print("")
        if(profile['stt_engine'] == 'watson-stt'):
            profile["watson_stt"] = {}
            username = raw_input(translator.gettext(
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                " Please enter your watson username: "))
            profile["watson_stt"]["username"] = username
            # FIXME AaronC 2018-07-29 - another password. Not as crucial as
            # protecting the user's email password but still...
            profile["watson_stt"]["password"] = getpass()
            print("")
            print("")
            print("")
        if(profile['stt_engine'] == 'kaldigstserver-stt'):
            profile['kaldigstserver-stt'] = {}
            print(translator.gettext(t.bold_blue+"    I need your Kaldi g-streamer server url to continue"))
            print(translator.gettext("    (default is "+t.yellow+"http://localhost:8888/client/dynamic/recognize)"))
            print("")
            profile['kaldigstserver-stt']['url'] = raw_input(translator.gettext(
                                                                                t.bold_white + '[' +
                                                                                t.bold_cyan + '!' +
                                                                                t.bold_white + ']' +
                                                                                " Please enter your server url: "))
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
            profile["julius"] = {}
            profile["julius"]["hmmdefs"] = raw_input(
                translator.gettext(
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                " Enter path to julius hmm defs: ")
            )
            profile["julius"]["tiedlist"] = raw_input(
                translator.gettext(
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                " Enter path to julius tied list: ")
            )
            profile["julius"]["lexicon"] = raw_input(
                translator.gettext(
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                " Enter path to julius lexicon: ")
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
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                t.red+" I cannot locate phonetisaurus-g2p(fst) in any of the standard locations."
                    ))
                    print(translator.gettext(
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                t.red+" (either phonetisaurus-g2p,phonetisaurus-g2pfst, or try using the find command)"
                    ))
                    phonetisaurus_executable = raw_input(translator.gettext(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " What is the name of your phonetisaurus-g2p program? "
                    ))

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
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                t.red+" I could not find your hmm directory in any of the standard places"
                    ))
                    hmm_dir = raw_input(translator.gettext(
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                " Please enter the path to your hmm directory: "
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
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                t.red+"I could not find your fst model (usually either g014b2b.fst or model.fst)"
                    ))
                    fst_model = raw_input(translator.gettext(
                                t.bold_white + '[' +
                                t.bold_cyan + '!' +
                                t.bold_white + ']' +
                                " Please enter the path to your fst model: "
                    ))
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
        print(translator.gettext(t.bold_blue+"    If you would like to choose a specific text to speech (TTS) engine,"))
        print(translator.gettext("    please specify which."))
        print("")
        print(translator.gettext("    Available implementations: " +t.yellow+"%s. "))
        print("")
        response = raw_input(translator.gettext(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " (Press Enter to default to Festival): "
        ) % tts_engines.keys())
        if(response in tts_engines.keys()):
            profile['tts_engine'] = tts_engines[response]
        else:
            print(translator.gettext(
                t.red+"Unrecognized option." +
                t.bold_white+"Setting text to speech engine to " +
                t.yellow+"Festival."
            ))
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
            print(t.bold_blue+"    You can set the default voice in the config file as so:")
            print("")
            print("    tts_engine: flite-tts")
            print("    flite-tts:")
            print("        voice:'slt'")
            print("")
            print("")
            print("")
        # elif( profile["tts_engine"]=="pico-tts" ):
        #    # there is nothing to configure, apparently
        elif(profile["tts_engine"] == "ivona-tts"):
            print(t.bold_blue+"    You will now need to enter your Ivona account information.")
            print("")
            print("    You will need to create an account at")
            print(t.yellow+"    https://www.ivona.com/us/account/speechcloud/creation/"+t.bold_blue+"if you haven't already.")
            print("")
            profile["ivona-tts"] = {}
            profile["ivona-tts"]["access_key"] = raw_input(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " What is your Access key? ")
            profile["ivona-tts"]["secret_key"] = raw_input(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " What is your Secret key? ")
            profile["ivona-tts"]["voice"] = raw_input(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " What Voice do you want "+t.yellow+"(default is Brian)"+t.bold_white+"? ")
            print("")
            print("")
            print("")
        elif(profile["tts_engine"] == "mary-tts"):
            profile["mary-tts"] = {}
            profile["mary-tts"]["server"] = raw_input(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " Server? ")
            profile["mary-tts"]["port"] = raw_input(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " Port? ")
            profile["mary-tts"]["language"] = raw_input(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " Language? ")
            profile["mary-tts"]["voice"] = raw_input(
                                t.bold_white + '[' +
                                t.bold_yellow + '?' +
                                t.bold_white + ']' +
                                " Voice? ")
            print("")
            print("")
            print("")
        # Getting information to beep or not beep
        print(translator.gettext(t.bold_blue+"    Naomi's active listener has two modes Beep or Voice."))
        
        response = raw_input(translator.gettext(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " (B) for beeps or (V) for voice. "
        ))
        while not response or (response != 'B' and response != 'V'):
            response = raw_input(translator.gettext(t.red+
                "Please choose beeps (B) or voice (V): "+t.bold_white
            ))
        if(response is not "B"):
            print("")
            print("")
            print("")
            print(translator.gettext(t.bold_blue+"    Type the words that Naomi will respond with after her name is called."))
            print("")
            areply = raw_input(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " Reply: ")
            print("")
            print(areply + t.bold_blue +" Is this correct?")
            print("")
            areplyRespon = raw_input(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " Y/N? ")
            while not(areplyRespon.upper() == 'Y' or areplyRespon.upper() == 'N'):
                areplyRespon = raw_input(
                                    t.bold_white + '[' +
                                    t.red + '!' +
                                    t.bold_white + ']' +
                                    " Y/N? ")
            if(areplyRespon != "Y"):
                areply = raw_input(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " Reply: ")
            profile['active_stt'] = {'reply': areply}
            print("")
            print("")
            print("")
            print(t.bold_blue+"    Type the words that Naomi will say after hearing you.")
            aresponse = raw_input(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " Response: ")
            print("")
            print(aresponse + t.bold_blue+" Is this correct?")
            print("")
            aresponseRespon = raw_input(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " Y/N? ")
            while(aresponseRespon != 'Y' and aresponseRespon != 'N'):
                aresponseRespon = raw_input(
                                    t.bold_white + '[' +
                                    t.red + '!' +
                                    t.bold_white + ']' +
                                    " Y/N? ")
            if(aresponseRespon is not "Y"):
                aresponse = raw_input(
                                    t.bold_white + '[' +
                                    t.bold_yellow + '?' +
                                    t.bold_white + ']' +
                                    " Response: ")
            profile['active_stt'] = {'response': aresponse}
            print("")
            print("")
            print("")
            
    
        # write to profile
        print(t.bold_magenta+"    Writing to profile...")
        if not os.path.exists(paths.CONFIG_PATH):
            os.makedirs(paths.CONFIG_PATH)
        outputFile = open(paths.config("profile.yml"), "w")
        yaml.dump(profile, outputFile, default_flow_style=False)
        print("")
        print("")
        print("")
        print(t.bold_green+"    Done.")


if __name__ == "__main__":
    run()