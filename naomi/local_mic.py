# -*- coding: utf-8 -*-
"""
A drop-in replacement for the Mic class that allows for all I/O to occur
over the terminal. Useful for debugging. Unlike with the typical Mic
implementation, Naomi is always active listening with local_mic.
"""
import contextlib
import logging
import unicodedata
from naomi import i18n
from naomi import paths
from naomi import profile
from naomi.mic import Unexpected


class Mic(i18n.GettextMixin):
    prev = None
    Continue = True

    def __init__(self, *args, **kwargs):
        self.passive_listen = profile.get_profile_flag(["passive_listen"])
        keyword = profile.get_profile_var(['keyword'], 'NAOMI')
        self.brain = kwargs['brain']
        self._logger = logging.getLogger(__name__)
        translations = i18n.parse_translations(paths.data('locale'))
        i18n.GettextMixin.__init__(self, translations, profile)
        if isinstance(keyword, list):
            self._keyword = keyword[0]
        else:
            self._keyword = keyword
        return

    @staticmethod
    @contextlib.contextmanager
    def special_mode(name, phrases):
        yield

    def wait_for_keyword(self, keyword="NAOMI"):
        if(self.passive_listen):
            return self.active_listen()
        else:
            return

    def active_listen(self):
        input_text = input("YOU: ").upper()
        unicodedata.normalize('NFD', input_text).encode('ascii', 'ignore')
        self.prev = input_text
        return [input_text]

    def listen(self):
        return self.active_listen()

    def expect(self, prompt, phrases, name='expect', instructions=None):
        self.say(prompt)
        transcribed = self.listen()
        phrase, score = profile.get_arg("application").brain._intentparser.match_phrase(transcribed, phrases)
        if(score > 0.1):
            response = phrase
        else:
            raise Unexpected(transcribed)
        return response

    # This is a very simple recognition of a positive or negative response.
    # We need to move the string literals into an external file.
    def confirm(self, prompt, name='confirm'):
        # default to english
        language = profile.get(['language'], 'en-US')[:2]
        POSITIVE = ['YES', 'SURE']
        NEGATIVE = ['NO', 'NOPE']
        if(language == "fr"):
            POSITIVE = ['OUI']
            NEGATIVE = ['NON']
        elif(language == "de"):
            POSITIVE = ['JA']
            NEGATIVE = ['NEIN']
        phrase = self.expect(
            prompt,
            POSITIVE + NEGATIVE,
            name,
            instructions=profile.get_arg("application").conversation.gettext(
                "Please respond with Yes or No"
            )
        )
        if phrase in POSITIVE:
            return True
        else:
            return False

    def say(self, phrase, OPTIONS=None):
        print("{}: {}".format(self._keyword, phrase))

    def main_loop(self):
        while self.Continue:
            utterance = self.listen()
            if not isinstance(utterance, bool):
                handled = False
                while(" ".join(utterance) != "" and not handled):
                    utterance, handled = self.handleRequest(utterance)

    def handleRequest(self, utterance):
        handled = False
        intent = self.brain.query(utterance)
        if intent:
            try:
                self._logger.info(intent)
                intent['action'](intent, self)
                handled = True
            except Unexpected as e:
                utterance = e.utterance
            except Exception as e:
                self._logger.error(
                    'Failed to service intent {}: {}'.format(intent, str(e)),
                    exc_info=True
                )
                self.say(self.gettext("I'm sorry."))
                self.say(self.gettext("I had some trouble with that operation."))
                self.say(str(e))
                self.say(self.gettext("Please try again later."))
                handled = True
            else:
                self._logger.debug(
                    " ".join([
                        "Handling of phrase '{}'",
                        "by plugin '{}' completed"
                    ]).format(
                        utterance,
                        intent
                    )
                )
        else:
            self.say_i_do_not_understand()
            handled = True
        return utterance, handled

    def say_i_do_not_understand(self):
        self.say(
            random.choice(
                [  # nosec
                    self.gettext("I'm sorry, could you repeat that?"),
                    self.gettext("My apologies, could you try saying that again?"),
                    self.gettext("Say that again?"),
                    self.gettext("I beg your pardon?"),
                    self.gettext("Pardon?")
                ]
            )
        )
