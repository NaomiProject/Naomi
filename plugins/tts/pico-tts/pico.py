import logging
import os
import pipes
import re
import subprocess
import tempfile
import unittest
from naomi import diagnose
from naomi import plugin
from naomi import profile

EXECUTABLE = 'pico2wave'

if not diagnose.check_executable(EXECUTABLE):
    raise unittest.SkipTest("Skipping Pico, executable '%s' not found!" % EXECUTABLE)
    raise ImportError("Executable '%s' not found!" % EXECUTABLE)


class PicoTTSPlugin(plugin.TTSPlugin):
    """
    Uses the svox-pico-tts speech synthesizer
    Requires pico2wave to be available
    """

    def __init__(self, *args, **kwargs):
        plugin.TTSPlugin.__init__(self, *args, **kwargs)

        language = profile.get(['language'], 'en-US')

        available_languages = self.get_languages()
        if language not in available_languages:
            raise ValueError("Language '%s' not supported" % language)

        self._language = language

    def get_languages(self):
        cmd = [EXECUTABLE, '-l', 'NULL',
                           '-w', os.devnull,
                           'NULL']
        with tempfile.SpooledTemporaryFile() as f:
            subprocess.call(cmd, stderr=f)
            f.seek(0)
            output = f.read().decode('utf-8')
        pattern = re.compile(r'Unknown language: NULL\nValid languages:\n' +
                             r'((?:[a-z]{2}-[A-Z]{2}\n)+)')
        matchobj = pattern.match(output)
        if not matchobj:
            raise RuntimeError("%s: valid languages not detected" % EXECUTABLE)
        langs = matchobj.group(1).split()
        return langs

    def say(self, phrase):
        logger = logging.getLogger(__name__)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            fname = f.name

        cmd = [EXECUTABLE, '-w', fname,
                           '-l', self._language,
                           phrase]
        logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                               for arg in cmd]))
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
            if output:
                logger.debug("Output was: '%s'", output)
        with open(fname, 'rb') as f:
            data = f.read()
        os.remove(fname)
        return data
