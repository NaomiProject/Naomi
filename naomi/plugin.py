# -*- coding: utf-8 -*-
import abc
import collections
import logging
import mad
import tempfile
import wave
from . import audioengine
from . import commandline
from . import i18n
from . import paths
from . import profile
from . import vocabcompiler


class GenericPlugin(object):
    def __init__(self, info, *args, **kwargs):
        self._plugin_info = info
        if(not hasattr(self, '_logger')):
            self._logger = logging.getLogger(__name__)
        interface = commandline.commandline()
        interface.get_language(once=True)
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations)
        self.gettext = translator.gettext
        # Skip asking for missing settings if we are using a test profile
        if hasattr(self, 'settings') and not profile._test_profile:
            # set a variable here to tell us if all settings are
            # completed or not
            # If all settings do not currently exist, go ahead and
            # re-query all settings for this plugin
            settings_complete = True
            # Step through the settings and check for
            # any missing settings
            settings = self.settings()
            for setting in settings:
                if profile.get_arg("repopulate") or not profile.check_profile_var_exists(setting):
                    # Check if this setting has already been addressed
                    if(setting not in profile._settings):
                        # Go ahead and pull the setting
                        self._logger.info(
                            "{} setting does not exist".format(setting)
                        )
                        settings_complete = False
                # Add the setting to the settings_cache
                profile._settings[setting] = settings[setting]
            if(not settings_complete):
                print(interface.status_text(self.gettext(
                    "Configuring {}"
                ).format(
                    self._plugin_info.name
                )))
                for setting in settings:
                    interface.get_setting(
                        setting, settings[setting]
                    )
                # Save the profile with the new settings
                profile.save_profile()

    @property
    def info(self):
        return self._plugin_info


class AudioEnginePlugin(GenericPlugin, audioengine.AudioEngine):
    pass


class SpeechHandlerPlugin(
    GenericPlugin,
    i18n.GettextMixin,
    metaclass=abc.ABCMeta
):
    def __init__(self, *args, **kwargs):
        GenericPlugin.__init__(self, *args, **kwargs)
        i18n.GettextMixin.__init__(
            self,
            self.info.translations
        )

    @abc.abstractmethod
    def intents(self):
        pass

    @abc.abstractmethod
    def handle(self, intent, mic):
        pass


class STTPlugin(GenericPlugin, metaclass=abc.ABCMeta):
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

        language = profile.get(['language'], 'en-US')

        vocabulary = vocabcompiler.VocabularyCompiler(
            self.info.name, self._vocabulary_name,
            path=paths.sub('vocabularies', language)
        )

        if not vocabulary.matches_phrases(self._vocabulary_phrases):
            vocabulary.compile(
                compilation_func,
                self._vocabulary_phrases
            )

        self._vocabulary_path = vocabulary.path
        return self._vocabulary_path

    @property
    def vocabulary_path(self):
        return self._vocabulary_path

    @abc.abstractmethod
    def transcribe(self, fp):
        pass


class TTSPlugin(GenericPlugin, metaclass=abc.ABCMeta):
    """
    Generic parent class for all speakers
    """
    @abc.abstractmethod
    def say(self, phrase, voice):
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
    # timeout is seconds of audio to capture before first
    # and after last voice detected
    # minimum capture is minimum audio to capture, minus the padding
    # at the front and end
    def __init__(self, input_device, timeout=1, minimum_capture=0.5):
        self._logger = logging.getLogger(__name__)
        # input device
        self._input_device = input_device
        # Here is the number of frames that have to pass without
        # detecing a voice before we respond
        chunklength = input_device._input_chunksize / input_device._input_rate
        self._timeout = round(timeout / chunklength)
        # Mimimum capture frames is the smallest number of frames that will
        # be recognized as audio.
        self._minimum_capture = round((timeout + minimum_capture) / chunklength)
        ct = input_device._input_chunksize / input_device._input_rate
        self._chunktime = ct

    # Override the _voice_detected method with your own method for
    # detecting whether a voice is detected or not. Return True if
    # you detect a voice, otherwise False.
    def _voice_detected(self, *args, **kwargs):
        pass

    def get_audio(self):
        frames = collections.deque([], 30)
        last_voice_frame = 0
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
            voice_detected = self._voice_detected(frame, recording=recording)
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
                    recording_frames = list(frames)[-self._timeout:]
                    last_voice_frame = len(recording_frames)
            else:
                # We're recording
                recording_frames.append(frame)
                if(voice_detected):
                    last_voice_frame = len(recording_frames)
                if(last_voice_frame < len(recording_frames) - self._timeout):
                    # We have waited past the timeout number of frames
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


class TTIPlugin(GenericPlugin, metaclass=abc.ABCMeta):
    intent_map = {'intents': {}}
    keywords = {}
    keyword_index = 0
    regex = {}
    words = {}
    trained = False

    def add_intent(self, intent):
        self.add_intents(intent)

    @abc.abstractmethod
    def add_intents(self, intents):
        pass

    @abc.abstractmethod
    def get_plugin_phrases(self, passive_listen=False):
        pass

    def train(self):
        self.trained = True

    @abc.abstractmethod
    def determine_intent(self, phrase):
        pass

    # FIXME this does not belong here. It should be in a special language object
    @staticmethod
    def cleantext(text):
        language = profile.get(["language"], "en-US")[:2]
        if language == "en":
            # upper case
            text = text.upper()
            words = text.split(" ")
            # Adapted from a list at https://stackoverflow.com/questions/19790188/expanding-english-language-contractions-in-python
            contractions = {
                "AIN'T": "ARE NOT",  # "am not / are not / is not / has not / have not"
                "AREN'T": "ARE NOT",
                "CAN'T": "CAN NOT",
                "CAN'T'VE": "CAN NOT HAVE",
                "'CAUSE": "BECAUSE",
                "COULD'VE": "COULD HAVE",
                "COULDN'T": "COULD NOT",
                "COULDN'T'VE": "COULD NOT HAVE",
                "DIDN'T": "DID NOT",
                "DOESN'T": "DOES NOT",
                "DON'T": "DO NOT",
                "HADN'T": "HAD NOT",
                "HADN'T'VE": "HAD NOT HAVE",
                "HASN'T": "HAS NOT",
                "HAVEN'T": "HAVE NOT",
                "HE'D": "HE WOULD",  # "he had / he would",
                "HE'D'VE": "HE WOULD HAVE",
                "HE'LL": "HE WILL",  # "he shall / he will",
                "HE'LL'VE": "HE WILL HAVE",  # "he shall have / he will have",
                "HE'S": "HE IS",  # "he has / he is",
                "HOW'D": "HOW DID",
                "HOW'D'Y": "HOW DO YOU",
                "HOW'LL": "HOW WILL",
                "HOW'S": "HOW IS",  # "how has / how is / how does",
                "I'D": "I WOULD",  # "I had / I would",
                "I'D'VE": "I WOULD HAVE",
                "I'LL": "I WILL",  # "I shall / I will",
                "I'LL'VE": "I WILL HAVE",  # "I shall have / I will have",
                "I'M": "I AM",
                "I'VE": "I HAVE",
                "ISN'T": "IS NOT",
                "IT'D": "IT WOULD",  # "it had / it would",
                "IT'D'VE": "IT WOULD HAVE",
                "IT'LL": "IT WILL",  # "it shall / it will",
                "IT'LL'VE": "IT WILL HAVE",  # "it shall have / it will have",
                "IT'S": "IT IS",  # "it has / it is",
                "LET'S": "LET US",
                "MA'AM": "MADAM",
                "MAYN'T": "MAY NOT",
                "MIGHT'VE": "MIGHT HAVE",
                "MIGHTN'T": "MIGHT NOT",
                "MIGHTN'T'VE": "MIGHT NOT HAVE",
                "MUST'VE": "MUST HAVE",
                "MUSTN'T": "MUST NOT",
                "MUSTN'T'VE": "MUST NOT HAVE",
                "NEEDN'T": "NEED NOT",
                "NEEDN'T'VE": "NEED NOT HAVE",
                "OUGHTN'T": "OUGHT NOT",
                "OUGHTN'T'VE": "OUGHT NOT HAVE",
                "SHAN'T": "SHALL NOT",
                "SHAN'T'VE": "SHALL NOT HAVE",
                "SHE'D": "SHE WOULD",  # "she had / she would",
                "SHE'D'VE": "SHE WOULD HAVE",
                "SHE'LL": "SHE WILL",  # "she shall / she will",
                "SHE'LL'VE": "SHE WILL HAVE",  # "she shall have / she will have",
                "SHE'S": "SHE IS",  # "she has / she is",
                "SHOULD'VE": "SHOULD HAVE",
                "SHOULDN'T": "SHOULD NOT",
                "SHOULDN'T'VE": "SHOULD NOT HAVE",
                "SO'VE": "SO HAVE",
                "SO'S": "SO IS",  # "so as / so is",
                "THAT'D": "THAT WOULD",  # "that would / that had",
                "THAT'WOULD'VE": "THAT WOULD HAVE",
                "THAT'S": "THAT IS",  # "that has / that is",
                "THERE'D": "THERE WOULD",  # "there had / there would",
                "THERE'D'VE": "THERE WOULD HAVE",
                "THERE'S": "THERE IS",  # "there has / there is",
                "THEY'D": "THEY WOULD",  # "they had / they would",
                "THEY'D'VE": "THEY WOULD HAVE",
                "THEY'LL": "THEY WILL",  # "they shall / they will",
                "THEY'LL'VE": "THEY WILL HAVE",  # "they shall have / they will have",
                "THEY'RE": "THEY ARE",
                "THEY'VE": "THEY HAVE",
                "TO'VE": "TO HAVE",
                "WASN'T": "WAS NOT",
                "WE'D": "WE WOULD",  # "we had / we would",
                "WE'D'VE": "WE WOULD HAVE",
                "WE'LL": "WE WILL",
                "WE'LL'VE": "WE WILL HAVE",
                "WE'RE": "WE ARE",
                "WE'VE": "WE HAVE",
                "WEREN'T": "WERE NOT",
                "WHAT'LL": "WHAT WILL",  # "what shall / what will",
                "WHAT'LL'VE": "WHAT WILL HAVE",  # "what shall have / what will have",
                "WHAT'RE": "WHAT ARE",
                "WHAT'S": "WHAT IS",  # "what has / what is",
                "WHAT'VE": "WHAT HAVE",
                "WHEN'S": "WHEN IS",  # "when has / when is",
                "WHEN'VE": "WHEN HAVE",
                "WHERE'D": "WHERE DID",
                "WHERE'S": "WHERE IS",  # "where has / where is",
                "WHERE'VE": "WHERE HAVE",
                "WHO'LL": "WHO WILL",  # "who shall / who will",
                "WHO'LL'VE": "WHO WILL HAVE",  # "who shall have / who will have",
                "WHO'S": "WHO IS",  # "who has / who is",
                "WHO'VE": "WHO HAVE",
                "WHY'S": "WHY IS",  # "why has / why is",
                "WHY'VE": "WHY HAVE",
                "WILL'VE": "WILL HAVE",
                "WON'T": "WILL NOT",
                "WON'T'VE": "WILL NOT HAVE",
                "WOULD'VE": "WOULD HAVE",
                "WOULDN'T": "WOULD NOT",
                "WOULDN'T'VE": "WOULD NOT HAVE",
                "Y'ALL": "YOU ALL",
                "Y'ALL'D": "YOU ALL WOULD",
                "Y'ALL'D'VE": "YOU ALL WOULD HAVE",
                "Y'ALL'RE": "YOU ALL ARE",
                "Y'ALL'VE": "YOU ALL HAVE",
                "YOU'D": "YOU WOULD",  # "you had / you would",
                "YOU'D'VE": "YOU WOULD HAVE",
                "YOU'LL": "YOU WILL",  # "you shall / you will",
                "YOU'LL'VE": "YOU WILL HAVE",  # "you shall have / you will have",
                "YOU'RE": "YOU ARE",
                "YOU'VE": "YOU HAVE"
            }
            for i, word in enumerate(words):
                # expand contractions
                if word in contractions:
                    words[i] = contractions[word]
                # remove punctuation from beginning and end of words
                while len(words[i]) > 0 and words[i][:1] not in [chr(i) for i in range(65, 91)]:
                    words[i] = words[i][1:]
                while len(words[i]) > 0 and words[i][-1:] not in [chr(i) for i in range(65, 91)]:
                    words[i] = words[i][:-1]
            # put it all back together
            text = " ".join(words)
        return text


class VisualizationsPlugin(GenericPlugin):
    pass


class NotificationClientPlugin(GenericPlugin):

    def __init__(self, *args, **kwargs):
        GenericPlugin.__init__(self, *args, **kwargs)
        self._mic = kwargs["mic"]
        self._brain = kwargs["brain"]
        self.timestamp = kwargs["timestamp"]

    def run(self):
        self.timestamp = self.gather(self.timestamp)
