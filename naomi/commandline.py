# -*- coding: utf-8 -*-
from blessings import Terminal
from getpass import getpass
from naomi import app_utils
from naomi import i18n
from naomi import paths
from naomi import profile
# from . import coloredformatting as cf
import re
import sys


_ = None
affirmative = ""
negative = ""
audioengine_plugins = None
t = None


# This method gives me a way to print to the terminal while
# the SNRVAD is providing a visualization of how Naomi is
# listening
def println(string):
    # check and see if string ends with a line feed
    addCR = False
    matchgroups = re.match('^(.*)\n$', string, re.MULTILINE)
    if (matchgroups):
        string = matchgroups.groups(0)[0]
        addCR = True
    # clear the current line
    try:
        columns = t.width - 1
    except TypeError:
        columns = 79
    sys.stdout.write("{}{}\r".format(
        string, " " * (columns - len(string)))
    )
    if (addCR):
        sys.stdout.write("\n")
    sys.stdout.flush()


class commandline(object):
    def __init__(self):
        global _, t, affirmative, negative
        t = Terminal()
        # If the language has already been set, no need to change it.
        # If the language has not been set, we will need to set it before
        # interacting with the user
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations)

        _ = translator.gettext
        language = self.get_language(once=True)
        if (language == 'fr-FR'):
            affirmative = 'oui'
            negative = 'non'
        elif (language == 'de-DE'):
            affirmative = "ja"
            negative = "nein"
        else:
            affirmative = 'yes'
            negative = 'no'

    # FIXME this does not belong here.
    def get_language(self, language=None, once=False):
        global _
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
            ) and (
                self.check_for_value(
                    selected_language.strip().lower(),
                    [
                        x[:len(selected_language)].lower()
                        for x in languages.keys()
                    ]
                )
            )
        ):
            once = True
            print("    " + self.instruction_text(_("Language Selector")))
            print("")
            print("")
            for language in languages.keys():
                print("    {}".format(language))
            print("")
            selected_language = self.simple_input(
                self.format_prompt(
                    "?",
                    _('Select Language')
                ),
                selected_language
            ).strip().lower()
            if (len(selected_language) > 0):
                if (self.check_for_value(
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
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations)
        _ = translator.gettext
        return language

    # If value exists in list, return the index
    # of that value (+ 1 so that the first item
    # does not return zero which is interpreted
    # as false), otherwise return None
    @staticmethod
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
    @staticmethod
    def normal_text(text=""):
        return t.normal + text

    # this is for emphasis
    @staticmethod
    def strong_text(text=""):
        return t.bold_cyan + text

    # this is for instructions
    @staticmethod
    def instruction_text(text=""):
        return t.bold_blue + text

    # This is for the brackets surrounding the icon
    @staticmethod
    def icon_text(text=""):
        return t.bold_cyan + text

    # This is for question text
    @staticmethod
    def question_text(text=""):
        return t.bold_blue + text

    # This is for the question icon
    @staticmethod
    def question_icon(text=""):
        return t.bold_yellow + text

    # This is for alert text
    @staticmethod
    def alert_text(text=""):
        return t.bold_red + text

    # This is for the alert icon
    @staticmethod
    def alert_icon(text=""):
        return t.bold_cyan + text

    # This is for listing choices available to choose from
    @staticmethod
    def choices_text(text=""):
        return t.bold_cyan + text

    # This is for displaying the default choice when there is a default
    @staticmethod
    def default_text(text=""):
        return t.normal + text

    # This is for the prompt after the default text
    @staticmethod
    def default_prompt(text="// "):
        return t.bold_blue + text

    # This is the color for the text as the user is entering a choice
    @staticmethod
    def input_text(text=""):
        return t.normal + text

    # This is text for a url
    @staticmethod
    def url_text(text=""):
        return t.bold_cyan + t.underline + text + t.normal

    # This is for a status message
    @staticmethod
    def status_text(text=""):
        return t.bold_magenta + text

    # This is a positive alert
    @staticmethod
    def success_text(text=""):
        return t.bold_green + text

    def format_prompt(self, icon, prompt):
        if (icon == "!"):
            prompt = "".join([
                self.icon_text('['),
                self.alert_icon('!'),
                self.icon_text('] '),
                self.question_text(prompt)
            ])
        elif (icon == "?"):
            prompt = "".join([
                self.icon_text('['),
                self.question_icon('?'),
                self.icon_text('] '),
                self.question_text(prompt)
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
    def simple_input(self, prompt, default=None):
        prompt += ": "
        if (default):
            if isinstance(default, (int, float, bool)):
                default = str(default)
            if isinstance(default, str):
                prompt += self.default_text(default) + self.default_prompt()
            else:
                prompt += self.default_text(', '.join(default)) + self.default_prompt()
        prompt += self.input_text()
        # don't use print here so no automatic carriage return
        # if you pass the prompt to input, it will be written to
        # stderr, so if you are doing something like:
        # $ ./Naomi --debug --repopulate 2>naomi.log
        # to capture stderr to a log and also configure Naomi,
        # it won't work.
        sys.stdout.write(prompt)
        response = input()
        # if the user pressed enter without entering anything,
        # set the response to default
        if (default and not response):
            if (isinstance(default, int) or isinstance(default, float)):
                response = str(default)
            elif (isinstance(default, list)):
                # if the default is a list, convert it to a string
                response = ", ".join(default)
            else:
                response = default
        if not isinstance(response, str):
            response = str(response)
        return response.strip()

    # AaronC - simple_password is a lot like simple_input, just uses
    # getpass instead of input. It does not encrypt the password. That
    # happens after the password has been validated.
    def simple_password(self, prompt, default=None):
        prompt += ": "
        if (default):
            prompt += self.default_text("********") + self.default_prompt()
        prompt += self.input_text()
        # don't use print here so no automatic carriage return
        # sys.stdout.write(prompt)
        response = getpass(prompt)
        # if the user pressed enter without entering anything,
        # set the response to default
        if (default and not response):
            response = default
        return response.strip()

    # AaronC - simple_request is, ironically, more complicated, and
    # populates the profile variable directly.
    # path is the path within profile.yml
    # prompt is the prompt that is displayed to the user
    # cleanInput is a function used to format the text
    def simple_request(self, path, prompt, cleanInput=None):
        input_str = self.simple_input(prompt, profile.get_profile_var(path))
        if input_str:
            if cleanInput:
                input_str = cleanInput(input_str)
            profile.set_profile_var(path, input_str)

    # AaronC Sept 18 2018 This uses affirmative/negative to ask
    # a yes/no question. Returns True for yes and False for no.
    def simple_yes_no(
        self,
        prompt,
        description=None,
        default=None
    ):
        response = ""
        # Make it so the default value is upper case and the non-default value
        # is lower case
        instruction = ""
        if (description):
            instruction = '"?" for help'
        choice_affirmative = affirmative[:1].lower()
        choice_negative = negative[:1].lower()
        if (default is not None):
            if (not isinstance(default, bool)):
                if (not isinstance(default, str)):
                    default = str(default)
                default = app_utils.is_positive(default)
            if (isinstance(default, bool)):
                if (default):
                    choice_affirmative = affirmative[:1].upper()
                    default = choice_affirmative
                else:
                    choice_negative = negative[:1].upper()
                    default = choice_negative
        while (response[:1] not in (affirmative.lower()[:1], negative.lower()[:1])):
            temp_response = self.simple_input(
                self.format_prompt(
                    "?",
                    prompt + self.instruction_text(" (") + self.choices_text(
                        choice_affirmative
                    ) + self.instruction_text("/") + self.choices_text(
                        choice_negative
                    ) + self.instruction_text(")") + instruction
                ),
                default
            ).strip().lower()
            if description and temp_response[:1] == "?":
                print(self.instruction_text(description))
            elif temp_response[:1] in (affirmative.lower()[:1], negative.lower()[:1]):
                response = temp_response
            else:
                print(self.alert_text("Please select '{}' or '{}'.").format(
                    affirmative.upper()[:1],
                    negative.upper()[:1]
                ))
        if response.lower() == affirmative.lower()[:1]:
            return True
        else:
            return False

    # This is a higher level control that takes a "setting" as input
    def get_setting(self, setting, definition):
        # set a default default value
        default = ""
        # if default is defined, then use that value as default
        if ("default" in definition):
            try:
                default = definition["default"]()
            except TypeError:
                default = definition["default"]
        active = True
        if ("active" in definition):
            try:
                # check if definition["active"] is a function
                active = definition["active"]()
            except TypeError:
                # if not, then take the value of definition["active"]
                active = definition["active"]
        if (active):
            # Set a default description
            description = _("Sorry, no additional information is available about this setting")
            # read the description (a value)
            if ("description" in definition):
                description = definition["description"]
            # Check if there is a current value
            value = profile.get(setting, default)
            # Set a default for the type of control
            controltype = "textbox"
            if ("type" in definition):
                controltype = definition["type"].lower()
            return_list = False
            if ("return_list" in definition):
                try:
                    return_list = definition["return_list"]()
                except TypeError:
                    return_list = definition["return_list"]
            if (controltype == "listbox"):
                # Listbox is used to present a list of options from which
                # the user has to select. If the user enters something not
                # on the list, it will be rejected and the listbox will
                # ask again. An empty response is always acceptable.
                try:
                    options = definition["options"]()
                except TypeError:
                    options = definition["options"]
                if (isinstance(options, list)):
                    options = {item: item for item in options}
                print(
                    "    " + self.instruction_text(
                        definition["title"]
                    )
                )
                # Make sure the default value is actually available in the list of options
                if (value in options):
                    response = value
                else:
                    response = ""
                once = False
                while not ((once) and (profile.validate(definition, response))):
                    once = True
                    tmp_response = self.simple_input(
                        "    " + self.instruction_text(
                            _("Available choices:")
                        ) + " " + self.choices_text(
                            ("{}. ".format(", ".join(sorted(list(options.keys())))))
                        ) + self.instruction_text('"?" for help'),
                        response
                    )
                    if (tmp_response.strip() == "?"):
                        # Print the description plus any help text for the control
                        print("")
                        print(self.instruction_text(description))
                        once = False
                        continue
                    response = tmp_response
                    print("")
                    if (len(response.strip()) > 0):
                        if (return_list):
                            options_list = []
                            response = [item.strip() for item in response.split(",")]
                            for item in response:
                                try:
                                    options_list.append(options[item])
                                except KeyError:
                                    print(
                                        self.alert_text(
                                            _("Unrecognized option: {}").format(item)
                                        )
                                    )
                            profile.set_profile_var(
                                setting,
                                options_list
                            )
                        else:
                            try:
                                profile.set_profile_var(
                                    setting,
                                    options[response]
                                )
                            except KeyError:
                                print(
                                    self.alert_text(
                                        _("Unrecognized option.")
                                    )
                                )
                    else:
                        if (return_list):
                            profile.set_profile_var(
                                setting,
                                []
                            )
                        else:
                            profile.set_profile_var(
                                setting,
                                ""
                            )
                print("")
            elif (controltype == "password"):
                print("")
                value = profile.get_profile_password(setting, default)
                response = value
                once = False
                while not ((once) and (profile.validate(definition, response))):
                    once = True
                    tmp_response = self.simple_password(
                        "    " + self.instruction_text(
                            _('{} ("?" for help)').format(definition["title"])
                        ),
                        response
                    )
                    if (tmp_response.strip() == "?"):
                        # Print the description plus any help text
                        # for the control
                        print("")
                        print(self.instruction_text(definition["description"]))
                        once = False
                        continue
                    response = tmp_response
                    print("")
                    profile.set_profile_password(
                        setting,
                        response
                    )
            elif (controltype == "encrypted"):
                # Encrypted is like password, in that it encrypts the
                # information in your profile, so it would be protected
                # from someone who steals your profile.
                # However, it does not hide the text the way password does.
                print("")
                value = profile.get_profile_password(setting, default)
                response = value
                once = False
                while not ((once) and (profile.validate(definition, response))):
                    once = True
                    tmp_response = self.simple_input(
                        "    " + self.instruction_text(
                            _('{} ("?" for help)').format(definition["title"])
                        ),
                        response
                    )
                    if (tmp_response.strip() == "?"):
                        # Print the description plus any help text
                        # for the control
                        print("")
                        print(self.instruction_text(definition["description"]))
                        once = False
                        continue
                    response = tmp_response
                    print("")
                    profile.set_profile_password(
                        setting,
                        response
                    )
            elif (controltype == "boolean"):
                value = profile.get_profile_flag(setting, default)
                description = None
                if ('description' in definition):
                    description = definition['description']
                response = value
                once = False
                while not (once):
                    once = True
                    response = self.simple_yes_no(
                        definition['title'],
                        description,
                        response
                    )
                profile.set_profile_var(
                    setting,
                    response
                )
            elif (controltype == "number"):
                print("")
                response = value
                once = False
                while not ((once) and (profile.validate(definition, response))):
                    once = True
                    tmp_response = self.simple_input(
                        "    " + self.instruction_text(_('{} ("?" for help)').format(definition["title"])),
                        response
                    )
                    if (tmp_response.strip() == "?"):
                        # Print the description plus any help text for the control
                        print("")
                        print(self.instruction_text(definition["description"]))
                        once = False
                    else:
                        response = tmp_response
                        profile.set_profile_var(
                            setting,
                            response
                        )
                        print("")
            else:
                # this is the default (textbox)
                print("")
                response = value
                once = False
                while not ((once) and (profile.validate(definition, response))):
                    once = True
                    tmp_response = self.simple_input(
                        "    " + self.instruction_text(_('{} ("?" for help)').format(definition["title"])),
                        response
                    )
                    if (tmp_response.strip() == "?"):
                        # Print the description plus any help text for the control
                        print("")
                        print(self.instruction_text(definition["description"]))
                        once = False
                        continue
                    response = tmp_response
                    if (return_list):
                        response = [x.strip() for x in response.split(",")]
                    print("")
                    profile.set_profile_var(
                        setting,
                        response
                    )
        else:
            # Just set the value to the default value so we know we don't need
            # to address this again.
            profile.set_profile_var(setting, profile.get(setting, default))

    @staticmethod
    def separator():
        print("")
        print("")
        print("")
