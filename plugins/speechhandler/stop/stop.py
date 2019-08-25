# -*- coding: utf-8 -*-
import datetime
from naomi import app_utils
from naomi import plugin


class StopPlugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        return [
            self.gettext("STOP"),
            self.gettext("SHUT UP")
        ]

    def handle(self, text, mic):
        """
        Says an empty string to interrupt Naomi.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """

        mic.stop()
        if self.gettext("SHUT UP").lower() in text.lower():
            mic.say(self.gettext("Okay, if that's what you want then I'll shut up, but you don't have to be rude about it."))

    def is_valid(self, text):
        """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
