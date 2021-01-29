import logging
import os
import unittest
from collections import OrderedDict
from naomi import plugin
from naomi import profile
try:
    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types
    from google.api_core.exceptions import GoogleAPICallError, RetryError
    from google.oauth2 import service_account
except ImportError:
    raise unittest.SkipTest("google module not installed")

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

    def __init__(self, *args, **kwargs):
        plugin.STTPlugin.__init__(self, *args, **kwargs)
        # FIXME: get init args from config

        if(google_env_var in os.environ):
            self._client = speech.SpeechClient()
        else:
            credentials_json = profile.get_profile_var(["google", "credentials_json"])
            cred = service_account.Credentials.from_service_account_file(credentials_json)
            self._client = speech.SpeechClient(credentials=cred)
        self._regenerate_config()

    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ("google", "credentials_json"), {
                        "type": "file",
                        "title": _("Google application credentials (*.json)"),
                        "description": _("This is a json file that allows your assistant to use the Google Speech API for converting speech to text. You need to generate and download an google cloud API key. Details here: https://cloud.google.com/speech-to-text/docs/quickstart-protocol"),
                        "validation": lambda filename: os.path.exists(os.path.expanduser(filename)),
                        "invalidmsg": lambda filename: _("File {} does not exist".format(os.path.expanduser(filename))),
                        "default": os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                    }
                )
            ]
        )

    def _regenerate_config(self):
        phrases = []
        phrases.extend(profile.get_profile_var(["keyword"], "Naomi"))

        self._config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=profile.get(['language'], 'en-US'),
            speech_contexts=[
                speech.types.SpeechContext(
                    phrases=phrases
                )
            ] if len(phrases) else None,
            model="command_and_search"
        )

    def transcribe(self, fp):
        """
        Performs STT via the Google Speech API, transcribing an audio file and
        returning an English string.

        Arguments:
        fp -- the path to the .wav file to be transcribed
        """
        content = fp.read()
        audio = types.RecognitionAudio(content=content)
        try:
            response = self._client.recognize(self._config, audio)
        except GoogleAPICallError as e:
            # request failed for any reason
            error_message = 'Google STT API call error. response: {}'.format(
                e.args[0]
            )
            if(self._logger.getEffectiveLevel() > logging.WARN):
                print(error_message)
            self._logger.warning(error_message)
            results = []
        except RetryError as e:
            # failed due to a retryable error and retry attempts failed
            error_message = 'Google STT retry error. response: {}'.format(
                e.args[0]
            )
            if(self._logger.getEffectiveLevel() > logging.WARN):
                print(error_message)
            self._logger.warning(error_message)
            results = []
        except ValueError as e:
            error_message = 'Empty response: {}'.format(e.args[0])
            if(self._logger.getEffectiveLevel() > logging.WARN):
                print(error_message)
            self._logger.warning(error_message)
            results = []
        else:
            # Convert all results to uppercase
            results = [
                str(result.alternatives[0].transcript).upper()
                for result in response.results
            ]
            self._logger.info('Transcribed: %r', results)

        return results
