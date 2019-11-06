# -*- coding: utf-8 -*-
import logging
import random
from . import i18n
from . import paths
from . import profile
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
        if profile.get(['keyword']):
            salutation = self.gettext("My name is {}.").format(
                ' or '.join(
                    profile.get(['keyword'])
                )
            )
        else:
            salutation = self.gettext("My name is Naomi")
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
            # Print notifications until empty
            """notifications = self.notifier.get_all_notifications()
            for notif in notifications:
                self._logger.info("Received notification: '%s'", str(notif))"""

            utterance = self.mic.listen()

            if utterance:
                intent = self.brain.query(utterance)
                if intent:
                    try:
                        self._logger.info(intent)
                        intent['action'](intent, self.mic)
                    except Exception:
                        self._logger.error(
                            'Failed to execute module',
                            exc_info=True
                        )
                        self.mic.say(
                            " ".join([
                                self.gettext("I'm sorry."),
                                self.gettext("I had some trouble with that operation."),
                                self.gettext("Please try again later.")
                            ])
                        )
                    else:
                        self._logger.debug(
                            " ".join([
                                "Handling of phrase '{}'",
                                "by module '{}' completed"
                            ]).format(
                                utterance,
                                intent
                            )
                        )
                else:
                    self.mic.say(random.choice([  # nosec
                        self.gettext("I'm sorry, could you repeat that?"),
                        self.gettext("My apologies, could you try saying that again?"),
                        self.gettext("Say that again?"),
                        self.gettext("I beg your pardon?")
                    ]))
            else:
                self.mic.say(self.gettext("Pardon?"))
