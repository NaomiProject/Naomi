# -*- coding: utf-8 -*-
import datetime
from naomi import app_utils
from naomi import plugin


class ClockPlugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        return [self.gettext("TIME")]

    def handle(self, text, mic):
        """
        Reports the current time based on the user's timezone.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """

        tz = app_utils.get_timezone(self.profile)
        now = datetime.datetime.now(tz=tz)
        if now.minute == 0:
            fmt = "It is {t:%l} {t:%p} right now."
        else:
            fmt = "It is {t:%l}:{t:%M} {t:%p} right now."
        mic.say(self.gettext(fmt).format(t=now))

    def is_valid(self, text):
        """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
