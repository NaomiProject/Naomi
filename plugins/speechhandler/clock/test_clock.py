# -*- coding: utf-8 -*-
import unittest
from naomi import testutils
from . import clock


class TestClockPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(clock.ClockPlugin)

    def test_handle_method(self):
        mic = testutils.TestMic()
        self.plugin.handle(
            {'input': "What time is it?"},
            mic
        )
        self.assertEqual(len(mic.outputs), 1)
        self.assertIn("It is", mic.outputs[0])
