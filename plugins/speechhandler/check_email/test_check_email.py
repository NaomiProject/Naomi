# -*- coding: utf-8 -*-
import unittest
from . import check_email
from naomi import diagnose
from naomi import profile
from naomi import testutils


class TestCheckEmailPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(
            check_email.CheckEmailPlugin
        )

    @unittest.skipIf(
        not diagnose.check_network_connection(),
        "No internet connection"
    )
    def test_handle_method(self):
        if not profile.get(['email', 'password']):
            self.skipTest("Email password not available")

        mic = testutils.TestMic()
        self.plugin.handle(
            {'input': "Check my email account!"}
            , mic
        )
