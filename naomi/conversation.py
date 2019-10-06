# -*- coding: utf-8 -*-
import logging
from . import i18n
from . import paths
from . import profile
#  from notifier import Notifier


class Conversation(i18n.GettextMixin):
    def __init__(self, mic, brain, *args, **kwargs):
        translations = i18n.parse_translations(paths.data('locale'))
        i18n.GettextMixin.__init__(self, translations, profile)
        self._logger = logging.getLogger(__name__)
        self.mic = mic
        self.brain = brain
        #  self.notifier = Notifier(profile)
        self.translations = {}

    # Add way for the system to ask for name if is not found in the config
    def askName(self):
        if profile.get(['keyword']):
            salutation = self.gettext("My name is {}.").format(
                profile.get(['keyword'])
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

            input = self.mic.listen()

            if input:
                plugin, text = self.brain.query(input)
                if plugin and text:
                    try:
                        plugin.handle(text, self.mic)
                    except Exception:
                        self._logger.error('Failed to execute module',
                                           exc_info=True)
                        self.mic.say(self.gettext(
                            "I'm sorry. I had some trouble with that "
                        ) + self.gettext(
                            "operation. Please try again later.")
                        )
                    else:
                        self._logger.debug(
                            " ".join([
                                "Handling of phrase '{}'",
                                "by module '{}' completed"
                            ]).format(
                                text,
                                plugin.info.name
                            )
                        )
            else:
                self.mic.say(self.gettext("Pardon?"))
