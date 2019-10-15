import os.path
import tempfile
from collections import OrderedDict
from naomi import plugin
from naomi import profile
from . import sphinxvocab
try:
    try:
        from pocketsphinx import pocketsphinx
    except ValueError:
        # Fixes a quirky bug when first import doesn't work.
        # See http://sourceforge.net/p/cmusphinx/bugs/284/ for details.
        from pocketsphinx import pocketsphinx
    pocketsphinx_available = True
    # Why do we have to import sphinxbase.sphinxbase.*?
    # otherwise, when we create pocketsphinx.Decoder.default_config()
    # we get the wrong object for some reason.
    from sphinxbase.sphinxbase import *
except ImportError:
    pocketsphinx = None
    pocketsphinx_available = False


# AaronC - This searches some standard places (/bin, /usr/bin, /usr/local/bin)
# for a program name.
# This could be updated to search the PATH, and also verify that execute
# permissions are set, but for right now this is a quick and dirty
# placeholder.
def check_program_exists(program):
    standardlocations = ['/usr/local/bin', '/usr/bin', '/bin']
    response = False
    for location in standardlocations:
        if(os.path.isfile(os.path.join(location, program))):
            response = True
    return response


class PocketsphinxSTTPlugin(plugin.STTPlugin):
    """
    The default Speech-to-Text implementation which relies on PocketSphinx.
    """
    _logfile = None

    def __init__(self, *args, **kwargs):
        """
        Initiates the pocketsphinx instance.

        Arguments:
            vocabulary -- a PocketsphinxVocabulary instance
            hmm_dir -- the path of the Hidden Markov Model (HMM)
        """
        plugin.STTPlugin.__init__(self, *args, **kwargs)

        if not pocketsphinx_available:
            raise ImportError("Pocketsphinx not installed!")

        vocabulary_path = self.compile_vocabulary(
            sphinxvocab.compile_vocabulary)

        lm_path = sphinxvocab.get_languagemodel_path(vocabulary_path)
        dict_path = sphinxvocab.get_dictionary_path(vocabulary_path)
        hmm_dir = profile.get(['pocketsphinx', 'hmm_dir'])

        self._logger.debug(
            "Initializing PocketSphinx Decoder with hmm_dir '{}'".format(
                hmm_dir
            )
        )
        # Perform some checks on the hmm_dir so that we can display more
        # meaningful error messages if neccessary
        if not os.path.exists(hmm_dir):
            msg = " ".join([
                "hmm_dir '{}' does not exist! Please make sure that you",
                "have set the correct hmm_dir in your profile."
            ]).format(hmm_dir)
            self._logger.error(msg)
            raise RuntimeError(msg)
        # Lets check if all required files are there. Refer to:
        # http://cmusphinx.sourceforge.net/wiki/acousticmodelformat
        # for details
        missing_hmm_files = []
        for fname in ('mdef', 'feat.params', 'means', 'noisedict',
                      'transition_matrices', 'variances'):
            if not os.path.exists(os.path.join(hmm_dir, fname)):
                missing_hmm_files.append(fname)
        mixweights = os.path.exists(os.path.join(hmm_dir, 'mixture_weights'))
        sendump = os.path.exists(os.path.join(hmm_dir, 'sendump'))
        if not mixweights and not sendump:
            # We only need mixture_weights OR sendump
            missing_hmm_files.append('mixture_weights or sendump')
        if missing_hmm_files:
            self._logger.warning(
                " ".join([
                    "hmm_dir '%s' is missing files: %s.",
                    "Please make sure that you have set the correct",
                    "hmm_dir in your profile."
                ]).format(hmm_dir, ', '.join(missing_hmm_files))
            )
        self._pocketsphinx_v5 = hasattr(pocketsphinx.Decoder, 'default_config')

        with tempfile.NamedTemporaryFile(prefix='psdecoder_',
                                         suffix='.log', delete=False) as f:
            self._logfile = f.name

        if self._pocketsphinx_v5:
            # Pocketsphinx v5
            config = pocketsphinx.Decoder.default_config()
            config.set_string('-hmm', hmm_dir)
            config.set_string('-lm', lm_path)
            config.set_string('-dict', dict_path)
            config.set_string('-logfn', self._logfile)
            self._decoder = pocketsphinx.Decoder(config)
        else:
            # Pocketsphinx v4 or sooner
            self._decoder = pocketsphinx.Decoder(
                hmm=hmm_dir,
                logfn=self._logfile,
                lm=lm_path,
                dict=dict_path
            )

    def __del__(self):
        if self._logfile is not None:
            os.remove(self._logfile)

    def settings(self):
        # Get the defaults for settings
        # hmm_dir
        hmm_dir = profile.get(
            ['pocketsphinx', 'hmm_dir'],
            "/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k"
        )
        if(not hmm_dir):
            if(os.path.isdir(os.path.join(
                os.path.expanduser("~"),
                "pocketsphinx-python",
                "pocketsphinx",
                "model",
                "en-us",
                "en-us"
            ))):
                hmm_dir = os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx-python",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
                )
            elif(os.path.isdir(os.path.join(
                os.path.expanduser("~"),
                "pocketsphinx",
                "model",
                "en-us",
                "en-us"
            ))):
                hmm_dir = os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
                )
            elif(os.path.isdir(os.path.join(
                    "/",
                    "usr",
                    "share",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
            ))):
                hmm_dir = os.path.join(
                    "/",
                    "usr",
                    "share",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
                )
            else:
                hmm_dir = os.path.join(
                    "/usr",
                    "local",
                    "share",
                    "pocketsphinx",
                    "model",
                    "hmm",
                    "en_US",
                    "hub4wsj_sc_8k"
                )
        # fst_model
        fst_model = profile.get_profile_var(["pocketsphinx", "fst_model"])
        if not fst_model:
            if(os.path.isfile(os.path.join(
                os.path.expanduser("~"),
                "pocketsphinx-python",
                "pocketsphinx",
                "model",
                "en-us",
                "train",
                "model.fst"
            ))):
                fst_model = os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx-python",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "train",
                    "model.fst"
                )
            elif(os.path.isfile(os.path.join(
                os.path.expanduser("~"),
                "cmudict",
                "train",
                "model.fst"
            ))):
                fst_model = os.path.join(
                    os.path.expanduser("~"),
                    "cmudict",
                    "train",
                    "model.fst"
                )
            elif(os.path.isfile(os.path.join(
                os.path.expanduser("~"),
                "CMUDict",
                "train",
                "model.fst"
            ))):
                fst_model = os.path.join(
                    os.path.expanduser("~"),
                    "CMUDict",
                    "train",
                    "model.fst"
                )
            elif(os.path.isfile(os.path.join(
                os.path.expanduser("~"),
                "phonetisaurus",
                "g014b2b.fst"
            ))):
                fst_model = os.path.join(
                    os.path.expanduser("~"),
                    "phonetisaurus",
                    "g014b2b.fst"
                )
        phonetisaurus_executable = profile.get_profile_var(
            ['pocketsphinx', 'phonetisaurus_executable']
        )
        if(not phonetisaurus_executable):
            if(check_program_exists('phonetisaurus-g2pfst')):
                phonetisaurus_executable = 'phonetisaurus-g2pfst'
            else:
                phonetisaurus_executable = 'phonetisaurus-g2p'
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ('pocketsphinx', 'hmm_dir'), {
                        'title': _('PocketSphinx hmm file'),
                        'description': "".join([
                            _('PocketSphinx hidden markov model file')
                        ]),
                        'default': hmm_dir
                    }
                ),
                (
                    ('pocketsphinx', 'fst_model'), {
                        'title': _('PocketSphinx FST file'),
                        'description': "".join([
                            _('PocketSphinx finite state transducer file')
                        ]),
                        'default': hmm_dir
                    }
                ),
                (
                    ('pocketsphinx', 'phonetisaurus_executable'), {
                        'title': _('Phonetisaurus executable'),
                        'description': "".join([
                            _('Phonetisaurus is used to build custom dictionaries')
                        ]),
                        'default': phonetisaurus_executable
                    }
                ),
            ]
        )

    def transcribe(self, fp):
        """
        Performs STT, transcribing an audio file and returning the result.

        Arguments:
            fp -- a file object containing audio data
        """

        fp.seek(44)

        # FIXME: Can't use the Decoder.decode_raw() here, because
        # pocketsphinx segfaults with tempfile.SpooledTemporaryFile()
        data = fp.read()
        self._decoder.start_utt()
        self._decoder.process_raw(data, False, True)
        self._decoder.end_utt()

        if self._pocketsphinx_v5:
            hyp = self._decoder.hyp()
            result = hyp.hypstr if hyp is not None else ''
        else:
            result = self._decoder.get_hyp()[0]
        if self._logfile is not None:
            with open(self._logfile, 'r+') as f:
                for line in f:
                    self._logger.debug(line.strip())
                f.truncate()

        transcribed = [result] if result != '' else []
        self._logger.info('Transcribed: %r', transcribed)
        return transcribed
