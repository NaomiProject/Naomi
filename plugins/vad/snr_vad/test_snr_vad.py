# -*- coding: utf-8 -*-
import collections
import contextlib
import logging
import os
import unittest
import wave
from naomi import testutils, diagnose
from . import snr_vad


class TestSNR_VADPlugin(unittest.TestCase):
    channels = 1
    sample_rate = 16000 # Hz
    sample_width = 16 # bits
    clip_duration = 30 # ms
    clip_bytes = int((sample_width / 8) * (sample_rate * clip_duration / 1000))

    def setUp(self):
        self._logger = logging.getLogger(__name__)
        _test_input = testutils.TestInput(self.sample_rate,self.sample_width,480)
        self.plugin = testutils.get_plugin_instance(
            snr_vad.SNRPlugin,
            _test_input
        )
        # prime by running through one wav file
        with contextlib.closing(wave.open("naomi/data/audio/naomi.wav","rb")) as wf:
            assert wf.getnchannels() == self.channels
            assert wf.getsampwidth() == self.sample_width / 8
            assert wf.getframerate() == self.sample_rate
            audio = wf.readframes(wf.getnframes())
            clip_detect = ""
            offset = 0
            while offset + self.clip_bytes < len(audio):
                result = self.plugin._voice_detected(audio[offset:offset + self.clip_bytes])
                clip_detect += "+" if result else "-"
                offset += self.clip_bytes
            self._logger.info(clip_detect)

    def test_silence(self):
        self.assertFalse(self.plugin._voice_detected(
            b'\x00' * self.clip_bytes
        ))

    def test_voice(self):
        # Get a sample of voice from a known sample
        # (naomi/data/audio/naomi.wav)
        # Voice data starts at .8 seconds
        with contextlib.closing(wave.open("naomi/data/audio/naomi.wav","rb")) as wf:
            bytes_per_frame = self.channels * self.sample_width / 8
            bytes_per_clip = int(((self.clip_duration / 1000) * self.sample_rate * self.sample_width / 8))
            if False:
                # Read the whole file into memory
                wf.rewind()
                audio_data = wf.readframes(wf.getnframes())
                # Grab the bytes I need
                position = int((0.84 * self.clip_bytes) / ((self.clip_duration / 1000)))
                clip = audio_data[position:int(position + (bytes_per_clip))]
            else:
                # Go to the position of the clip I want to test (0.84 seconds)
                # measured in frames
                #position = int((0.84 * self.clip_bytes) / ((self.clip_duration / 1000) * bytes_per_frame))
                position = int(0.84 * wf.getframerate())
                wf.setpos(position)
                clip = wf.readframes(int(((self.clip_duration / 1000) * self.sample_rate)))
        self.assertTrue(self.plugin._voice_detected(
            clip
        ))
