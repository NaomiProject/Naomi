import os
import logging
import unittest
from collections import OrderedDict
from naomi import plugin
from naomi import profile
try:
    from google.cloud import texttospeech
except ImportError:
    raise unittest.SkipTest("Skipping Google-TTS, module 'google.cloud' not found")
try:
    from google.oauth2 import service_account
except ImportError:
    raise unittest.SkipTest("Skipping Google-TTS, module 'google.oauth2' not found")


google_env_var = "GOOGLE_APPLICATION_CREDENTIALS"


class GoogleTTSPlugin(plugin.TTSPlugin):
    """
    Uses the Google TTS python API

    https://cloud.google.com/text-to-speech/docs/reference/rpc/google.cloud.texttospeech.v1beta1#audioencoding

    """

    def __init__(self, *args, **kwargs):
        plugin.TTSPlugin.__init__(self, *args, **kwargs)

        self._logger = logging.getLogger(__name__)

        self.language = profile.get_profile_var(['language'], 'en-US')

        if(google_env_var in os.environ):
            self.client = texttospeech.TextToSpeechClient()
        else:
            credentials_json = profile.get_profile_var(
                ["google", "credentials_json"]
            )
            cred = service_account.Credentials.from_service_account_file(
                credentials_json
            )
            self.client = texttospeech.TextToSpeechClient(credentials=cred)
        # Build the voice request, select the language code and
        # voice gender ("neutral")
        self.voice = texttospeech.types.VoiceSelectionParams(
            language_code=self.language,
            ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL
        )
        # Select the type of audio file you want returned
        self.audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16
        )

    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [(
                ("google", "credentials_json"), {
                    "type": "file",
                    "title": "Google application credentials (*.json)",
                    "description": "This is a json file that allows your assistant to use the Google Speech API for converting speech to text. You need to generate and download an google cloud API key. Details here: https://cloud.google.com/speech-to-text/docs/quickstart-protocol",
                    "validation": lambda filename: os.path.exists(os.path.expanduser(filename)),
                    "invalidmsg": "File {} does not exist".format,
                    "default": os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                }
            )]
        )

    def say(self, phrase):
        # Set the text input to be synthesized
        synthesis_input = texttospeech.types.SynthesisInput(text=phrase)

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = self.client.synthesize_speech(
            synthesis_input,
            self.voice,
            self.audio_config
        )
        return response.audio_content
