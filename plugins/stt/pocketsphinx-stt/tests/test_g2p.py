# -*- coding: utf-8 -*-
import unittest
from naomi import profile
import mock
from .. import g2p


WORDS = ['GOOD', 'BAD', 'UGLY']


def predict():
    return [
        ("good", ["G", "UH", "D"]),
        ("good", ["G", "UW", "D"]),
        ("good", ["G", "UH", "D", "IY"]),
        ("bad", ["B", "AE", "D"]),
        ("bad", ["B", "AA", "D"]),
        ("bad", ["B", "AH", "D"]),
        ("ugly", ["AH", "G", "L", "IY"]),
        ("ugly", ["Y", "UW", "G", "L", "IY"]),
        ("ugly", ["AH", "G", "L", "AY"])
    ]


class TestPatchedG2P(unittest.TestCase):
    def setUp(self):
        self.g2pconv = g2p.PhonetisaurusG2P(
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
            'phonetisaurus.predict',
            return_value=predict()
        ):
            for word in WORDS:
                results = [word for (word, pronunciation) in self.g2pconv.translate([word])]
                self.assertIn(word.lower(), results)

    def testTranslateWords(self):
        with mock.patch(
            'phonetisaurus.predict',
            return_value=predict()
        ):
            results = [word for (word, pronunciation) in self.g2pconv.translate(WORDS)]
            for word in WORDS:
                self.assertIn(word.lower(), results)
