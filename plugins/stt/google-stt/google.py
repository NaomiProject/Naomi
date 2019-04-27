import logging
from naomi import plugin

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from google.api_core.exceptions import GoogleAPICallError,RetryError


class GoogleSTTPlugin(plugin.STTPlugin):
    """
    Speech-To-Text implementation using the Google Speech API.
    Uses the google python client:
    https://googleapis.github.io/google-cloud-python/latest/speech/index.html

    You need to download an google cloud API key and set its location using the 
    environment variable GOOGLE_APPLICATION_CREDENTIALS. Details here:

    https://cloud.google.com/speech-to-text/docs/quickstart-protocol

    """

    def __init__(self, *args, **kwargs):
        plugin.STTPlugin.__init__(self, *args, **kwargs)
        # FIXME: get init args from config

        self._logger = logging.getLogger(__name__)
        self._language = None
        self._client = speech.SpeechClient()
        self._config = None
        try:
            language = self.profile['language']
        except KeyError:
            language = 'en-US'

        self.language = language.lower()

        self._regenerate_config()


    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value):
        self._language = value
        self._regenerate_config()

    def _regenerate_config(self):
        keyword = None
        try:
            keyword = self.profile["keyword"]
        except:
            pass

        self._config = types.RecognitionConfig(
                           encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                           language_code=self.language,
                           speech_contexts=[speech.types.SpeechContext(phrases=[keyword])],
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
            results = [ str(result.alternatives[0].transcript).upper() for 
                            result in response.results]
            self._logger.info('Transcribed: %r', results)

        return results

