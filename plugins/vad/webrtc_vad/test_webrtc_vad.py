# -*- coding: utf-8 -*-
import collections
import contextlib
import logging
import os
import unittest
import wave
from naomi import testutils, diagnose
from . import webrtc_vad


class TestWebRTCPlugin(unittest.TestCase):
    sample_rate = 16000 # Hz
    sample_width = 16 # bits
    clip_duration = 30 # ms
    clip_bytes = int((sample_width / 8) * (sample_rate * clip_duration / 1000))

    def setUp(self):
        self._logger = logging.getLogger(__name__)
        _test_input = testutils.TestInput(self.sample_rate,self.sample_width,480)
        self.plugin = testutils.get_plugin_instance(
            webrtc_vad.WebRTCPlugin,
            _test_input
        )
        # This is just for comparison to see how VAD engines compare in
        # detecting audio. Skip if not in INFO logging level.
        if(self._logger.getEffectiveLevel() < logging.WARN):
            with contextlib.closing(wave.open("naomi/data/audio/naomi.wav","rb")) as wf:
                assert wf.getnchannels() == 1
                assert wf.getsampwidth() == 2
                assert wf.getframerate() == 16000
                audio_data = wf.readframes(wf.getnframes())
                clip_detect = ""
                offset = 0
                while offset + self.clip_bytes < len(audio_data):
                    result = self.plugin._voice_detected(audio_data[offset:offset + self.clip_bytes])
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
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000
            position = int(0.84 * wf.getframerate())
            wf.setpos(position)
            clip = wf.readframes(int(((self.clip_duration / 1000) * self.sample_rate)))
        self.assertTrue(self.plugin._voice_detected(
            clip
        ))
