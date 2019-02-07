# -*- coding: utf-8 -*-
import logging
from naomi import testutils
from . import webrtc_vad


class TestWebRTC_VADPlugin(testutils.Test_VADPlugin):

    def setUp(self):
        super(TestWebRTC_VADPlugin, self).setUp()
        self.plugin = testutils.get_plugin_instance(
            webrtc_vad.WebRTCPlugin,
            self._test_input
        )
        # This is just for comparison to see how VAD engines compare in
        # detecting audio. Skip if not in INFO logging level.
        if(self._logger.getEffectiveLevel() < logging.WARN):
            self.map_file()
