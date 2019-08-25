# -*- coding: utf-8 -*-
from naomi import plugin


class StopPlugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        return [
            self.gettext("STOP"),
            self.gettext("SHUT UP")
        ]

    def handle(self, text, mic):
        """
        Interrupt Naomi.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """

        mic.stop()
        if self.gettext("SHUT UP").lower() in text.lower():
            mic.say(self.gettext("Okay, if that's what you want then I'll shut up, but you don't have to be rude about it."))

    def is_valid(self, text):
        """
        Returns True if input is asking Naomi to stop speaking.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
