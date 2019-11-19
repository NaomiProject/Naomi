# -*- coding: utf-8 -*-
import unittest
from naomi import testutils
from . import padatious_tti


class TestPadatiousTTIPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(padatious_tti.PadatiousTTIPlugin)
