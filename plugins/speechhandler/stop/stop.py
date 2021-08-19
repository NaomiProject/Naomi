# -*- coding: utf-8 -*-
from naomi import plugin
from naomi import profile


class StopPlugin(plugin.SpeechHandlerPlugin):
    _plugins = []

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
    def __init__(self, *args, **kwargs):
        super(StopPlugin, self).__init__(*args, **kwargs)
        for info in profile.get_arg('plugins').get_plugins_by_category("speechhandler"):
            if info.name != 'stop':
                plugin = info.plugin_class(info)
                if 'stop' in dir(plugin):
                    self._plugins.append(plugin.stop)
                    self._logger.info("{} stop command added".format(info.name))

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
        mic.stop()
        # Run "stop" methods from other speechhandlers
        for method in self._plugins:
            method(intent, mic)

        if self.gettext("SHUT UP").lower() in text.lower():
            mic.say(self.gettext("Okay, if that's what you want then I'll be quiet, but you don't have to be rude about it."))
