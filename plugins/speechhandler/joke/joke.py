# -*- coding: utf-8 -*-
import os
import random
import re
from naomi import plugin
from naomi import profile


def get_jokes(language='en-US'):
    filename = os.path.join(os.path.dirname(__file__),
                            'data',
                            '%s.txt' % language)
    jokes = []
    found = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            found.append(line)
            if len(found) == 2:
                jokes.append(tuple(found))
                found = []
    return jokes


class JokePlugin(plugin.SpeechHandlerPlugin):
    def __init__(self, *args, **kwargs):
        super(JokePlugin, self).__init__(*args, **kwargs)

        language = profile.get(['language'], 'en-US')

        try:
            self._jokes = get_jokes(language)
        except IOError as e:
            if e.errno == 2:
                self._jokes = []
            else:
                raise e

        if len(self._jokes) == 0:
            raise ValueError('Unsupported language!')

    def intents(self):
        return {
            'JokeIntent': {
                'locale': {
                    'en-US': {
                        'templates': [
                            "TELL ME A KNOCK KNOCK JOKE",
                            "DO YOU KNOW ANY KNOCK KNOCK JOKES",
                            "CAN YOU TELL ME A KNOCK KNOCK JOKE",
                            "MAKE ME LAUGH"
                        ]
                    },
                    'fr-FR': {
                        'templates': [
                            "RACONTE MOI UNE BLAGUE",
                            "CONNAISSEZ-VOUS DES PLAISANTERIES",
                            "PEUX-TU ME DIRE UNE BLAGUE",
                            "FAIS MOI RIRE"
                        ]
                    },
                    'de-DE': {
                        'templates': [
                            "ERZÄHL MIR EINEN WITZ",
                            "KENNEN SIE JEDE WITZ",
                            "KÖNNEN SIE MIR EINEN WITZ ERZÄHLEN",
                            "BRING MICH ZUM LACHEN"
                        ]
                    }
                },
                'action': self.handle
            }
        }

    def handle(self, intent, mic):
        """
        Responds to user-input, typically speech text, by telling a joke.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """
        joke = random.choice(self._jokes)

        matched, phrase = mic.expect(
            "joke_who_is_there",             # name
            self.gettext("Knock knock"),     # prompt or question
            ["WHO'S THERE", "WHO IS THERE"]  # expected responses
        )
        if(matched):
            matched, phrase = mic.expect(
                "joke_{}_who".format(re.sub("[^a-z]", "_", joke[0].lower())),
                joke[0],
                ["{} WHO".format(joke[0].upper())]
            )
            if(matched):
                mic.say(joke[1])
                (matched, phrase) = mic.confirm("Was that joke funny?")
                if matched:
                    if(phrase == "Y"):
                        mic.say("I'm glad you enjoyed it")
                    else:
                        mic.say("Oh, well, maybe the next one will be funny")
        return(matched, phrase)
