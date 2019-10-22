import os
import scipy.io.wavfile as wav
from collections import OrderedDict
from naomi import plugin
from naomi import profile


try:
    from deepspeech.model import Model
    deepspeech_available = True
except ImportError:
    try:
        from deepspeech import Model  # v0.4.1
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
        if not deepspeech_available:
            self._logger.warning("DeepSpeech import error!")
            raise ImportError("DeepSpeech not installed!")
        # Beam width used in the CTC decoder when building candidate
        # transcriptions
        self._BEAM_WIDTH = profile.get(
            ['deepspeech', 'beam_width'],
            500
        )

        # The alpha hyperparameter of the CTC decoder. Language Model weight
        self._LM_WEIGHT = profile.get(
            ['deepspeech', 'lm_weight'],
            1.75
        )

        # The beta hyperparameter of the CTC decoder. Word insertion weight
        # (penalty)
        self._WORD_COUNT_WEIGHT = profile.get(
            ['deepspeech', 'word_count_weight'],
            1.00
        )

        # Valid word insertion weight. This is used to lessen the word
        # insertion penalty when the inserted word is part of the vocabulary
        self._VALID_WORD_COUNT_WEIGHT = profile.get(
            ['deepspeech', 'valid_word_count_weight'],
            1.00
        )

        # These constants are tied to the shape of the graph used (changing
        # them changes the geometry of the first layer), so make sure you
        # use the same constants that were used during training

        # Number of MFCC features to use
        self._N_FEATURES = profile.get(
            ['deepspeech', 'n_features'],
            26
        )

        # Size of the context window used for producing timesteps in the
        # input vector
        self._N_CONTEXT = profile.get(
            ['deepspeech', 'n_context'],
            9
        )

        # Only 16KHz files are currently supported
        self._FS = profile.get(
            ['deepspeech', 'fs'],
            16000
        )

        # These are paths. They are required

        # Path to the model (protocol buffer binary file)
        self._MODEL = os.path.expanduser(
            profile.get(
                ['deepspeech', 'model']
            )
        )
        if(not os.path.exists(self._MODEL)):
            msg = " ".join([
                "DeepSpeech model '{}' does not exist!",
                "Please make sure that you have set the",
                "correct deepspeech: model in your profile."
            ]).format(self._MODEL)
            self._logger.error(msg)
            raise RuntimeError(msg)

        # Path to the configuration file specifying the alphabet used
        self._ALPHABET = os.path.expanduser(
            profile.get(
                ["deepspeech", "alphabet"]
            )
        )
        if(not os.path.exists(self._ALPHABET)):
            msg = " ".join([
                "DeepSpeech alphabet '{}' does not exist!",
                "Please make sure that you have set the",
                "correct deepspeech: alphabet in your profile."
            ]).format(self._ALPHABET)
            self._logger.error(msg)
            raise RuntimeError(msg)

        # Path to the language model binary file
        self._LM = os.path.expanduser(
            profile.get(
                ["deepspeech", "language_model"]
            )
        )
        if(not os.path.exists(self._LM)):
            msg = " ".join([
                "DeepSpeech language model '{}' does not exist!",
                "Please make sure that you have set the correct",
                "deepspeech: language_model in your profile."
            ]).format(self._LM)
            self._logger.error(msg)
            raise RuntimeError(msg)

        # Path to the language model trie file created with
        # native_client/generate_trie
        self._TRIE = os.path.expanduser(
            profile.get(
                ["deepspeech", "trie"]
            )
        )
        if(not os.path.exists(self._TRIE)):
            msg = " ".join([
                "DeepSpeech trie '{}' does not exist!",
                "Please make sure that you have set the",
                "correct deepspeech: trie in your profile."
            ]).format(self._TRIE)
            self._logger.error(msg)
            raise RuntimeError(msg)
        self._ds = Model(
            self._MODEL,
            self._N_FEATURES,
            self._N_CONTEXT,
            self._ALPHABET,
            self._BEAM_WIDTH
        )
        try:
            self._ds.enableDecoderWithLM(
                self._ALPHABET,
                self._LM,
                self._TRIE,
                self._LM_WEIGHT,
                self._WORD_COUNT_WEIGHT,
                self._VALID_WORD_COUNT_WEIGHT
            )
        except TypeError:
            # the current PyPi version does not
            # use the Valid word count weight
            self._ds.enableDecoderWithLM(
                self._ALPHABET,
                self._LM,
                self._TRIE,
                self._LM_WEIGHT,
                self._WORD_COUNT_WEIGHT
            )

    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ('deepspeech', 'alphabet'), {
                        'title': _('DeepSpeech alphabet.txt'),
                        'description': "".join([
                            _('The alphabet file for your deepspeech')
                        ]),
                        'default': '~/deepspeech-0.5.1-models/alphabet.txt'
                    }
                ),
                (
                    ('deepspeech', 'language_model'), {
                        'title': _('DeepSpeech language model'),
                        'description': "".join([
                            _('The deepspeech language model file')
                        ]),
                        'default': '~/deepspeech-0.5.1-models/lm.binary'
                    }
                ),
                (
                    ('deepspeech', 'model'), {
                        'title': _('DeepSpeech neural network graph model'),
                        'description': "".join([
                            _('The deepspeech neural network graph model file')
                        ]),
                        'default': '~/deepspeech-0.5.1-models/output_graph.pbmm'
                    }
                ),
                (
                    ('deepspeech', 'trie'), {
                        'title': _('DeepSpeech language model'),
                        'description': "".join([
                            _('The deepspeech trie file')
                        ]),
                        'default': '~/deepspeech-0.5.1-models/trie'
                    }
                )
            ]
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
            "Input wav file is %dHz, expecting %dHz" % (fs, self._FS)
        )

        text = self._ds.stt(audio, self._FS)

        transcribed = [text.upper()]

        return transcribed
