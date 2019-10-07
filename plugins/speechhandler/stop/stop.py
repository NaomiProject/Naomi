# -*- coding: utf-8 -*-
from naomi import plugin


class StopPlugin(plugin.SpeechHandlerPlugin):
    def intents(self):
        return {
            'StopIntent': {
                'templates': [
                    "STOP",
                    "SHUT UP"
                ],
                'action': self.handle
            }
        }

    def handle(self, intent, mic):
        """
        Interrupt Naomi.

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
        mic.stop()
        if self.gettext("SHUT UP").lower() in text.lower():
            mic.say(self.gettext("Okay, if that's what you want then I'll shut up, but you don't have to be rude about it."))
