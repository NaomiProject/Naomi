# -*- coding: utf-8 -*-
import random
import time
from naomi import plugin
from naomi import profile


class ShutdownPlugin(plugin.SpeechHandlerPlugin):
    def intents(self):
        return {
            'ShutdownIntent': {
                'locale': {
                    'en-US': {
                        'templates': [
                            "SHUTDOWN",
                            "TURN YOURSELF OFF"
                        ]
                    },
                    'fr-FR': {
                        'templates': [
                            "ÉTEINS-TOI",
                            "ÉTEIGNEZ-VOUS"
                        ]
                    },
                    'de-DE': {
                        'templates': [
                            "BEENDE DICH",
                            "SCHALTEN SIE SICH AUS"
                        ]
                    }
                },
                'action': self.handle
            }
        }

    def handle(self, intent, mic):
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

        quit()
