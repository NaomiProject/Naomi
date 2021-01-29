import logging
import urllib
import requests
from naomi import plugin
from naomi import profile


class MaryTTSPlugin(plugin.TTSPlugin):
    """
    Uses the MARY Text-to-Speech System (MaryTTS)
    MaryTTS is an open-source, multilingual Text-to-Speech Synthesis platform
    written in Java.
    Please specify your own server instead of using the demonstration server
    (http://mary.dfki.de:59125/) to save bandwidth and to protect your privacy.
    """

    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger(__name__)

        plugin.TTSPlugin.__init__(self, *args, **kwargs)

        self.server = profile.get(
            ['mary-tts', 'server'],
            'marytts.phonetik.uni-muenchen.de'
        )

        try:
            port = int(profile.get(['mary-tts', 'port']))
        except(TypeError, ValueError):
            port = 59125
        self.port = port

        self.netloc = '{server}:{port}'.format(
            server=self.server,
            port=self.port
        )
        self.session = requests.Session()

        available_voices = self.get_voices()

        orig_language = profile.get(['language'], 'en-US')

        language = orig_language.replace('-', '_')
        if language not in available_voices:
            language = language.split('_')[0]
        if language not in available_voices:
            raise ValueError(
                "Language '{}' ('{}') not supported".format(
                    language,
                    orig_language
                )
            )
        self.language = language

        self._logger.info('Available voices: %s', ', '.join(
            available_voices[language]))

        voice = profile.get(['mary-tts', 'voice'])

        if voice is not None and voice in available_voices[language]:
            self.voice = voice
        else:
            self.voice = available_voices[language][0]
            if voice is not None:
                self._logger.info(
                    "Voice '{}' not found, using '{}' instead.".format(
                        voice,
                        self.voice
                    )
                )

    def get_voices(self):
        voices = {}
        try:
            r = self.session.get(self._makeurl('/voices'))
            r.raise_for_status()
        except requests.exceptions.RequestException:
            self._logger.critical(
                "Communication with MaryTTS server at {} failed.".format(
                    self.netloc
                )
            )
            raise
        for line in r.text.splitlines():
            parts = line.strip().split()
            if len(parts) > 2:
                name = parts[0]
                lang = parts[1]
                if lang not in voices:
                    voices[lang] = []
                voices[lang].append(name)
        return voices

    def _makeurl(self, path, query={}):
        query_s = urllib.parse.urlencode(query)
        urlparts = ('http', self.netloc, path, query_s, '')
        return urllib.parse.urlunsplit(urlparts)

    def say(self, phrase):
        query = {'OUTPUT_TYPE': 'AUDIO',
                 'AUDIO': 'WAVE_FILE',
                 'INPUT_TYPE': 'TEXT',
                 'INPUT_TEXT': phrase.encode('utf8'),
                 'LOCALE': self.language,
                 'VOICE': self.voice}

        r = self.session.get(self._makeurl('/process', query=query))
        return r.content
