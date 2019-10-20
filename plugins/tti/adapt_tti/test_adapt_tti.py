# -*- coding: utf-8 -*-
import unittest
from naomi import testutils
from . import adapt_tti


class TestClockPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(adapt_tti.AdaptTTIPlugin)
