# -*- coding: utf-8 -*-
"""
A drop-in replacement for the Mic class that allows for all I/O to occur
over the terminal. Useful for debugging. Unlike with the typical Mic
implementation, Naomi is always active listening with local_mic.
"""
import contextlib
import unicodedata
from naomi import profile


class Mic(object):
    prev = None

    def __init__(self, *args, **kwargs):
        self.passive_listen = profile.get_profile_flag(["passive_listen"])
        self._keyword = profile.get_profile_var(['keyword'], 'NAOMI')
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
        input_text = input("YOU: ")
        unicodedata.normalize('NFD', input_text).encode('ascii', 'ignore')
        self.prev = input_text
        return [input_text]

    def listen(self):
        return self.active_listen(timeout=3)

    def say(self, phrase, OPTIONS=None):
        print("{}: {}".format(self._keyword, phrase))
