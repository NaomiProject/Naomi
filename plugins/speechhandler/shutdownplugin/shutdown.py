# -*- coding: utf-8 -*-
import random
import time
from naomi import plugin
from naomi import profile


class ShutdownPlugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        return [
            self.gettext("SHUTDOWN"),
            self.gettext("SHUT DOWN")
        ]

    def handle(self, text, mic):
        """
        Responds to user-input, typically speech text, by relaying the
        meaning of life.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """
        name = profile.get_profile_var(['first_name'], '')

        messages = [
            self.gettext("I'm shutting down."),
            self.gettext("Shutting down now."),
            self.gettext("Bye Bye."),
            self.gettext("Goodbye, {}").format(name)
        ]

        message = random.choice(messages)

        mic.say(message)
        # specifically wait for Naomi to finish talking
        # here, otherwise it will exit before getting to
        # speak.
        while(mic.current_thread.is_alive()):
            time.sleep(1)

        quit()

    def is_valid(self, text):
        """
        Returns True if the input is related to the meaning of life.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
