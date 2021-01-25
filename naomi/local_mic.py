# -*- coding: utf-8 -*-
"""
A drop-in replacement for the Mic class that allows for all I/O to occur
over the terminal. Useful for debugging. Unlike with the typical Mic
implementation, Naomi is always active listening with local_mic.
"""
import contextlib
import unicodedata
from jiwer import wer
from naomi import i18n
from naomi import paths
from naomi import profile


class Mic(i18n.GettextMixin):
    prev = None

    def __init__(self, *args, **kwargs):
        translations = i18n.parse_translations(paths.data('locale'))
        i18n.GettextMixin.__init__(self, translations, profile)
        self.passive_listen = profile.get_profile_flag(["passive_listen"])
        keyword = profile.get_profile_var(['keyword'], 'NAOMI')
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

    def active_listen(self, timeout=3):
        input_text = input("YOU: ").upper()
        unicodedata.normalize('NFD', input_text).encode('ascii', 'ignore')
        self.prev = input_text
        return [input_text]

    def listen(self):
        return self.active_listen(timeout=3)

    def expect(self, name, prompt, phrases):
        self.say(prompt)
        transcribed = self.listen()
        phrase, score = self.match_phrase(transcribed, phrases)
        # If it does, then return True and the phrase
        if(score > .5):
            response = (True, phrase)
        # Otherwise, return False and the active transcription
        else:
            response = (False, transcribed)
        return response

    def confirm(self, prompt):
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
        (matched, phrase) = self.expect(
            "confirm",
            prompt,
            POSITIVE + NEGATIVE
        )
        if(matched):
            if phrase in POSITIVE:
                return (matched, "Y")
            else:
                return (matched, "N")
        else:
            return (matched, phrase)

    @staticmethod
    def match_phrase(phrase, phrases):
        # If phrase is a list, convert to a string
        # (otherwise the "split" below throws an error)
        if(isinstance(phrase, list)):
            phrase = " ".join(phrase)
        if phrase == "":
            return ("", 0.0)
        else:
            # Just implement a quick edit distance
            # FIXME replace this with a call to a real intent parser
            templates = {}
            for template in phrases:
                phrase_len = len(phrase.split())
                template_len = len(template.split())
                if(phrase_len > template_len):
                    templates[template] = (phrase_len - wer(template, phrase)) / phrase_len
                else:
                    templates[template] = (template_len - wer(phrase, template)) / template_len
            besttemplate = max(templates, key=lambda key: templates[key])
            return(besttemplate, templates[besttemplate])

    def say(self, phrase, OPTIONS=None):
        print("{}: {}".format(self._keyword, phrase))
