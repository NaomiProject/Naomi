import logging
import os
import pipes
import subprocess
import tempfile
import unittest
from naomi import diagnose
from naomi import plugin
from naomi import profile


EXECUTABLE = 'flite'

if not diagnose.check_executable(EXECUTABLE):
    raise unittest.SkipTest(
        "Skipping flite-tts, executable '{}' not found".format(EXECUTABLE)
    )
    raise ImportError("Executable '%s' not found!" % EXECUTABLE)


class FliteTTSPlugin(plugin.TTSPlugin):
    """
    Uses the flite speech synthesizer
    Requires flite to be available
    """

    def __init__(self, *args, **kwargs):
        plugin.TTSPlugin.__init__(self, *args, **kwargs)

        self._logger = logging.getLogger(__name__)
        self._logger.warning(
            "This TTS plugin doesn't have multilanguage support!"
        )
        voice = profile.get(['flite-tts', 'voice'], '')
        self._logger.info("Voice: {}".format(voice))
        voices = self.get_voices()
        if not voice or voice not in voices:
            self._logger.info(
                "Voice {} not in Voices {}".format(voice, voices)
            )
            voice = ''
        self.voice = voice

    @classmethod
    def get_voices(cls):
        cmd = ['flite', '-lv']
        voices = []
        with tempfile.SpooledTemporaryFile() as out_f:
            subprocess.call(cmd, stdout=out_f)
            out_f.seek(0)
            for line in out_f:
                strline = line.decode("utf-8")
                if strline.startswith('Voices available: '):
                    voices.extend([x.strip() for x in strline[18:].split()
                                   if x.strip()])
        return voices

    def say(self, phrase, voice=None):
        if not voice:
            voice = self.voice
        cmd = ['flite']
        if self.voice:
            self._logger.info("voice = {}".format(voice))
            cmd.extend(['-voice', voice])
        else:
            self._logger.info("voice is false")
        cmd.extend(['-t', phrase])
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            fname = f.name
        cmd.append(fname)
        with tempfile.SpooledTemporaryFile() as out_f:
            self._logger.debug('Executing %s',
                               ' '.join([pipes.quote(arg)
                                         for arg in cmd]))
            subprocess.call(cmd, stdout=out_f, stderr=out_f)
            out_f.seek(0)
            output = out_f.read().strip()
        if output:
            self._logger.debug("Output was: '%s'", output)

        with open(fname, 'rb') as f:
            data = f.read()
        os.remove(fname)
        return data
