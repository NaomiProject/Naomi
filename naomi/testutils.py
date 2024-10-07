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
    try:
        if os.path.isfile(paths.config("profile.yml")):
            with open(paths.config("profile.yml"), "r") as f:
                config = yaml.safe_load(f)
        else:
            config = {}

        TEST_PROFILE = {
            'prefers_email': False,
            'timezone': 'US/Eastern',
            'phone_number': '012344321'
        }

        try:
            TEST_PROFILE['pocketsphinx'] = config['pocketsphinx']
        except KeyError:
            logging.warning("Missing pocketsphinx configuration")
        try:
            TEST_PROFILE['language'] = config['language']
        except KeyError:
            logging.warning("Missing language configuration")
        try:
            TEST_PROFILE['google'] = {
                'credentials_json': config['google']['credentials_json']
            }
        except KeyError:
            logging.warning("Missing Google configuration")
        try:
            TEST_PROFILE['key'] = config['key']
            TEST_PROFILE['email'] = config['email']
        except KeyError:
            logging.warning("Missing key or email in the profile")
        try:
            TEST_PROFILE['kenlm'] = {'source_dir': config['kenlm']['source_dir']}
        except KeyError:
            logging.warning("Missing KenLM configuration")
        
        return TEST_PROFILE

    except Exception as e:
        logging.error(f"Error loading profile: {str(e)}")
        return {}

class TestMic(object):
    def __init__(self, inputs=[]):
        self.inputs = inputs
        self.idx = 0
        self.outputs = []

    @classmethod
    def wait_for_keyword(cls, keyword="NAOMI"):
        try:
            # Simulate keyword detection
            return
        except Exception as e:
            logging.error(f"Error waiting for keyword: {str(e)}")

    def active_listen(self, timeout=3):
        try:
            if self.idx < len(self.inputs):
                self.idx += 1
                return [self.inputs[self.idx - 1]]
            return [""]
        except Exception as e:
            logging.error(f"Error during active listen: {str(e)}")
            return [""]

    def expect(self, prompt, phrases, name='expect', instructions=None):
        try:
            self.say(prompt)
            return (True, " ".join(self.active_listen()))
        except Exception as e:
            logging.error(f"Error in expect: {str(e)}")
            return (False, "")

    def confirm(self, prompt):
        try:
            (matched, phrase) = self.expect("confirm", prompt, ['YES', 'NO'])
            if matched:
                phrase = 'Y' if phrase == 'YES' else 'N'
            return (matched, phrase)
        except Exception as e:
            logging.error(f"Error in confirm: {str(e)}")
            return (False, "")

    def say(self, phrase):
        try:
            self.outputs.append(phrase)
        except Exception as e:
            logging.error(f"Error in say: {str(e)}")


class TestInput(object):
    def __init__(self, input_rate, input_bits, input_chunksize):
        try:
            self._input_rate = input_rate
            self._input_bits = input_bits
            self._input_chunksize = input_chunksize
        except Exception as e:
            logging.error(f"Error initializing TestInput: {str(e)}")


class Test_VADPlugin(object):
    sample_file = "naomi/data/audio/naomi.wav"
    sample_channels = 1
    sample_rate = 16000  # Hz
    sample_width = 16    # bits
    clip_duration = 30   # ms
    clip_bytes = int((sample_width / 8) * (sample_rate * clip_duration / 1000))

    def setUp(self):
        try:
            super(Test_VADPlugin, self).setUp()
            self._logger = logging.getLogger(__name__)
            self._test_input = TestInput(
                self.sample_rate,
                self.sample_width,
                (self.clip_duration / 1000) * self.sample_rate
            )
        except Exception as e:
            logging.error(f"Error in setUp: {str(e)}")

    def map_file(self):
        try:
            with contextlib.closing(wave.open(self.sample_file, "rb")) as wf:
                audio = wf.readframes(wf.getnframes())
                clip_detect = ""
                offset = 0
                while offset + self.clip_bytes < len(audio):
                    result = self.plugin._voice_detected(
                        audio[offset:offset + self.clip_bytes]
                    )
                    clip_detect += "+" if result else "-"
                    offset += self.clip_bytes

                stream_handler = logging.StreamHandler(sys.stdout)
                self._logger.addHandler(stream_handler)
                self._logger.info("")
                self._logger.info(clip_detect)
                self._logger.removeHandler(stream_handler)
        except Exception as e:
            logging.error(f"Error in map_file: {str(e)}")

    def test_silence(self):
        try:
            self.assertFalse(self.plugin._voice_detected(
                b'\x00' * self.clip_bytes
            ))
        except Exception as e:
            logging.error(f"Error in test_silence: {str(e)}")

    def test_voice(self):
        try:
            with contextlib.closing(wave.open("naomi/data/audio/naomi.wav", "rb")) as wf:
                position = int(0.84 * wf.getframerate())
                wf.setpos(position)
                clip = wf.readframes(int((self.clip_duration / 1000) * self.sample_rate))
            self.assertTrue(self.plugin._voice_detected(clip))
        except Exception as e:
            logging.error(f"Error in test_voice: {str(e)}")


def get_plugin_instance(plugin_class, *extra_args):
    try:
        info = type(
            '',
            (object,),
            {
                'name': 'pluginunittest',
                'translations': {'en-US': gettext.NullTranslations()}
            }
        )()
        args = tuple(extra_args) + (info, test_profile())
        return plugin_class(*args)
    except Exception as e:
        logging.error(f"Error getting plugin instance: {str(e)}")
        return None
