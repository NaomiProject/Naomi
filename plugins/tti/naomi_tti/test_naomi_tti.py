# -*- coding: utf-8 -*-
import unittest
from naomi import testutils
from . import naomi_tti


class TestNaomiTTIPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(naomi_tti.NaomiTTIPlugin)
