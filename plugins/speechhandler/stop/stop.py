# -*- coding: utf-8 -*-
from naomi import plugin


class StopPlugin(plugin.SpeechHandlerPlugin):
    def intents(self):
        return {
            'StopIntent': {
<<<<<<< HEAD
                'templates': [
                    "STOP",
                    "SHUT UP"
                ],
=======
                'locale': {
                    'en-US': {
                        'templates': [
                            "STOP",
                            "SHUT UP"
                        ]
                    },
                    'fr-FR': {
                        'templates': [
                            "ARRÊTEZ",
                            "TAIS-TOI"
                        ]
                    },
                    'de-DE': {
                        'templates': [
                            "STOPP",
                            "HALT DIE KLAPPE"
                        ]
                    }
                },
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
                'action': self.handle
            }
        }

    def handle(self, text, mic):
        intent = text
        text = intent['input']
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
