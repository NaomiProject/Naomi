from naomi import i18n
from naomi import paths
from naomi import profile
from getpass import getpass
import re
from blessings import Terminal

_ = None
affirmative = ""
negative = ""
audioengine_plugins = None
t = None


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
        if(language == 'fr-FR'):
            affirmative = 'oui'
            negative = 'non'
        elif(language == 'de-DE'):
            affirmative = "ja"
            negative = "nein"
        else:
            affirmative = 'yes'
            negative = 'no'

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
            )and(
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
            if(len(selected_language) > 0):
                if(self.check_for_value(
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
        if(icon == "!"):
            prompt = "".join([
                self.icon_text('['),
                self.alert_icon('!'),
                self.icon_text('] '),
                self.question_text(prompt)
            ])
        elif(icon == "?"):
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
        if(default):
            prompt += self.default_text(default) + self.default_prompt()
        prompt += self.input_text()
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
    def simple_password(self, prompt, default=None):
        prompt += ": "
        prompt += self.input_text()
        # don't use print here so no automatic carriage return
        # sys.stdout.write(prompt)
        response = getpass(prompt)
        # if the user pressed enter without entering anything,
        # set the response to default
        if(default and not response):
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
    def simple_yes_no(self, prompt):
        response = ""
        while(response not in (affirmative.lower()[:1], negative.lower()[:1])):
            response = self.simple_input(
                self.format_prompt(
                    "?",
                    prompt + self.instruction_text(" (") + self.choices_text(
                        affirmative.upper()[:1]
                    ) + self.instruction_text("/") + self.choices_text(
                        negative.upper()[:1]
                    ) + self.instruction_text(")")
                )
            ).strip().lower()[:1]
            if response not in (affirmative.lower()[:1], negative.lower()[:1]):
                print(self.alert_text("Please select '{}' or '{}'.").format(
                    affirmative.upper()[:1],
                    negative.upper()[:1]
                ))
        if response == affirmative.lower()[:1]:
            return True
        else:
            return False

    # This is a higher level control that takes a "setting" as input
    def get_setting(self, setting, definition):
        active = True
        if("active" in definition):
            try:
                # check if definition["active"] is a function
                active = definition["active"]()
            except TypeError:
                # if not, then take the value of definition["active"]
                active = definition["active"]
        if(active):
            # Set a default description
            description = _("Sorry, no additional information is available about this setting")
            # read the description (a value)
            if("description" in definition):
                description = definition["description"]
            # set a default default value
            default = ""
            # if default is defined, then use that value as default
            if("default" in definition):
                default = definition["default"]
            # Check if there is a current value
            value = profile.get(setting, default)
            # Set a default for the type of control
            controltype = "textbox"
            if("type" in definition):
                controltype = definition["type"].lower()
            if(controltype == "listbox"):
                try:
                    options = definition["options"]()
                except TypeError:
                    options = definition["options"]
                print(
                    "    " + self.instruction_text(
                        definition["title"]
                    )
                )
                print("")
                response = value
                once = False
                while not ((once) and (self.validate(definition, response))):
                    once = True
                    tmp_response = self.simple_input(
                        "    " + self.instruction_text(
                            _("Available choices:")
                        ) + " " + self.choices_text(
                            ("{}. ".format(", ".join(sorted(list(options.keys())))))
                        ) + self.instruction_text('"?" for help'),
                        response
                    )
                    if(tmp_response.strip() == "?"):
                        # Print the description plus any help text for the control
                        print("")
                        print(self.instruction_text(description))
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
                            self.alert_text(
                                _("Unrecognized option.")
                            )
                        )
                print("")
            elif(controltype == "password"):
                print("")
                value = profile.get_profile_password(setting, default)
                response = value
                once = False
                while not ((once) and (self.validate(definition, response))):
                    once = True
                    tmp_response = self.simple_password(
                        "    " + self.instruction_text('{} ("?" for help)'.format(definition["title"])),
                        response
                    )
                    if(tmp_response.strip() == "?"):
                        # Print the description plus any help text for the control
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
            else:
                # this is the default (textbox)
                print("")
                response = value
                once = False
                while not ((once) and (self.validate(definition, response))):
                    once = True
                    tmp_response = self.simple_input(
                        "    " + self.instruction_text('{} ("?" for help)'.format(definition["title"])),
                        response
                    )
                    if(tmp_response.strip() == "?"):
                        # Print the description plus any help text for the control
                        print("")
                        print(self.instruction_text(definition["description"]))
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
    @staticmethod
    def validate(definition, response):
        valid = False
        if(len(response.strip()) == 0):
            valid = True
        else:
            try:
                validfunction = definition["validation"]
                valid = validfunction(response)
            except KeyError:
                try:
                    if(definition["type"] in ["listbox"]):
                        # Use the default validation, which is to make sure whatever
                        # is selected is a member of options
                        try:
                            valid = response in definition["options"]()
                        except TypeError:
                            # must not be a function, assume it is a list
                            valid = response in definition["options"]
                    else:
                        valid = True
                except KeyError:
                    # must be a textbox with no validation
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

    @staticmethod
    def separator():
        print("")
        print("")
        print("")
