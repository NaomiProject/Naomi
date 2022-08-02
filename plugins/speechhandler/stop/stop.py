# -*- coding: utf-8 -*-
from naomi import plugin
from naomi import profile


class StopPlugin(plugin.SpeechHandlerPlugin):
    _plugins = []
    _setup = False

    def intents(self):
        return {
            'StopIntent': {
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
                'action': self.handle
            }
        }

    # Create a list of speechhandler plugins that have a "stop" method
    # This needs to run after all speechhandler plugins have been loaded.
    def setup(self, *args, **kwargs):
        for plug_in in profile.get_arg('application').brain._plugins:
            if 'stop' in dir(plug_in):
                self._plugins.append(plug_in.stop)
                self._logger.info("{} stop command added".format(plug_in.info.name))
            else:
                self._logger.info("{} stop command not found".format(plug_in.info.name))
        self._setup = True

    def handle(self, intent, mic):
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
        if not self._setup:
            self._logger.info("searching for plugins with 'stop' methods")
            self.setup()
        else:
            self._logger.info("'stop' methods already configured")
        mic.stop()
        # Run "stop" methods from other speechhandlers
        for method in self._plugins:
            method(intent, mic)

        if self.gettext("SHUT UP").lower() in text.lower():
            mic.say(self.gettext("Okay, if that's what you want then I'll be quiet, but you don't have to be rude about it."))
