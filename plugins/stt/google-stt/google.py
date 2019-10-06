import logging
from collections import OrderedDict
from naomi import plugin
from naomi import profile
import os

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from google.api_core.exceptions import GoogleAPICallError, RetryError

from google.oauth2 import service_account


google_env_var = "GOOGLE_APPLICATION_CREDENTIALS"


class GoogleSTTPlugin(plugin.STTPlugin):
    """
    Speech-To-Text implementation using the Google Speech API.
    Uses the google python client:
    https://googleapis.github.io/google-cloud-python/latest/speech/index.html

    You need to download an google cloud API key and set its location using the
    environment variable GOOGLE_APPLICATION_CREDENTIALS. Details here:

    https://cloud.google.com/speech-to-text/docs/quickstart-protocol

    The python api for google stt is documented here:
    https://googleapis.github.io/google-cloud-python/latest/speech/index.html

    """

    settings = OrderedDict(
        [
            (
                ("google", "credentials_json"), {
                    "type": "file",
                    "title": "Google application credentials (*.json)",
                    "description": "This is a json file that allows your assistant to use the Google Speech API for converting speech to text. You need to generate and download an google cloud API key. Details here: https://cloud.google.com/speech-to-text/docs/quickstart-protocol",
                    "validation": lambda filename: os.path.exists(os.path.expanduser(filename)),
                    "invalidmsg": "File {} does not exist".format,
                    "default": os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                }
            )
        ]
    )

    def __init__(self, *args, **kwargs):
        plugin.STTPlugin.__init__(self, *args, **kwargs)
        # FIXME: get init args from config

        self._logger = logging.getLogger(__name__)
        self._language = profile.get_profile_var(['language'], 'en-US')
        self._config = None

        if(google_env_var in os.environ):
            self._client = speech.SpeechClient()
        else:
            credentials_json = profile.get_profile_var(["google", "credentials_json"])
            cred = service_account.Credentials.from_service_account_file(credentials_json)
            self._client = speech.SpeechClient(credentials=cred)
        self._regenerate_config()

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value):
        self._language = value.lower()
        self._regenerate_config()

    def _regenerate_config(self):
        keyword = profile.get_profile_var(["keyword"], "Naomi")

        self._config = types.RecognitionConfig(
                           encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                           language_code=self.language,
                           speech_contexts=[speech.types.SpeechContext(phrases=[keyword])] if keyword else None,
                           model="command_and_search"
                       )

    def transcribe(self, fp):
        """
        Performs STT via the Google Speech API, transcribing an audio file and
        returning an English string.

        Arguments:
        fp -- the path to the .wav file to be transcribed
        """
        if not self.language:
            self._logger.critical('Language info missing, transcription ' +
                                  'request aborted.')
            return []

        content = fp.read()
        audio = types.RecognitionAudio(content=content)
        try:
            response = self._client.recognize(self._config, audio)
        except GoogleAPICallError as e:
            # request failed for any reason
            self._logger.warning('Google STT retry error. response: %s', e.args[0])
            results = []
        except RetryError as e:
            # failed due to a retryable error and retry attempts failed
            self._logger.warning('Google STT retry error. response: %s', e.args[0])
            results = []
        except ValueError as e:
            self._logger.warning('Empty response: %s', e.args[0])
            results = []
        else:
            # Convert all results to uppercase
            results = [str(result.alternatives[0].transcript).upper() for
                            result in response.results]
            self._logger.info('Transcribed: %r', results)

        return results
