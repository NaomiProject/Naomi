# -*- coding: utf-8 -*-
import unittest
from naomi import testutils
from naomi import brain
from naomi import plugin
from naomi import pluginstore
from naomi import profile


class ExampleSpeechHandlerPlugin(plugin.SpeechHandlerPlugin):
    def __init__(self, test_phrases):
        info = testutils.test_info(test_phrases)
        super(ExampleSpeechHandlerPlugin, self).__init__(info)
        self.test_phrases = test_phrases

    def intents(self):
        return {
            'TestIntent': {
<<<<<<< HEAD
                'templates': self.test_phrases,
=======
                'locale': {
                    'en-US': {
                        'templates': self.test_phrases,
                    }
                },
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
                'action': None
            }
        }

    def handle(self, intent, mic):
        mic.say("Test")


class TestBrain(unittest.TestCase):
    # aaronc 2019-10-04 Since we now have an actual intent parser,
    # it is no longer necessary to use priority to organize the
    # plugins.
    # def testPriority(self):
    #     """Does Brain sort modules by priority?"""
    #     my_brain = brain.Brain(testutils.test_profile())
    #
    #     plugin1 = ExamplePlugin(['MOCK1'], priority=1)
    #     plugin2 = ExamplePlugin(['MOCK1'], priority=999)
    #     plugin3 = ExamplePlugin(['MOCK2'], priority=998)
    #     plugin4 = ExamplePlugin(['MOCK1'], priority=0)
    #     plugin5 = ExamplePlugin(['MOCK2'], priority=-3)
    #
    #     for plugin in (plugin1, plugin2, plugin3, plugin4, plugin5):
    #         my_brain.add_plugin(plugin)
    #
    #     expected_order = [plugin2, plugin3, plugin1, plugin4, plugin5]
    #     self.assertEqual(expected_order, my_brain.get_plugins())
    #
    #     input_texts = ['MOCK1']
    #     plugin, output_text = my_brain.query(input_texts)
    #     self.assertIs(plugin, plugin2)
    #     self.assertEqual(input_texts[0], output_text)
    #
    #     input_texts = ['MOCK2']
    #     plugin, output_text = my_brain.query(input_texts)
    #     self.assertIs(plugin, plugin3)
    #     self.assertEqual(input_texts[0], output_text)

    # AJC 2019-08-07 This is no longer true. We now have a list of
    # additional phrases to help the parser.
    # Every element of expected_phrases must exist in extracted_phrases,
    # but they do not have to be equal.
    def testPluginPhraseExtraction(self):
        expected_phrases = ['MOCK1', 'MOCK2']

        self.plugins = pluginstore.PluginStore()
        self.plugins.detect_plugins()
        tti_slug = 'Naomi TTI'
        tti_info = self.plugins.get_plugin(
            tti_slug,
            category='tti'
        )
        intent_parser = tti_info.plugin_class(tti_info)
        profile.set_profile(testutils.test_profile())
        my_brain = brain.Brain(intent_parser)

        my_brain.add_plugin(ExampleSpeechHandlerPlugin(['MOCK2']))
        my_brain.add_plugin(ExampleSpeechHandlerPlugin(['MOCK1']))

        extracted_phrases = my_brain.get_plugin_phrases()

        self.assertListContains(expected_phrases, extracted_phrases)

    # AJC 2019-08-07 This whole test makes no sense to me
    # It looks like it is writing 'MOCK' to a temporary file
    # which somehow brain.get_standard_phrases is supposed
    # to figure out is the file to use for reading the
    # list of standard phrases from
    # def testStandardPhraseExtraction(self):
    #    expected_phrases = [b'MOCK']
    #
    #    my_brain = brain.Brain(testutils.test_profile())
    #
    #    with tempfile.TemporaryFile() as f:
    #        # We can't use mock_open here, because it doesn't seem to work
    #        # with the 'for line in f' syntax
    #        f.write(b"MOCK\n")
    #        f.seek(0)
    #        with mock.patch('%s.open' % brain.__name__,
    #                        return_value=f, create=True):
    #            extracted_phrases = my_brain.get_standard_phrases()
    #    self.assertEqual(expected_phrases, extracted_phrases)

    @staticmethod
    def assertListContains(child_list, parent_list):
        if not all(elem in parent_list for elem in child_list):
            raise AttributeError("list does not contain elements of other list")
