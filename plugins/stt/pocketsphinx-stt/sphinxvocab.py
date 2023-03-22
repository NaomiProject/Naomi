# -*- coding: utf-8 -*-
import logging
import os
import re
from .g2p import PhonetisaurusG2P
from naomi import profile
from naomi.run_command import run_command


def delete_temp_file(file_to_delete):
    if True:
        os.remove(file_to_delete)


def get_languagemodel_path(path):
    """
    Returns:
        The path of the the pocketsphinx languagemodel file as string
    """
    return os.path.join(path, 'languagemodel')


def get_dictionary_path(path):
    """
    Returns:
        The path of the pocketsphinx dictionary file as string
    """
    return os.path.join(path, 'dictionary')


def compile_vocabulary(directory, phrases):
    """
    Compiles the vocabulary to the Pocketsphinx format by creating a
    languagemodel and a dictionary.

    Arguments:
        phrases -- a list of phrases that this vocabulary will contain
    """
    logger = logging.getLogger(__name__)
    languagemodel_path = get_languagemodel_path(directory)
    dictionary_path = get_dictionary_path(directory)

    nbest = profile.get(
        ['pocketsphinx', 'nbest'],
        3
    )
    fst_model = profile.get(['pocketsphinx', 'fst_model'])
    fst_model_alphabet = profile.get(
        ['pocketsphinx', 'fst_model_alphabet'],
        'arpabet'
    )

    if not fst_model:
        raise ValueError('FST model not specified!')

    if not os.path.exists(fst_model):
        raise OSError('FST model {} does not exist!'.format(fst_model))

    g2pconverter = PhonetisaurusG2P(
        fst_model,
        fst_model_alphabet=fst_model_alphabet,
        nbest=nbest
    )

    logger.debug('Languagemodel path: %s' % languagemodel_path)
    logger.debug('Dictionary path:    %s' % dictionary_path)
    logger.debug('Compiling languagemodel...')
    compile_languagemodel(phrases, languagemodel_path)
    logger.debug('Starting dictionary...')
    compile_dictionary(g2pconverter, phrases, dictionary_path)


def compile_languagemodel(corpus, output_file):
    """
    Compiles the languagemodel from a text.

    Arguments:
        corpus -- the text the languagemodel will be generated from
        output_file -- the path of the file this languagemodel will
            be written to

    Returns:
        A list of all unique words this vocabulary contains.
    """
    text = "\n".join([line for line in map(lambda phrase: phrase.lower(), corpus)])
    if len(text.strip()) == 0:
        raise ValueError('No text to compile into languagemodel!')

    logger = logging.getLogger(__name__)

    # Create language model from corpus
    logger.debug("Creating languagemodel file: '%s'" % output_file)
    completedprocess = run_command(
        [
            os.path.join(
                profile.get(['kenlm', 'source_dir']),
                'build',
                'bin',
                'lmplz'
            ),
            '-o', '3',
            '--discount_fallback'
        ],
        4,
        stdin=text
    )
    if completedprocess.returncode == 0:
        if completedprocess.stdout:
            with open(output_file, 'w') as f:
                f.write(completedprocess.stdout.decode("utf-8").strip())
        else:
            print("process completed but produced no output")
    else:
        if completedprocess.stderr:
            print(completedprocess.stderr.decode("utf-8").strip())
        else:
            print("process completed with error but no output")


def compile_dictionary(g2pconverter, corpus, output_file):
    """
    Compiles the dictionary from a list of words.

    Arguments:
        corpus -- the text the dictionary will be generated from
        output_file -- the path of the file this dictionary will
                       be written to
    """
    # read the standard dictionary in
    RE_WORDS = re.compile(
        r"^(?P<word>[a-zA-Z0-9'\.\-]+)(\(\d\))?\s+(?P<pronunciation>[a-zA-Z]+.*[a-zA-Z0-9])\s*$"
    )
    lexicon = {}
    with open(os.path.join(profile.get(['pocketsphinx', 'hmm_dir']), 'cmudict.dict'), 'r') as f:
        line = f.readline().strip()
        while line:
            for match in RE_WORDS.finditer(line):
                try:
                    lexicon[match.group('word')].append(
                        match.group('pronunciation').split()
                    )
                except KeyError:
                    lexicon[match.group('word')] = [
                        match.group('pronunciation').split()
                    ]
            line = f.readline().strip()

    # create a list of words from the corpus
    corpus_lexicon = {}
    words = set()
    for line in corpus:
        for word in line.split():
            words.add(word.lower())

    # Fetch pronunciations for every word in corpus
    for word in words:
        if word in lexicon:
            corpus_lexicon[word] = lexicon[word]
        else:
            corpus_lexicon[word] = []
            for w, p in g2pconverter.translate(word):
                corpus_lexicon[word].append(p)
    with open(output_file, "w") as f:
        for word in sorted(corpus_lexicon):
            for index, phones in enumerate(corpus_lexicon[word]):
                if index == 0:
                    f.write(f"{word} {' '.join(phones)}\n")
                else:
                    f.write(f"{word}({index+1}) {' '.join(phones)}\n")
