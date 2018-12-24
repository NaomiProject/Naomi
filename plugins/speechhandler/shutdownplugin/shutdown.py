# -*- coding: utf-8 -*-
import random
from naomi import plugin
import subprocess


class ShutdownPlugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        return [
            self.gettext("SHUTDOWN"),
            self.gettext("SHUT"),
            self.gettext("DOWN")]

    def handle(self, text, mic):
        """
        Responds to user-input, typically speech text, by relaying the
        meaning of life.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """
        name = self.profile['first_name']

        messages = [
            self.gettext("I'm going down."),
            self.gettext("Shuting down now."),
            self.gettext("Bye Bye."),
            self.gettext("Goodbye, {}").format(name)
        ]

        message = random.choice(messages)

        mic.say(message)

        proc = subprocess.Popen(["pkill", "-f", "Naomi.py"],
                                stdout=subprocess.PIPE)
        proc.wait()

    def is_valid(self, text):
        """
        Returns True if the input is related to the meaning of life.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
