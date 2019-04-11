# -*- coding: utf-8 -*-
import unittest
from naomi import profile
from naomi import testutils
import mock
from .. import g2p


WORDS = ['GOOD', 'BAD', 'UGLY']


class DummyProc(object):
    def __init__(self, *args, **kwargs):
        profile.set_profile(testutils.test_profile())
        self.returncode = 0
        self.stderr = mock.Mock()
        self.stderr.readline = mock.Mock(return_value='')

    def communicate(self):
        if(profile.get_profile_var([
            'pocketsphinx',
            'phonetisaurus_executable'
        ]) == "phonetisaurus-g2p"):
            return (
                '\n'.join([
                    "GOOD\t9.20477\t<s> G UH D </s>",
                    "GOOD\t14.4036\t<s> G UW D </s>",
                    "GOOD\t16.0258\t<s> G UH D IY </s>",
                    "BAD\t0.7416\t<s> B AE D </s>",
                    "BAD\t12.5495\t<s> B AA D </s>",
                    "BAD\t13.6745\t<s> B AH D </s>",
                    "UGLY\t12.572\t<s> AH G L IY </s>",
                    "UGLY\t17.9278\t<s> Y UW G L IY </s>",
                    "UGLY\t18.9617\t<s> AH G L AY </s>"
                ]).encode("utf-8"),
                "".encode("utf-8")
            )
        else:
            return (
                '\n'.join([
                    "GOOD\t9.20477\tG UH D",
                    "GOOD\t14.4036\tG UW D",
                    "GOOD\t16.0258\tG UH D IY",
                    "BAD\t0.7416\tB AE D",
                    "BAD\t12.5495\tB AA D",
                    "BAD\t13.6745\tB AH D",
                    "UGLY\t12.572\tAH G L IY",
                    "UGLY\t17.9278\tY UW G L IY",
                    "UGLY\t18.9617\tAH G L AY"
                ]).encode("utf-8"),
                "".encode("utf-8")
            )

    def poll(self):
        return 1


class TestPatchedG2P(unittest.TestCase):
    def setUp(self):
        self.g2pconv = g2p.PhonetisaurusG2P(
            'phonetisaurus-g2pfst',
            'dummy_fst_model.fst',
            nbest=3
        )

    @unittest.skipIf(
        not profile.check_profile_var_exists(
            ['pocketsphinx']
        ),
        "Pocketsphinx not configured"
    )
    def testTranslateWord(self):
        with mock.patch(
            'subprocess.Popen',
            return_value=DummyProc()
        ):
            for word in WORDS:
                self.assertIn(word, self.g2pconv.translate(word).keys())

    def testTranslateWords(self):
        with mock.patch(
            'subprocess.Popen',
            return_value=DummyProc()
        ):
            results = self.g2pconv.translate(WORDS).keys()
            for word in WORDS:
                self.assertIn(word, results)
