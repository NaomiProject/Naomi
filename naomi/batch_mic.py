# -*- coding: utf-8 -*-
"""
A drop-in replacement for the Mic class that allows for batch mode operation.
Useful for debugging. Unlike with the typical Mic implementation, Naomi
processes the given commands in the batchfile.
"""
import contextlib
import os.path
import logging
from naomi import profile


def parse_batch_file(fp):
    # parse given batch file and get the filenames or commands
    for line in fp:
        line = line.partition('#')[0].rstrip()
        if line:
            yield line


class Mic(object):
    def __init__(
        self
    ):
        self._logger = logging.getLogger(__name__)
        self._keyword = keyword
        self.passive_stt_engine = passive_stt_engine
        self.active_stt_engine = active_stt_engine
        self.special_stt_slug = special_stt_slug
        self.plugins = plugins
        self._commands = parse_batch_file(batch_file)
        self.passive_listen = profile.get_profile_flag(["passive_listen"])

    @contextlib.contextmanager
    def special_mode(self, name, phrases):
        plugin_info = self.plugins.get_plugin(
            self.special_stt_slug,
            category='stt'
        )
        plugin_config = profile.get_profile()

        original_stt_engine = self.active_stt_engine

        # If the special_mode engine is not specifically set,
        # copy the settings from the active stt engine.
        try:
            mode_stt_engine = plugin_info.plugin_class(
                name,
                phrases,
                plugin_info,
                plugin_config
            )
            if(profile.check_profile_var_exists(['special_stt'])):
                if(profile.check_profile_var_exists([
                    'special_stt',
                    'samplerate'
                ])):
                    mode_stt_engine._samplerate = int(
                        profile.get_profile_var([
                            'special_stt',
                            'samplerate'
                        ])
                    )
                if(profile.check_profile_var_exists([
                    'special_stt',
                    'volume_normalization'
                ])):
                    mode_stt_engine._volume_normalization = float(
                        profile.get_profile_var([
                            'special_stt',
                            'volume_normalization'
                        ])
                    )
            else:
                mode_stt_engine._samplerate = self.active_stt_engine._samplerate
                mode_stt_engine._volume_normalization = self.active_stt_engine._volume_normalization
            self.active_stt_engine = mode_stt_engine
            yield
        finally:
            self.active_stt_engine = original_stt_engine

    def transcribe_command(self, command):
        # check if command is a filename
        if os.path.isfile(command):
            # handle it as mic input
            try:
                fp = open(command, 'rb')
            except (OSError, IOError) as e:
                self._logger.error('Failed to open "%s": %s',
                                   command, e.strerror)
            else:
                transcribed = self.active_stt_engine.transcribe(fp)
                fp.close()
        else:
            # handle it as text input
            transcribed = [command]
        return transcribed

    def wait_for_keyword(self, keyword='NAOMI'):
        if(self.passive_listen):
            return self.active_listen()
        else:
            return

    def active_listen(self, timeout=3):
        try:
            command = next(self._commands)
        except StopIteration:
            raise SystemExit
        else:
            transcribed = self.transcribe_command(command)
            if transcribed:
                print('YOU: %r' % transcribed)
            return transcribed

    def listen(self):
        return self.active_listen()

    def say(self, phrase, OPTIONS=None):
        print("{}: {}".format(self._keyword, phrase))
