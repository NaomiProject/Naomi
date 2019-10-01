# -*- coding: utf-8 -*-
import unittest
from naomi import testutils
from .terminal import TerminalVisualizationsPlugin


class TestTerminalVisualizationsPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(TerminalVisualizationsPlugin)

