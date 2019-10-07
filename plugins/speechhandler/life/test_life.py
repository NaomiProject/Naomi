# -*- coding: utf-8 -*-
import unittest
from naomi import testutils
from .life import MeaningOfLifePlugin


class TestMeaningOfLifePlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(MeaningOfLifePlugin)

    def test_handle_method(self):
        mic = testutils.TestMic()
        self.plugin.handle({'input': "What is the meaning of life?"}, mic)
        self.assertEqual(len(mic.outputs), 1)
