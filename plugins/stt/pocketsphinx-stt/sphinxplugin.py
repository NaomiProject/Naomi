import importlib.util
import logging
import os
import platform
import tempfile
from collections import OrderedDict
from naomi import paths
from naomi import plugin
from naomi import profile
from naomi.run_command import run_command
from naomi.run_command import process_completedprocess
try:
    from . import sphinxvocab
    from .g2p import PhonetisaurusG2P
except ModuleNotFoundError:
    # Try to install phonetisaurus from pypi
    cmd = [
        'pip', 'install', 'phonetisaurus'
    ]
    completedprocess = run_command(cmd)
    if completedprocess.returncode != 0:
        # check what architecture we are on
        architecture = platform.machine()
        phonetisaurus_url = ""
        if architecture == "x86_64":
            wheel = "phonetisaurus-0.3.0-py3-none-manylinux1_x86_64.whl"
        elif architecture == "arm6l":
            wheel = "phonetisaurus-0.3.0-py3-none-linux_armv6l.whl"
        elif architecture == "arm7l":
            wheel = "phonetisaurus-0.3.0-py3-none-linux_armv7l.whl"
        elif architecture == "aarch64":
            wheel = "phonetisaurus-0.3.0-py3-none-linux_aarch64.whl"
        else:
            # Here we should probably build the package from source
            raise (f"Architecture {architecture} is not supported at this time")
        phonetisaurus_url = f"https://github.com/rhasspy/phonetisaurus-pypi/releases/download/v0.3.0/{wheel}"
        phonetisaurus_path = paths.sub('sources', wheel)
        cmd = [
            'curl', '-L', '-o', phonetisaurus_path, phonetisaurus_url
        ]
        completedprocess = run_command(cmd)
        if completedprocess.returncode != 0:
            raise Exception("Unable to download file from {phonetisaurus_url}")
        else:
            # use pip to install the file
            cmd = [
                'pip',
                'install',
                phonetisaurus_path
            ]
            completedprocess = run_command(cmd)
            if completedprocess.returncode == 0:
                # Check if phonetisaurus is intalled
                if importlib.util.find_spec("phonetisaurus"):
                    from . import sphinxvocab
                    from .g2p import PhonetisaurusG2P
                else:
                    raise Exception("Phonetisaurus install failed")
            else:
                raise Exception("Phonetisaurus install failed")
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
        if (os.path.isfile(os.path.join(location, program))):
            response = True
    return response


def check_pocketsphinx_model(directory):
    # Start by assuming the files exist. If any file is found to not
    # exist, then set this to False
    FilesExist = True
    if (not os.path.isfile(os.path.join(directory, "mdef"))):
        FilesExist = False
    if (not os.path.isfile(os.path.join(directory, "means"))):
        FilesExist = False
    if (not os.path.isfile(os.path.join(directory, "mixture_weights"))):
        FilesExist = False
    if (not os.path.isfile(os.path.join(directory, "sendump"))):
        FilesExist = False
    if (not os.path.isfile(os.path.join(directory, "variances"))):
        FilesExist = False
    if (not os.path.isfile(os.path.join(directory, "model", "train.fst"))):
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
        self._config = pocketsphinx.Config(
            hmm=hmm_dir,
            lm=lm_path,
            dict=dict_path
        )
        self._decoder = pocketsphinx.Decoder(self._config)

    def reinit(self):
        self._logger.debug(
            "Re-initializing PocketSphinx Decoder {self._vocabulary_name}"
        )
        # Pocketsphinx v5
        self._decoder.reinit(self._config)

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
        if (not hmm_dir):
            # Make a list of possible paths to check
            hmm_dir_paths = [
                paths.sub("pocketsphinx", "standard")
            ]
            # see if any of these paths exist
            for path in hmm_dir_paths:
                if os.path.isdir(path):
                    hmm_dir = path
        # If the hmm dir is missing, then download the standard model
        if not (hmm_dir and os.path.isdir(hmm_dir)):
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
            if (not check_pocketsphinx_model(hmm_dir)):
                # Check and see if we already have a copy of the standard
                # language model
                print(
                    _("Downloading and installing the {} pocketsphinx language model").format(language)
                )
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
                if completedprocess.returncode != 0:
                    raise Exception("Error downloading standard language model")
        # path to CMU dictionary
        cmudict_path = os.path.join(
            hmm_dir,
            "cmudict.dict"
        )
        # fst_model
        fst_model = os.path.join(hmm_dir, 'g2p_model.fst')
        if (not os.path.isfile(fst_model)):
            # Use phonetisaurus to prepare an fst model
            print("Training an FST model")
            PhonetisaurusG2P.train_fst(
                cmudict_path,
                fst_model
            )
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

        fp.seek(44, os.SEEK_SET)

        # FIXME: Can't use the Decoder.decode_raw() here, because
        # pocketsphinx segfaults with tempfile.SpooledTemporaryFile()
        data = fp.read()
        transcribed = []
        while True:
            try:
                self._decoder.start_utt()
                self._decoder.process_raw(data, False, True)
                self._decoder.end_utt()
                hyp = self._decoder.hyp()
                result = hyp.hypstr if hyp is not None else ''
                transcribed = [result] if result != '' else []
                self._logger.info('Transcribed: %r', transcribed)
                break
            except RuntimeError:
                self.reinit()

        if self._logfile is not None:
            with open(self._logfile, 'r+') as f:
                for line in f:
                    self._logger.debug(line.strip())
                    if self._logger.getEffectiveLevel() == logging.DEBUG:
                        print(line.strip())
                f.truncate()

        return transcribed
