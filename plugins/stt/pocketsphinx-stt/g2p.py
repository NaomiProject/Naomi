# -*- coding: utf-8 -*-
import os
import phonetisaurus
import re
import logging
from . import phonemeconversion


class PhonetisaurusG2P(object):
    def __init__(
        self,
        fst_model,
        fst_model_alphabet='arpabet',
        nbest=None
    ):
        self._logger = logging.getLogger(__name__)

        self.fst_model = os.path.abspath(fst_model)
        self._logger.debug("Using FST model: '%s'", self.fst_model)

        self.fst_model_alphabet = fst_model_alphabet
        self._logger.debug(
            "Using FST model alphabet: '%s'" % self.fst_model_alphabet
        )

        self.nbest = nbest
        if (self.nbest is not None):
            self._logger.debug("Will use the %d best results.", self.nbest)

    def _convert_phonemes(self, data):
        if (self.fst_model_alphabet == 'xsampa'):
            for word in data:
                converted_phonemes = []
                for phoneme in data[word]:
                    converted_phonemes.append(
                        phonemeconversion.xsampa_to_arpabet(phoneme))
                data[word] = converted_phonemes
            return data
        elif self.fst_model_alphabet == 'arpabet':
            return data
        raise ValueError('Invalid FST model alphabet!')

    def _translate_word(self, word):
        return self._translate_words([word])

    def _translate_words(self, words):
        return phonetisaurus.predict(
            words,
            self.fst_model,
            nbest=self.nbest
        )

    def translate(self, words):
        self._logger.debug(
            'Converting {} word{} to phonemes'.format(
                len(words),
                's' if len(words) > 1 else ''
            )
        )
        output = list(self._translate_words(words))
        self._logger.debug(
            'G2P conversion returned phonemes for {} word{}'.format(
                len(output),
                's' if len(output) > 1 else ''
            )
        )
        self._logger.debug(output)

        return self._convert_phonemes(output)

    # This is used to train a model that can be used to guess the pronunciation
    # of new words not contained in the sample dictionary.
    # This is a rather silly procedure since the phonetisaurus-train command
    # works well, but this allows us to use the CMUDict.dict dictionary without
    # reformatting it.
    @staticmethod
    def train_fst(dict_file, fst_file):
        """
        parameters:
            dict_file - location of the dictionary file to read from
            fst_file - location of the fst file to create
        """
        RE_WORDS = re.compile(
            r"^(?P<word>[a-zA-Z0-9'\.\-]+)(\(\d\))?\s+(?P<pronunciation>[a-zA-Z]+.*[a-zA-Z0-9])\s*$"
        )
        lexicon = {}
        with open(dict_file, 'r') as f:
            line = f.readline().strip()
            while line:
                one = False
                for match in RE_WORDS.finditer(line):
                    one = True
                    try:
                        lexicon[match.group('word')].append(
                            match.group('pronunciation').split()
                        )
                    except KeyError:
                        lexicon[match.group('word')] = [
                            match.group('pronunciation').split()
                        ]
                if (not one):
                    print(line)
                line = f.readline().strip()
        phonetisaurus.train(
            lexicon,
            model_path=fst_file
        )
