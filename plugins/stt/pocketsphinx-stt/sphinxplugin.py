import os.path
import re
import tempfile
from collections import OrderedDict
from naomi import paths
from naomi import plugin
from naomi import profile
from naomi.run_command import run_command
from naomi.run_command import process_completedprocess
from . import sphinxvocab
from .g2p import PhonetisaurusG2P
from pocketsphinx import pocketsphinx


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


def check_pocketsphinx_model(directory):
    # Start by assuming the files exist. If any file is found to not
    # exist, then set this to False
    FilesExist = True
    mdef_file = os.path.join(directory, "mdef")
    mdef_text_file = os.path.join(directory, "mdef.txt")
    if(not os.path.isfile(mdef_text_file)):
        print(f"{mdef_text_file} does not exist. Creating.")
        if(os.path.isfile(mdef_file)):
            command = [
                "pocketsphinx_mdef_convert",
                "-text",
                mdef_file,
                mdef_text_file
            ]
            completedprocess = run_command(command)
            print("Command {} returned {}".format(
                " ".join(completedprocess.args),
                completedprocess.returncode
            ))
        if(not os.path.isfile(mdef_text_file)):
            print(f"{mdef_text_file} still does not exist")
            FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "means"))):
        print(f"means does not exist")
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "mixture_weights"))):
        print(f"mixture_weights does not exist")
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "sendump"))):
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "variances"))):
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "model", "train.fst"))):
        FilesExist = False
    return FilesExist


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

        print("initializing Pocketsphinx plugin")
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

        with tempfile.NamedTemporaryFile(
            prefix='psdecoder_',
            suffix='.log',
            delete=False
        ) as f:
            self._logfile = f.name

        # Pocketsphinx v5
        config = pocketsphinx.Config()
        config.set_string('-hmm', hmm_dir)
        config.set_string('-lm', lm_path)
        config.set_string('-dict', dict_path)
        config.set_string('-logfn', self._logfile)
        self._decoder = pocketsphinx.Decoder(config)

    def __del__(self):
        if self._logfile is not None:
            os.remove(self._logfile)

    def settings(self):
        language = profile.get(['language'])
        _ = self.gettext
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
        # If either the hmm dir or fst model is missing, then
        # download the standard model
        if not(hmm_dir and os.path.isdir(hmm_dir) and fst_model and os.path.isfile(fst_model)):
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
            fst_model = os.path.join(hmm_dir, "train", "model.fst")
            cmudict_path = os.path.join(
                hmm_dir,
                "cmudict.dict"
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
            if(not os.path.isfile(fst_model)):
                # Use phonetisaurus to prepare an fst model
                print("Training an FST model")
                PhonetisaurusG2P.train_fst(cmudict_path, os.path.join(hmm_dir, fst_model))
        kenlm_dir = profile.get(
            ['pocketsphinx', 'kenlm_dir'],
            paths.sub('kenlm')
        )
        if not os.path.isdir(kenlm_dir):
            print("Downloading KenLM")
            cmd = [
                'git',
                'clone',
                'https://github.com/kpu/kenlm.git',
                kenlm_dir
            ]
            completedprocess = run_command(cmd)
            self._logger.info(process_completedprocess(completedprocess))
        kenlm_build = os.path.join(
            kenlm_dir,
            'build'
        )
        kenlm_lmplz = os.path.join(
            kenlm_build,
            'bin',
            'lmplz'
        )
        if not os.path.isfile(kenlm_lmplz):
            if not os.path.isdir(kenlm_build):
                os.mkdir(kenlm_build)
        if not os.path.isfile(kenlm_lmplz):
            print("Compiling kenlm")
            cmd = [
                'cmake',
                '..'
            ]
            completedprocess = run_command(cmd, cwd=kenlm_build)
            self._logger.info(process_completedprocess(completedprocess))
            cmd = [
                'make'
            ]
            completedprocess = run_command(cmd, cwd=kenlm_build)
            self._logger.info(process_completedprocess(completedprocess))
        return OrderedDict(
            [
                (
                    ('pocketsphinx', 'hmm_dir'), {
                        'title': _('PocketSphinx hmm file'),
                        'description': "".join([
                            _('PocketSphinx hidden markov model directory')
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
                    ('kenlm', 'source_dir'), {
                        'title': _('KenLM source directory'),
                        'description': _('Location of the KenLM source'),
                        'default': kenlm_dir
                    }
                )
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
