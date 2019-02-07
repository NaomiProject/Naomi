# -*- coding: utf-8 -*-
from . import paths
import gettext
import yaml


def test_profile():
    with open(paths.config("profile.yml"), "r") as f:
        config = yaml.safe_load(f)
    TEST_PROFILE = {
        'prefers_email': False,
        'timezone': 'US/Eastern',
        'phone_number': '012344321',
        'weather': {
            'location': 'New York',
            'unit': 'Fahrenheit'
        }
    }
    try:
        TEST_PROFILE['pocketsphinx'] = config['pocketsphinx']
    except(KeyError, NameError):
        pass
    try:
        TEST_PROFILE['language'] = config['language']
    except(KeyError, NameError):
        pass
    return TEST_PROFILE


class TestMic(object):
    def __init__(self, inputs=[]):
        self.inputs = inputs
        self.idx = 0
        self.outputs = []

    @classmethod
    def wait_for_keyword(self, keyword="NAOMI"):
        return

    def active_listen(self, timeout=3):
        if self.idx < len(self.inputs):
            self.idx += 1
            return [self.inputs[self.idx - 1]]
        return [""]

    def say(self, phrase):
        self.outputs.append(phrase)


class TestInput:
    def __init__(self, input_rate, input_bits, input_chunksize):
        self._input_rate = input_rate
        self._input_bits = input_bits
        self._input_chunksize = input_chunksize


def get_plugin_instance(plugin_class, *extra_args):
    info = type(
        '',
        (object,),
        {
            'name': 'pluginunittest',
            'translations': {
                'en-US': gettext.NullTranslations()
            }
        }
    )()
    args = tuple(extra_args) + (info, test_profile())
    return plugin_class(*args)
