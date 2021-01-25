# -*- coding: utf-8 -*-
import unittest
from naomi import testutils
from . import joke


class TestJokePlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(joke.JokePlugin)

    def test_handle_method(self):
        mic = testutils.TestMic(inputs=["WHO'S THERE", "RANDOM RESPONSE", "YES"])
        jokes = joke.get_jokes()
        self.plugin.handle(
            {'input': "Tell me a joke."},
            mic
        )
        self.assertEqual(len(mic.outputs), 5)
        self.assertIn((mic.outputs[1], mic.outputs[2]), jokes)
