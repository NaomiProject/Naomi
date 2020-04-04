# -*- coding: utf-8 -*-
import unittest
from naomi import testutils, diagnose
from . import hackernews


class TestHackerNewsPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(
            hackernews.HackerNewsPlugin
        )

<<<<<<< HEAD
    @unittest.skipIf(not diagnose.check_network_connection(),
                     "No internet connection")
=======
    @unittest.skipIf(
        not diagnose.check_network_connection(),
        "No internet connection"
    )
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
    def test_handle_method(self):
        mic = testutils.TestMic(inputs=["No."])
        self.plugin.handle(
            {'input': "Find me some of the top hacker news stories."},
            mic
        )
        self.assertGreater(len(mic.outputs), 1)
        self.assertIn("current top stories", mic.outputs[1])
