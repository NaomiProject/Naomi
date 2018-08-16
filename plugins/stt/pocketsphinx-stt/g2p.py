# -*- coding: utf-8 -*-
import os
import re
import subprocess
import tempfile
import logging
from . import phonemeconversion


def execute(executable, fst_model, input, is_file=False, nbest=None):
    logger = logging.getLogger(__name__)

    RE_WORDS = re.compile(
        r'(?P<word>[a-zA-Z]+)\s+(?P<precision>\d+\.\d+)\s+' +
        r'(?:(?P<sep><s>\s+)){0,1}(?P<pronounciation>.+)' +
        r'(?(sep)\s+</s>)',
        re.MULTILINE
    )
    RE_ISYMNOTFOUND = re.compile(
        r'^Symbol: \'(?P<symbol>.+)\' not found in ' +
        r'input symbols table'
    )
    # the newer version of phonetisaurus uses a different filename
    # and a different method
    if(executable == 'phonetisaurus-g2pfst'):
        cmd = [executable,
            '--model=%s' % fst_model,
            '--beam=1000',
            '--thresh=99.0',
            '--accumulate=true',
            '--pmass=0.85',
            '--nlog_probs=false',
            '--wordlist=%s' % input]
        # In this case, the output looks a little different
        # from the old g2p output
        # For example:
        #     phonetisaurus-g2p:     ANSWER	12.2497	<s> AE N S ER </s>
        #     phonetisaurus-g2pfst:  ANSWER	1	AE1 N S ER0
        RE_WORDS = re.compile(
            r'(?P<word>[a-zA-Z]+)\s+(?P<precision>[\d\.]+)\s+' +
            r'(?P<pronounciation>[a-zA-Z]+.*[a-zA-Z0-9])\s*$',
            re.MULTILINE)
    else:
        cmd = [executable,
            '--model=%s' % fst_model,
            '--input=%s' % input,
            '--words']
        if is_file:
            cmd.append('--isfile')

    if nbest is not None:
        cmd.extend(['--nbest=%d' % nbest])

    cmd = [str(x) for x in cmd]
    logger.debug("cmd: %s" % cmd)
    try:
        # FIXME: We can't just use subprocess.call and redirect stdout
        # and stderr, because it looks like Phonetisaurus can't open
        # an already opened file descriptor a second time. This is why
        # we have to use this somehow hacky subprocess.Popen approach.
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        while proc.poll() is None:
            nextline = proc.stderr.readline()
            logger.debug("NextLine: '%s'" % nextline)
            if(nextline == ''):
                continue
            if(len(RE_ISYMNOTFOUND.findall(nextline)) > 0):
                # instead of killing the process or raising an error,
                # just skip the line.
                # This will create the checksum which will continue
                # to be valid, while allowing the user to generate
                # their own language model.
                # http://www.speech.cs.cmu.edu/tools/lmtool-new.html
                logger.error('Input symbol not found')
                continue
        stdoutdata, stderrdata = proc.communicate()
        logger.debug("StdOutData: %s" % stdoutdata)
    except OSError:
        logger.error(
            "Error occured while executing command '%s'" % ' '.join(cmd),
            exc_info=True
        )
        raise

    if(stderrdata):
        for line in stderrdata.splitlines():
            message = line.strip()
            if(message):
                logger.debug(message)

    if(proc.returncode != 0):
        logger.error(
            "Command '%s' return with exit status %d" % ' '.join(cmd),
            proc.returncode
        )
        raise OSError("Command execution failed")

    result = {}
    if stdoutdata is not None:
        for match in RE_WORDS.finditer(stdoutdata):
            word = match.group('word')
            pronounciation = match.group('pronounciation')
            if word not in result:
                result[word] = []
            result[word].append(pronounciation)
    return result


class PhonetisaurusG2P(object):
    def __init__(
        self,
        executable,
        fst_model,
        fst_model_alphabet='arpabet',
        nbest=None
    ):
        self._logger = logging.getLogger(__name__)

        self.executable = executable

        self.fst_model = os.path.abspath(fst_model)
        self._logger.debug("Using FST model: '%s'", self.fst_model)

        self.fst_model_alphabet = fst_model_alphabet
        self._logger.debug(
            "Using FST model alphabet: '%s'" % self.fst_model_alphabet
        )

        self.nbest = nbest
        if(self.nbest is not None):
            self._logger.debug("Will use the %d best results.", self.nbest)

    def _convert_phonemes(self, data):
        if(self.fst_model_alphabet == 'xsampa'):
            print("xsampa: %s" % data)
            quit()
            for word in data:
                converted_phonemes = []
                for phoneme in data[word]:
                    converted_phonemes.append(
                        phonemeconversion.xsampa_to_arpabet(phoneme))
                data[word] = converted_phonemes
            return data
        elif self.fst_model_alphabet == 'arpabet':
            print('arpabet: %s' % data)
            return data
        raise ValueError('Invalid FST model alphabet!')

    def _translate_word(self, word):
        self._logger.debug("enter _translate_word")
        return execute(
            self.executable,
            self.fst_model,
            word,
            nbest=self.nbest
        )

    def _translate_words(self, words):
        self._logger.debug("enter _translate_words")
        with tempfile.NamedTemporaryFile(suffix='.g2p', delete=False) as f:
            # The 'delete=False' kwarg is kind of a hack, but Phonetisaurus
            # won't work if we remove it, because it seems that I can't open
            # a file descriptor a second time.
            for word in words:
                self._logger.debug(word)
                f.write("%s\n" % word)
            tmp_fname = f.name
        self._logger.debug("Self.executable = %s" % self.executable)
        self._logger.debug("Self.fst_model = %s" % self.fst_model)
        self._logger.debug("tmp_fname = %s" % tmp_fname)
        self._logger.debug("nbest = %s" % self.nbest)
        self._logger.debug(
            ("%s --model=%s --beam=1000 --thresh=99.0 --accumulate=true " +
            "--pmass=0.85 --nlog_probs=false --wordlist=%s --nbest=%d") %
            (self.executable, self.fst_model, tmp_fname, self.nbest)
        )

        output = execute(
            self.executable,
            self.fst_model,
            tmp_fname,
            is_file=True,
            nbest=self.nbest
        )

        os.remove(tmp_fname)
        return output

    def translate(self, words):
        if type(words) is str or len(words) == 1:
            self._logger.debug('Converting single word to phonemes')
            output = self._translate_word(
                words if type(words) is str else words[0]
            )
        else:
            self._logger.debug('Converting %d words to phonemes', len(words))
            output = self._translate_words(words)
        self._logger.debug(
            'G2P conversion returned phonemes for %d words' % len(output)
        )
        self._logger.debug(output)

        return self._convert_phonemes(output)
