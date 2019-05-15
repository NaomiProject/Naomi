# -*- coding: utf-8 -*-
import unittest
from naomi import paths
from naomi import testutils
from naomi import profile
from .. import google
import os


class TestGoogleSTTPlugin(unittest.TestCase):

    def setUp(self):
        self.naomi_clip = paths.data('audio', 'naomi.wav')
        self.time_clip = paths.data('audio', 'time.wav')

        # google_env_var = "GOOGLE_APPLICATION_CREDENTIALS"
        google_env_var = google.google_env_var
        if(google_env_var in os.environ):
            credentials_json = os.getenv(google_env_var)
        elif profile.check_profile_var_exists(["google", "credentials_json"]):
            credentials_json = profile.get_profile_var(["google", "credentials_json"])
        else:
            self.skipTest("Please set " + google_env_var)
        if(not os.path.isfile(os.path.expanduser(credentials_json))):
            self.skiptest("Credentials file {} does not exist".format(credentials_json))

        try:
            self.passive_stt_engine = testutils.get_plugin_instance(
                google.GoogleSTTPlugin,
                'unittest-passive', ['NAOMI'])
            self.active_stt_engine = testutils.get_plugin_instance(
                google.GoogleSTTPlugin,
                'unittest-active', ['TIME'])
        except ImportError:
            self.skipTest("Google STT not installed!")

    def testTranscribeNaomi(self):
        """
        Does Naomi recognize his name (i.e., passive listen)?
        """
        with open(self.naomi_clip, mode="rb") as f:
            transcription = self.passive_stt_engine.transcribe(f)
        self.assertIn("NAOMI", transcription)

    def testTranscribe(self):
        """
        Does Naomi recognize 'time' (i.e., active listen)?
        """
        with open(self.time_clip, mode="rb") as f:
            transcription = self.active_stt_engine.transcribe(f)
        self.assertIn("TIME", transcription)
