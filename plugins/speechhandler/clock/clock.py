# -*- coding: utf-8 -*-
import datetime
from collections import OrderedDict
from naomi import app_utils
from naomi import plugin
from naomi.run_command import run_command


class ClockPlugin(plugin.SpeechHandlerPlugin):
    def settings(self):
        _ = self.gettext
        try:
            tz = run_command(
                ["/bin/cat", "/etc/timezone"],
                capture=1
            ).stdout.decode('utf-8').strip()
        except OSError:
            tz = None

        return OrderedDict(
            {
                ('timezone',): {
                    "title": _("What is your timezone?"),
                    "description": _("Please enter a timezone from the list located in the TZ* column at http://en.wikipedia.org/wiki/List_of_tz_database_time_zones"),
                    "default": tz
                }
            }
        )

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

    def handle(self, text, mic):
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
