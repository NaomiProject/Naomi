from . import i18n
from . import paths
from . import profile
from getpass import getpass
import re
from blessings import Terminal


_ = None
affirmative = ""
negative = ""
audioengine_plugins = None
t = None


def get_language(language=None, once=False):
    global _, t, affirmative, negative
    t = Terminal()
    if language is None:
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations, profile.get_profile())
        _ = translator.gettext
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
        while not (
            (
                once
            )and(
                check_for_value(
                    selected_language.strip().lower(),
                    [
                        x[:len(selected_language)].lower()
                        for x in languages.keys()
                    ]
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

    profile.set_profile_var(['language'], language)
    if(language == 'fr-FR'):
        affirmative = 'oui'
        negative = 'non'
    elif(language == 'de-DE'):
        affirmative = "ja"
        negative = "nein"
    else:
        affirmative = 'yes'
        negative = 'no'
    translations = i18n.parse_translations(paths.data('locale'))
    translator = i18n.GettextMixin(translations, profile.get_profile())
    _ = translator.gettext


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


# AaronC 2018-09-14
# Colors
# This returns to whatever the default color is in the terminal
# properties
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


# AaronC - simple_password is a lot like simple_input, just uses
# getpass instead of input. It does not encrypt the password. That
# happens after the password has been validated.
def simple_password(prompt, default=None):
    prompt += ": "
    prompt += input_text()
    # don't use print here so no automatic carriage return
    # sys.stdout.write(prompt)
    response = getpass(prompt)
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
            print(alert_text("Please select '{}' or '{}'.").format(
                affirmative.upper()[:1],
                negative.upper()[:1]
            ))
    if response == affirmative.lower()[:1]:
        return True
    else:
        return False


# This is a higher level control that takes a "setting" as input
def get_setting(setting, definition):
    # If the language has already been set, no need to change it.
    get_language(once=True)
    active = True
    if("active" in definition):
        try:
            active = definition["active"]()
        except TypeError:
            active = definition["active"]
    if(active):
        controltype = "textbox"
        if("type" in definition):
            controltype = definition["type"].lower()
        if(controltype == "listbox"):
            default = ""
            if("default" in definition):
                default = definition["default"]
            value = profile.get_profile_var(setting, default)
            try:
                options = definition["options"]()
            except TypeError:
                options = definition["options"]
            print(
                "    " + instruction_text(
                    definition["title"]
                )
            )
            print("")
            response = value
            once = False
            while not ((once) and (validate(definition, response))):
                once = True
                tmp_response = simple_input(
                    "    " + instruction_text(
                        _("Available choices:")
                    ) + " " + choices_text(
                        ("{}. ".format(", ".join(sorted(list(options.keys())))))
                    ) + instruction_text('"?" for help'),
                    response
                )
                if(tmp_response.strip() == "?"):
                    # Print the description plus any help text for the control
                    print("")
                    print(instruction_text(definition["description"]))
                    once = False
                    continue
                response = tmp_response
                print("")
                try:
                    profile.set_profile_var(
                        setting,
                        options[response]
                    )
                except KeyError:
                    print(
                        alert_text(
                            _("Unrecognized option.")
                        )
                    )
            print("")
        elif(controltype == "password"):
            default = ""
            if("default" in definition):
                default = definition["default"]
            value = profile.get_profile_password(setting, default)
            print("")
            response = value
            once = False
            while not ((once) and (validate(definition, response))):
                once = True
                tmp_response = simple_password(
                    "    " + instruction_text('{} ("?" for help)'.format(definition["title"])),
                    response
                )
                if(tmp_response.strip() == "?"):
                    # Print the description plus any help text for the control
                    print("")
                    print(instruction_text(definition["description"]))
                    once = False
                    continue
                response = tmp_response
                print("")
                profile.set_profile_password(
                    setting,
                    response
                )
        else:
            # this is the default (textbox)
            default = ""
            if("default" in definition):
                default = definition["default"]
            value = profile.get_profile_var(setting, default)
            print("")
            response = value
            once = False
            while not ((once) and (validate(definition, response))):
                once = True
                tmp_response = simple_input(
                    "    " + instruction_text('{} ("?" for help)'.format(definition["title"])),
                    response
                )
                if(tmp_response.strip() == "?"):
                    # Print the description plus any help text for the control
                    print("")
                    print(instruction_text(definition["description"]))
                    once = False
                    continue
                response = tmp_response
                print("")
                profile.set_profile_var(
                    setting,
                    response
                )
    else:
        # Just set the value to an empty value so we know we don't need to
        # address this again.
        profile.set_profile_var(setting, "")


# FIXME I should put a default for listboxes here so that by default
# any value chosen has to be a member of the options.key() list.
def validate(definition, response):
    valid = False
    if(len(response.strip()) == 0):
        valid = True
    else:
        try:
            validfunction = definition["validation"]
            valid = validfunction(response)
        except KeyError:
            # there is no "validation" property, so anything validates
            valid = True
        except TypeError:
            # Not a function
            validstr = str(definition["validation"]).strip().lower()
            # Is it a boolean?
            if validstr in ('true', 'yes', 'on'):
                valid = True
            elif validstr in ('false', 'no', 'off'):
                valid = False
            elif validstr == 'email':
                valid = True if re.match('^[^@]+@[^@]+\\.[^@\\.]+$', response) else False
            elif validstr in ('int', 'integer'):
                try:
                    valid = str(int(response)) == response
                except ValueError:
                    valid = False
    return valid


def separator():
    print("")
    print("")
    print("")
