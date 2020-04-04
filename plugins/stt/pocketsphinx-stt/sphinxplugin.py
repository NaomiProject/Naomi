import os.path
<<<<<<< HEAD
=======
import re
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
import tempfile
from collections import OrderedDict
from naomi import paths
from naomi import plugin
from naomi import profile
<<<<<<< HEAD
=======
from naomi.run_command import run_command
from naomi.run_command import process_completedprocess
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
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


<<<<<<< HEAD
=======
def check_pocketsphinx_model(directory):
    # Start by assuming the files exist. If any file is found to not
    # exist, then set this to False
    FilesExist = True
    if(not os.path.isfile(os.path.join(directory, "mdef.txt"))):
        if(os.path.isfile(os.path.join(directory, "mdef"))):
            command = [
                "pocketsphinx_mdef_convert",
                "-text",
                os.path.join(directory, "mdef"),
                os.path.join(directory, "mdef.txt")
            ]
            completedprocess = run_command(command)
            print("Command {} returned {}".format(
                " ".join(completedprocess.args),
                completedprocess.returncode
            ))
        if(not os.path.isfile(os.path.join(directory, "mdef.txt"))):
            FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "means"))):
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "mixture_weights"))):
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "sendump"))):
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "variances"))):
        FilesExist = False
    return FilesExist


>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
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
            sphinxvocab.compile_vocabulary
        )

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
            ['pocketsphinx', 'hmm_dir']
        )
        if(not hmm_dir):
            # Make a list of possible paths to check
            hmm_dir_paths = [
                os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx-python",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
                ),
                os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
                ),
                os.path.join(
                    "/",
                    "usr",
                    "share",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "en-us"
                ),
                os.path.join(
                    "/usr",
                    "local",
                    "share",
                    "pocketsphinx",
                    "model",
                    "hmm",
                    "en_US",
                    "hub4wsj_sc_8k"
                )
            ]
            # see if any of these paths exist
            for path in hmm_dir_paths:
                if os.path.isdir(path):
                    hmm_dir = path
        # fst_model
        fst_model = profile.get_profile_var(["pocketsphinx", "fst_model"])
        if not fst_model:
            # Make a list of possible paths to check
            fst_model_paths = [
                os.path.join(
                    paths.sub(
                        os.path.join(
                            "pocketsphinx",
                            "adapt",
                            "en-US",
                            "train",
                            "model.fst"
                        )
                    )
                ),
                os.path.join(
                    os.path.expanduser("~"),
                    "pocketsphinx-python",
                    "pocketsphinx",
                    "model",
                    "en-us",
                    "train",
                    "model.fst"
                ),
                os.path.join(
                    os.path.expanduser("~"),
                    "cmudict",
                    "train",
                    "model.fst"
                ),
                os.path.join(
                    os.path.expanduser("~"),
                    "CMUDict",
                    "train",
                    "model.fst"
                ),
                os.path.join(
                    os.path.expanduser("~"),
                    "phonetisaurus",
                    "g014b2b.fst"
                )
            ]
            for path in fst_model_paths:
                if os.path.isfile(path):
                    fst_model = path
<<<<<<< HEAD
=======
        # If either the hmm dir or fst model is missing, then
        # download the standard model
        if not(hmm_dir and fst_model):
            # Start by checking to see if we have a copy of the standard
            # model for this user's chosen language and download it if not.
            # Check for the files we need
            language = profile.get_profile_var(['language'])
            base_working_dir = paths.sub("pocketsphinx")
            if not os.path.isdir(base_working_dir):
                os.mkdir(base_working_dir)
            standard_dir = os.path.join(base_working_dir, "standard")
            if not os.path.isdir(standard_dir):
                os.mkdir(standard_dir)
            standard_dir = os.path.join(standard_dir, language)
            if not os.path.isdir(standard_dir):
                os.mkdir(standard_dir)
            hmm_dir = standard_dir
            formatteddict_path = os.path.join(
                hmm_dir,
                "cmudict.formatted.dict"
            )
            if(not check_pocketsphinx_model(hmm_dir)):
                # Check and see if we already have a copy of the standard
                # language model
                print("Downloading and installing the {} pocketsphinx language model".format(language))
                cmd = [
                    'git',
                    'clone',
                    '-b',
                    language,
                    'https://github.com/NaomiProject/CMUSphinx_standard_language_models.git',
                    hmm_dir
                ]
                completedprocess = run_command(cmd)
                self._logger.info(process_completedprocess(completedprocess))

                print("Formatting the g2p dictionary")
                with open(os.path.join(standard_dir, "cmudict.dict"), "r") as in_file:
                    with open(formatteddict_path, "w+") as out_file:
                        for line in in_file:
                            # Remove whitespace at beginning and end
                            line = line.strip()
                            # remove the number in parentheses (if there is one)
                            line = re.sub('([^\\(]+)\\(\\d+\\)', '\\1', line)
                            # compress all multiple whitespaces into a single whitespace
                            line = re.sub('\s+', ' ', line)
                            # replace the first whitespace with a tab
                            line = line.replace(' ', '\t', 1)
                            print(line, file=out_file)
                # Use phonetisaurus to prepare an fst model
                print("Training an FST model")
                cmd = [
                    "phonetisaurus-train",
                    "--lexicon", formatteddict_path,
                    "--seq2_del",
                    "--dir_prefix", os.path.join(hmm_dir, "train")
                ]
                completedprocess = run_command(cmd)
                self._logger.info(process_completedprocess(completedprocess))
                fst_model = os.path.join(hmm_dir, "train", "model.fst")

>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
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
<<<<<<< HEAD
                            _('PocketSphinx hidden markov model file')
=======
                            _('PocketSphinx hidden markov model directory')
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
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
                        'default': fst_model
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
