# -*- coding: utf-8 -*-
import unittest
from naomi import paths
from naomi import testutils
from .. import sphinxplugin


class TestPocketsphinxSTTPlugin(unittest.TestCase):

    def setUp(self):
        self.naomi_clip = paths.data('audio', 'naomi.wav')
        self.time_clip = paths.data('audio', 'time.wav')

        try:
            # KenLM does not include a </s> when generating an
            # arpa model for single word vocabularies, so we
            # have to have at least two words in our vocabularies
            self.passive_stt_engine = testutils.get_plugin_instance(
                sphinxplugin.PocketsphinxSTTPlugin,
                'unittest-passive', ['NAOMI', 'COMPUTER'])
            self.active_stt_engine = testutils.get_plugin_instance(
                sphinxplugin.PocketsphinxSTTPlugin,
                'unittest-active', ['TIME', 'DATE'])
        except ImportError:
            self.skipTest("Pocketsphinx not installed!")

    def testTranscribeNaomi(self):
        """
        Does Naomi recognize his name (i.e., passive listen)?
        """
        with open(self.naomi_clip, mode="rb") as f:
            transcription = self.passive_stt_engine.transcribe(f)
        self.assertIn("NAOMI".lower(), transcription)

    def testTranscribe(self):
        """
        Does Naomi recognize 'time' (i.e., active listen)?
        """
        with open(self.time_clip, mode="rb") as f:
            transcription = self.active_stt_engine.transcribe(f)
        self.assertIn("TIME".lower(), transcription)
