# -*- coding: utf-8 -*-
import unittest
from naomi import testutils, diagnose
from . import news


class TestGmailPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(
            news.NewsPlugin
        )

    @unittest.skipIf(not diagnose.check_network_connection(),
                     "No internet connection")
    def test_handle_method(self):
        mic = testutils.TestMic(inputs=["No."])
        self.plugin.handle("Find me some of the top news stories.", mic)
        self.assertGreater(len(mic.outputs), 1)
        self.assertIn("top headlines", mic.outputs[1])
