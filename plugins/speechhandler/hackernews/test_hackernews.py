# -*- coding: utf-8 -*-
import unittest
from naomi import testutils, diagnose
from . import hackernews


class TestGmailPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(
            hackernews.HackerNewsPlugin)

    def test_is_valid_method(self):
        self.assertTrue(self.plugin.is_valid(
            "Find me some of the top hacker news stories."))
        self.assertFalse(self.plugin.is_valid("What time is it?"))

    @unittest.skipIf(not diagnose.check_network_connection(),
                     "No internet connection")
    def test_handle_method(self):
        mic = testutils.TestMic(inputs=["No."])
        self.plugin.handle("Find me some of the top hacker news stories.", mic)
        self.assertGreater(len(mic.outputs), 1)
        self.assertIn("current top stories", mic.outputs[1])
