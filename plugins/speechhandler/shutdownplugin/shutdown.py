# -*- coding: utf-8 -*-
import random
import time
from naomi import plugin
from naomi import profile


class ShutdownPlugin(plugin.SpeechHandlerPlugin):
    def intents(self):
        return {
            'ShutdownIntent': {
<<<<<<< HEAD
                'templates': [
                    "SHUTDOWN",
                    "TURN YOURSELF OFF"
                ],
=======
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
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
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
        # specifically wait for Naomi to finish talking
        # here, otherwise it will exit before getting to
        # speak.
<<<<<<< HEAD
        if hasattr(mic, "current_thread"):
            while(mic.current_thread.is_alive()):
                time.sleep(1)
=======
        if(profile.get_arg('listen_while_talking', False)):
            if hasattr(mic, "current_thread"):
                while(mic.current_thread.is_alive()):
                    time.sleep(1)
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8

        quit()
