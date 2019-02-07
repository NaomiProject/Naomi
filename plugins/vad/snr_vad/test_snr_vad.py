# -*- coding: utf-8 -*-
from naomi import testutils
from . import snr_vad


class TestSNR_VADPlugin(testutils.Test_VADPlugin):

    def setUp(self, *args, **kwargs):
        super(TestSNR_VADPlugin, self).setUp(*args, **kwargs)
        self.plugin = testutils.get_plugin_instance(
            snr_vad.SNRPlugin,
            self._test_input
        )
        # prime by running through one wav file
        self.map_file()
