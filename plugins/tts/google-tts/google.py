import os
import logging
from collections import OrderedDict
from naomi import plugin
from naomi import profile

from google.cloud import texttospeech


class GoogleTTSPlugin(plugin.TTSPlugin):
    """
    Uses the Google TTS python API

    https://cloud.google.com/text-to-speech/docs/reference/rpc/google.cloud.texttospeech.v1beta1#audioencoding

    """

    settings = OrderedDict(
                [(
                ("google", "authentication_json"), {
                     "type": "file",
                     "title": "Google application credentials (*.json)",
                     "description": "This is a json file that allows your assistant to use the Google Speech API for converting speech to text. You need to generate and download an google cloud API key. Details here: https://cloud.google.com/speech-to-text/docs/quickstart-protocol",                                                                                                                                                
                     "validation": lambda filename: os.path.exists(os.path.expanduser(filename)),
                     "invalidmsg": "File {} does not exist".format,
                     "default": os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                    }
                 )]
                )


    def __init__(self, *args, **kwargs):
        plugin.TTSPlugin.__init__(self, *args, **kwargs)

        self._logger = logging.getLogger(__name__)

        self.language = profile.get_profile_var(['language'], 'en-US')
        self.client   = texttospeech.TextToSpeechClient()
        # Build the voice request, select the language code and 
        # voice gender ("neutral")
        self.voice =    texttospeech.types.VoiceSelectionParams(
                        language_code=self.language,
                        ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)
        # Select the type of audio file you want returned
        self.audio_config = texttospeech.types.AudioConfig(
                            audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)

    def say(self, phrase):

        # Set the text input to be synthesized
        synthesis_input = texttospeech.types.SynthesisInput(text=phrase)

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = self.client.synthesize_speech(synthesis_input, 
                                                self.voice, 
                                                self.audio_config
                                                )
        return response.audio_content
