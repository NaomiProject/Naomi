# -*- coding: utf-8 -*-
import logging
import random
from . import i18n
from . import paths
from . import profile
from .mic import Unexpected
from .notifier import Notifier


class Conversation(i18n.GettextMixin):
    def __init__(self, mic, brain, *args, **kwargs):
        translations = i18n.parse_translations(paths.data('locale'))
        i18n.GettextMixin.__init__(self, translations, profile)
        self._logger = logging.getLogger(__name__)
        self.mic = mic
        self.brain = brain
        self.notifier = Notifier(mic=mic, brain=brain)
        self.translations = {}

    # Add way for the system to ask for name if is not found in the config
    def askName(self):
        keywords = profile.get(['keyword'], ['NAOMI'])
        if(isinstance(keywords, str)):
            keywords = [keywords]
        if(len(keywords) > 1):
            salutation = self.gettext(
                "My name is {} but you can also call me {}".format(
                    keywords[0],
                    " or ".join(keywords[1:])
                )
            )
        else:
            salutation = self.gettext(
                "My name is {}".format(keywords[0])
            )
        self.mic.say(salutation)

    def greet(self):
        if profile.get(['first_name']):
            salutation = self.gettext("How can I be of service, {}?").format(
                profile.get(["first_name"])
            )
        else:
            salutation = self.gettext("How can I be of service?")
        self.mic.say(salutation)

    def handleForever(self):
        """
        Delegates user input to the handling function when activated.
        """
        self._logger.debug('Starting to handle conversation.')
        while True:
            utterance = self.mic.listen()
            # if listen() returns False, just ignore it
            if not isinstance(utterance, bool):
                handled = False
                while(" ".join(utterance) != "" and not handled):
                    utterance, handled = self.handleRequest(utterance)

    def handleRequest(self, utterance):
        handled = False
        intent = self.brain.query(utterance)
        if intent:
            try:
                self._logger.info(intent)
                intent['action'](intent, self.mic)
                handled = True
            except Unexpected as e:
                utterance = e.utterance
            except Exception as e:
                self._logger.error(
                    'Failed to service intent {}: {}'.format(intent, str(e)),
                    exc_info=True
                )
                self.mic.say(
                    " ".join([
                        self.gettext("I'm sorry."),
                        self.gettext("I had some trouble with that operation."),
                        self.gettext("Please try again later.")
                    ])
                )
                handled = True
            else:
                self._logger.debug(
                    " ".join([
                        "Handling of phrase '{}'",
                        "by plugin '{}' completed"
                    ]).format(
                        utterance,
                        intent
                    )
                )
        else:
            self.say_i_do_not_understand()
            handled = True
        return utterance, handled

    def say_i_do_not_understand(self):
        self.mic.say(
            random.choice(
                [  # nosec
                    self.gettext("I'm sorry, could you repeat that?"),
                    self.gettext("My apologies, could you try saying that again?"),
                    self.gettext("Say that again?"),
                    self.gettext("I beg your pardon?"),
                    self.gettext("Pardon?")
                ]
            )
        )

    def list_choices(self, choices):
        if len(choices) == 1:
            self.mic.say(self.gettext("Please say {}").format(choices[0]))
        elif len(choices) == 2:
            self.mic.say(self.gettext("Please respond with {} or {}").format(choices[0], choices[1]))
        else:
            self.mic.say(
                self.gettext("Please respond with one of the following: {}").format(choices)
            )
