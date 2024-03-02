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
                "My name is {} but you can also call me {}"
            ).format(
                keywords[0],
                " or ".join(keywords[1:])
            )
        else:
            salutation = self.gettext(
                "My name is {}"
            ).format(keywords[0])
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
        self.mic.main_loop()
