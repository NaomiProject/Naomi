# -*- coding: utf-8 -*-
import datetime
from naomi import app_utils
from naomi import plugin


class ClockPlugin(plugin.SpeechHandlerPlugin):
    def intents(self):
        _ = self.gettext
        return {
            'ClockIntent': {
                'templates': [
                    _("WHAT TIME IS IT"),
                    _("TELL ME THE TIME"),
                    _("WHAT IS THE TIME")
                ],
                'action': self.handle
            }
        }

    def handle(self, intent, mic):
        """
        Reports the current time based on the user's timezone.


        Arguments:
        intent -- intentparser result with the following layout:
            intent['action'] = the action to take when the intent is activated
            intent['input'] = the original words
            intent['matches'] = dictionary of lists with matching elements,
                each with a list of the actual words matched
            intent['score'] = how confident Naomi is that it matched the
                correct intent.
        mic -- used to interact with the user (for both input and output)
        """
        tz = app_utils.get_timezone()
        now = datetime.datetime.now(tz=tz)
        if now.minute == 0:
            fmt = self.gettext("It is {t:%l} {t:%p} right now.")
        else:
            fmt = self.gettext("It is {t:%l}:{t:%M} {t:%p} right now.")
        mic.say(fmt.format(t=now))
