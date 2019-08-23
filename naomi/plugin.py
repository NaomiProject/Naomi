# -*- coding: utf-8 -*-
import abc
import collections
import logging
import tempfile
import wave
import mad
from . import paths
from . import vocabcompiler
from . import audioengine
from . import i18n
from . import commandline
from . import profile


class GenericPlugin(object):
    def __init__(self, info, config):
        self._plugin_config = config
        self._plugin_info = info
        if(not hasattr(self, '_logger')):
            self._logger = logging.getLogger(__name__)
        interface = commandline.commandline()
        _ = interface.get_language(once=True)
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations)
        _ = translator.gettext
        if hasattr(self, 'settings'):
            # set a variable here to tell us if all settings are
            # completed or not
            # If all settings do not currently exist, go ahead and
            # re-query all settings for this plugin
            settings_complete = True
            # Step through the settings and check for
            # any missing settings
            for setting in self.settings:
                if not profile.check_profile_var_exists(setting):
                    self._logger.info(
                        "{} setting does not exist".format(setting)
                    )
                    # Go ahead and pull the setting
                    settings_complete = False
            if(profile.get_arg("repopulate") or not settings_complete):
                print(interface.status_text(_(
                    "Configuring {}"
                ).format(
                    self._plugin_info.name
                )))
                for setting in self.settings:
                    interface.get_setting(
                        setting, self.settings[setting]
                    )
                # Save the profile with the new settings
                profile.save_profile()

    @property
    def profile(self):
        # FIXME: Remove this in favor of something better
        return self._plugin_config

    @property
    def info(self):
        return self._plugin_info


class AudioEnginePlugin(GenericPlugin, audioengine.AudioEngine):
    pass


class SpeechHandlerPlugin(GenericPlugin, i18n.GettextMixin):
    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        GenericPlugin.__init__(self, *args, **kwargs)
        i18n.GettextMixin.__init__(
            self,
            self.info.translations
        )

    @abc.abstractmethod
    def get_phrases(self):
        pass

    @abc.abstractmethod
    def handle(self, text, mic):
        pass

    @abc.abstractmethod
    def is_valid(self, text):
        pass

    def get_priority(self):
        return 0


class STTPlugin(GenericPlugin):
    def __init__(self, name, phrases, *args, **kwargs):
        GenericPlugin.__init__(self, *args, **kwargs)
        self._vocabulary_phrases = phrases
        self._vocabulary_name = name
        self._vocabulary_compiled = False
        self._vocabulary_path = None
        self._samplerate = 16000
        self._volume_normalization = None

    def compile_vocabulary(self, compilation_func):
        if self._vocabulary_compiled:
            raise RuntimeError("Vocabulary has already been compiled!")

        try:
            language = self.profile['language']
        except KeyError:
            language = None
        if not language:
            language = 'en-US'

        vocabulary = vocabcompiler.VocabularyCompiler(
            self.info.name, self._vocabulary_name,
            path=paths.sub('vocabularies', language))

        if not vocabulary.matches_phrases(self._vocabulary_phrases):
            vocabulary.compile(
                self.profile, compilation_func, self._vocabulary_phrases)

        self._vocabulary_path = vocabulary.path
        return self._vocabulary_path

    @property
    def vocabulary_path(self):
        return self._vocabulary_path

    @classmethod
    @abc.abstractmethod
    def is_available(cls):
        return True

    @abc.abstractmethod
    def transcribe(self, fp):
        pass


class TTSPlugin(GenericPlugin):
    """
    Generic parent class for all speakers
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def say(self, phrase, *args):
        pass

    def mp3_to_wave(self, filename):
        mf = mad.MadFile(filename)
        with tempfile.SpooledTemporaryFile() as f:
            wav = wave.open(f, mode='wb')
            wav.setframerate(mf.samplerate())
            wav.setnchannels(1 if mf.mode() == mad.MODE_SINGLE_CHANNEL else 2)
            # 4L is the sample width of 32 bit audio
            wav.setsampwidth(4)
            frame = mf.read()
            while frame is not None:
                wav.writeframes(frame)
                frame = mf.read()
            wav.close()
            f.seek(0)
            data = f.read()
        return data


class VADPlugin(GenericPlugin):
    def __init__(self, input_device, timeout=1, minimum_capture=0.5):
        self._logger = logging.getLogger(__name__)
        # input device
        self._input_device = input_device
        # Here is the number of frames that have to pass without
        # detecing a voice before we respond
        chunklength = input_device._input_rate / input_device._input_chunksize
        self._timeout = round(chunklength * timeout)
        # Mimimum capture frames is the smallest number of frames that will
        # be recognized as audio. I'm setting this to 1/2 second longer than
        # the timeout value.
        self._minimum_capture = round(chunklength * (timeout + minimum_capture))
        ct = input_device._input_chunksize / input_device._input_rate
        self._chunktime = ct

    # Override the _voice_detected method with your own method for
    # detecting whether a voice is detected or not. Return True if
    # you detect a voice, otherwise False.
    def _voice_detected(self, frame):
        pass

    def get_audio(self):
        frames = collections.deque([], 30)
        recording = False
        recording_frames = []
        self._logger.info("Waiting for voice data")
        for frame in self._input_device.record(
            self._input_device._input_chunksize,
            self._input_device._input_bits,
            self._input_device._input_channels,
            self._input_device._input_rate
        ):
            frames.append(frame)
            voice_detected = self._voice_detected(frame)
            if not recording:
                if(voice_detected):
                    # Voice activity detected, start recording and use
                    # the last 10 frames to start
                    self._logger.debug(
                        "Started recording on device '{:s}'".format(
                            self._input_device.slug
                        )
                    )
                    recording = True
                    # Include the previous 10 frames in the recording.
                    recording_frames = list(frames)[-10:]
                    last_voice_frame = len(recording_frames)
            else:
                # We're recording
                recording_frames.append(frame)
                if(voice_detected):
                    last_voice_frame = len(recording_frames)
                if(last_voice_frame < len(recording_frames) - self._timeout):
                    # We have waied past the timeout number of frames
                    # so we believe the speaker has finished speaking.
                    recording = False
                    if(len(recording_frames) < self._minimum_capture):
                        self._logger.debug(
                            " ".join([
                                "Recorded {:d} frames, less than threshold",
                                "of {:d} frames ({:.2f} seconds). Discarding"
                            ]).format(
                                len(recording_frames),
                                self._minimum_capture,
                                len(recording_frames) * self._chunktime
                            )
                        )
                    else:
                        self._logger.debug(
                            "Recorded {:d} frames".format(
                                len(recording_frames)
                            )
                        )
                        return recording_frames


class STTTrainerPlugin(GenericPlugin):
    pass
