# -*- coding: utf-8 -*-
import contextlib
import logging
import sys
import unittest
import wave
from naomi import testutils
from . import snr_vad


class TestSNR_VADPlugin(unittest.TestCase):
    # attributes of the sample we are using
    # These are standard defaults for Naomi
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
        self._logger = logging.getLogger(__name__)
        # Uncomment the following line to see detection timeline for sample
        # audio file
        # self._logger.setLevel(logging.INFO)
        _test_input = testutils.TestInput(
            self.sample_rate,
            self.sample_width,
            (self.clip_duration / 1000) * self.sample_rate
        )
        self.plugin = testutils.get_plugin_instance(
            snr_vad.SNRPlugin,
            _test_input
        )
        # prime by running through one wav file
        with contextlib.closing(
            wave.open("naomi/data/audio/naomi.wav", "rb")
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
