import logging
import os
import scipy.io.wavfile as wav
from naomi import plugin

try:
    from deepspeech.model import Model
    deepspeech_available = True
except ImportError:
    deepspeech_available = False


class DeepSpeechSTTPlugin(plugin.STTPlugin):
    """
    Speech-To-Text implementation which relies on the DeepSpeech API.
    """

    def __init__(self, *args, **kwargs):
        """
        Create Plugin Instance
        """
        plugin.STTPlugin.__init__(self, *args, **kwargs)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Init DeepSpeech")
        self._logger.debug(str(self.profile))

        if not deepspeech_available:
            self._logger.warning("DeepSpeech import error!")
        #    raise ImportError("DeepSpeech not installed!")

        self._logger.warning("This STT plugin doesn't have multilanguage " +
                             "support!")
        # Beam width used in the CTC decoder when building candidate
        # transcriptions
        try:
            self._BEAM_WIDTH = self.profile["deepspeech"]["beam_width"]
        except KeyError:
            self._BEAM_WIDTH = 500

        # The alpha hyperparameter of the CTC decoder. Language Model weight
        try:
            self._LM_WEIGHT = self.profile["deepspeech"]["lm_weight"]
        except KeyError:
            self._LM_WEIGHT = 1.75

        # The beta hyperparameter of the CTC decoder. Word insertion weight
        # (penalty)
        try:
            self._WORD_COUNT_WEIGHT = self.profile["deepspeech"]["word_count_weight"]
        except KeyError:
            self._WORD_COUNT_WEIGHT = 1.00

        # Valid word insertion weight. This is used to lessen the word
        # insertion penalty when the inserted word is part of the vocabulary
        try:
            self._VALID_WORD_COUNT_WEIGHT = self.profile["deepspeech"]["valid_word_count_weight"]
        except KeyError:
            self._VALID_WORD_COUNT_WEIGHT = 1.00

        # These constants are tied to the shape of the graph used (changing
        # them changes the geometry of the first layer), so make sure you
        # use the same constants that were used during training

        # Number of MFCC features to use
        try:
            self._N_FEATURES = self.profile["deepspeech"]["n_features"]
        except KeyError:
            self._N_FEATURES = 26

        # Size of the context window used for producing timesteps in the
        # input vector
        try:
            self._N_CONTEXT = self.profile["deepspeech"]["n_context"]
        except KeyError:
            self._N_CONTEXT = 9

        # Only 16KHz files are currently supported
        try:
            self._FS = self.profile["deepspeech"]["fs"]
        except KeyError:
            self._FS = 16000

        # These are paths. They are required

        # Path to the model (protocol buffer binary file)
        self._MODEL = self.profile["deepspeech"]["model"]
        if(not os.path.exists(self._MODEL)):
            msg = (
                "DeepSpeech model '%s' does not exist! "
                + "Please make sure that you have set the "
                + "correct deepspeech: model in your profile."
            ) % self._MODEL
            self._logger.error(msg)
            raise RuntimeError(msg)

        # Path to the configuration file specifying the alphabet used
        self._ALPHABET = self.profile["deepspeech"]["alphabet"]
        if(not os.path.exists(self._ALPHABET)):
            msg = (
                "DeepSpeech alphabet '%s' does not exist! "
                + "Please make sure that you have set the "
                + "correct deepspeech: alphabet in your profile."
            ) % self._ALPHABET
            self._logger.error(msg)
            raise RuntimeError(msg)

        # Path to the language model binary file
        self._LM = self.profile["deepspeech"]["language_model"]
        if(not os.path.exists(self._LM)):
            msg = (
                "DeepSpeech language model '%s' does not exist! "
                + "Please make sure that you have set the correct "
                + "deepspeech: language_model in your profile."
            ) % self._LM
            self._logger.error(msg)
            raise RuntimeError(msg)

        # Path to the language model trie file created with
        # native_client/generate_trie
        self._TRIE = self.profile["deepspeech"]["trie"]
        if(not os.path.exists(self._TRIE)):
            msg = (
                "DeepSpeech trie '%s' does not exist! "
                + "Please make sure that you have set the "
                + "correct deepspeech: trie in your profile."
            ) % self._TRIE
            self._logger.error(msg)
            raise RuntimeError(msg)
        self._ds = Model(
            self._MODEL,
            self._N_FEATURES,
            self._N_CONTEXT,
            self._ALPHABET,
            self._BEAM_WIDTH
        )
        self._ds.enableDecoderWithLM(
            self._ALPHABET,
            self._LM,
            self._TRIE,
            self._LM_WEIGHT,
            self._WORD_COUNT_WEIGHT,
            self._VALID_WORD_COUNT_WEIGHT
        )

    def transcribe(self, fp):
        """
        transcribe given audio file object fp and return the result.
        """
        fp.seek(0)
        fs, audio = wav.read(fp)
        # We can assume 16kHz
        # audio_length = len(audio) * (1 / self._FS)
        assert fs == self._FS, (
            "Only %dHz input WAV files are supported for now!" % self._FS
        )

        text = self._ds.stt(audio, self._FS)

        transcribed = [text.upper()]

        return transcribed
