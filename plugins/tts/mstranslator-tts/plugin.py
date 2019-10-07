import requests
import unittest
from naomi import plugin
from naomi import profile
try:
    import mstranslator
except ImportError:
    raise unittest.SkipTest('Skipping mstranslator, "mstranslator" module not found')


class MicrosoftTranslatorTTSPlugin(plugin.TTSPlugin):
    """
    Uses the Microsoft Translator API.
    See http://www.microsoft.com/en-us/translator/getstarted.aspx.
    """

    def __init__(self, *args, **kwargs):
        plugin.TTSPlugin.__init__(self, *args, **kwargs)

        client_id = profile.get(['mstranslator-tts', 'client_id'])
        if not client_id:
            raise ValueError('Microsoft Translator client ID not configured!')

        client_secret = profile.get(['mstranslator-tts', 'client_secret'])
        if not client_secret:
            raise ValueError(
                'Microsoft Translator client secret not configured!'
            )

        language = profile.get(['language'], 'en-US')

        self._mstranslator = mstranslator.Translator(client_id, client_secret)

        available_languages = self._mstranslator.get_langs(speakable=True)
        for lang in (language.lower(), language.lower().split('-')[0]):
            if lang in available_languages:
                self._language = lang
                break
        else:
            raise ValueError("Language '%s' not supported" % language)

        best_quality = profile.get(['mstranslator-tts']['best_quality'])

        self._kwargs = {
            'format': 'audio/wav',
            'best_quality': best_quality
        }

    def say(self, phrase):
        """ Method used to utter words using the MS Translator TTS plugin """
        url = self._mstranslator.speak(phrase, self._language, **self._kwargs)
        r = requests.get(url)
        return r.content
