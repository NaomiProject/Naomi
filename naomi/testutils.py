# -*- coding: utf-8 -*-
from naomi import paths
import contextlib
import gettext
import logging
import os
import sys
import wave
import yaml


class test_info:
    def __init__(self, name):
        self.name = name
        self.translations = {'en-US': None}


def test_profile():
    if os.path.isfile(paths.config("profile.yml")):
        with open(paths.config("profile.yml"), "r") as f:
            config = yaml.safe_load(f)
    TEST_PROFILE = {
        'prefers_email': False,
        'timezone': 'US/Eastern',
        'phone_number': '012344321'
    }
    try:
        TEST_PROFILE['pocketsphinx'] = config['pocketsphinx']
    except (KeyError, NameError):
        pass
    try:
        TEST_PROFILE['language'] = config['language']
    except (KeyError, NameError):
        pass
    try:
        TEST_PROFILE['google'] = {
            'credentials_json': config['google']['credentials_json']
        }
    except (KeyError, NameError):
        pass
    try:
        TEST_PROFILE['key'] = config['key']
        TEST_PROFILE['email'] = config['email']
    except (KeyError, NameError):
        pass
    try:
        TEST_PROFILE['kenlm'] = {'source_dir': config['kenlm']['source_dir']}
    except (KeyError, NameError):
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

    # For now, assume the input matches a phrase
    def expect(self, prompt, phrases, name='expect', instructions=None):
        self.say(prompt)
        return (True, " ".join(self.active_listen()))

    # For now, assume the input is "YES" or "NO"
    def confirm(self, prompt):
        (matched, phrase) = self.expect("confirm", prompt, ['YES', 'NO'])
        if matched:
            if phrase in ['YES']:
                phrase = 'Y'
            else:
                phrase = 'N'
        return (matched, phrase)

    def say(self, phrase):
        self.outputs.append(phrase)


# This class is required to create a fake input_device object
# when performing tests on VAD plugins below.
class TestInput(object):
    def __init__(self, input_rate, input_bits, input_chunksize):
        self._input_rate = input_rate
        self._input_bits = input_bits
        self._input_chunksize = input_chunksize


class Test_VADPlugin(object):
    # attributes of the sample we are using
    # These are standard defaults for Naomi
    sample_file = "naomi/data/audio/naomi.wav"
    sample_channels = 1
    sample_rate = 16000  # Hz
    sample_width = 16    # bits
    # Standard lengths for an audio clip used for VAD in webrtc are
    # 10ms, 20ms, or 30ms
    # It is not necessary to use the same clip length here, but we
    # will for consistancy.
    clip_duration = 30   # ms
    clip_bytes = int((sample_width / 8) * (sample_rate * clip_duration / 1000))

    def setUp(self):
        super(Test_VADPlugin, self).setUp()
        self._logger = logging.getLogger(__name__)
        # Uncomment the following line to see detection timeline for sample
        # audio file
        # self._logger.setLevel(logging.INFO)
        # This is necessary because the VAD plugin requires an input
        # device to initialize. These values are only used in the
        # get_audio method, so shouldn't have any real effect on these
        # tests.
        self._test_input = TestInput(
            self.sample_rate,
            self.sample_width,
            (self.clip_duration / 1000) * self.sample_rate
        )

    def map_file(self):
        with contextlib.closing(
            wave.open(self.sample_file, "rb")
        ) as wf:
            audio = wf.readframes(wf.getnframes())
            clip_detect = ""
            offset = 0
            while offset + self.clip_bytes < len(audio):
                result = self.plugin._voice_detected(
                    audio[offset:offset + self.clip_bytes]
                )
                clip_detect += "+" if result else "-"
                offset += self.clip_bytes
            # unittest appears to do something odd to stderr
            # to see logger output, have to do this:
            stream_handler = logging.StreamHandler(sys.stdout)
            self._logger.addHandler(stream_handler)
            self._logger.info("")
            self._logger.info(clip_detect)
            self._logger.removeHandler(stream_handler)

    def test_silence(self):
        self.assertFalse(self.plugin._voice_detected(
            b'\x00' * self.clip_bytes
        ))

    def test_voice(self):
        # Get a sample of voice from a known sample
        # (naomi/data/audio/naomi.wav)
        # Voice data starts at .8 seconds
        with contextlib.closing(
            wave.open("naomi/data/audio/naomi.wav", "rb")
        ) as wf:
            # Go to the position of the clip I want to test (0.84 seconds)
            # measured in frames
            position = int(0.84 * wf.getframerate())
            wf.setpos(position)
            clip = wf.readframes(
                int(((self.clip_duration / 1000) * self.sample_rate))
            )
        self.assertTrue(self.plugin._voice_detected(
            clip
        ))


# Return an instance of the plugin.
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
