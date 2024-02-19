# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict

import json
import requests
from naomi import plugin
from naomi import profile


# There's a list of supported languages, see Wit.ai FAQ : https://wit.ai/faq
# Last updated: February 09, 2024
SUPPORTED_LANG = (
    'ar',
    'bn',
    'my',
    'zh',
    'nl',
    'en',
    'fi',
    'fr',
    'de',
    'hi',
    'id',
    'it',
    'ja',
    'kn',
    'ko',
    'ms',
    'ml',
    'mr',
    'pl',
    'pt',
    'ru',
    'si',
    'es',
    'sv',
    'tl',
    'ta',
    'th',
    'tr',
    'ur',
    'vi'
)


class WitAiSTTPlugin(plugin.STTPlugin):
    """
    Speech-To-Text implementation which relies on the Wit.ai Speech API.

    This implementation requires an Wit.ai Access Token to be present in
    profile.yml. Please sign up at https://wit.ai and copy your instance
    token, which can be found under Settings in the Wit console to your
    profile.yml:
        ...
        stt_engine: witai-stt
        witai-stt:
          access_token:    INSERT_YOUR_TOKEN_HERE
    """

    def __init__(self, *args, **kwargs):
        """
        Create Plugin Instance
        """
        plugin.STTPlugin.__init__(self, *args, **kwargs)
        self._language = None
        self._logger = logging.getLogger(__name__)
        self.token = profile.get(['witai-stt', 'access_token'])

        language = profile.get(['language'], 'en-US')
        format_language = language.split('-')[0]
        if language.split('-')[0] not in SUPPORTED_LANG:
            raise ValueError(
                f'Language {format_language} is not supported.'
            )

    def settings(self):
        """
        Define required settings for this plugin
        """
        _ = self.gettext
        return OrderedDict(
            {
                ("witai-stt", "access_token"): {
                    "title": _("Wit.ai access token"),
                    "description": _("Your access token from https://wit.ai/")
                }
            }
        )

    @property
    def token(self):
        """
        Return defined acess token.
        """
        return self._token

    @property
    def language(self):
        """
        Returns selected language
        """
        return self._language

    @token.setter
    def token(self, value):
        """
        Sets property token
        """
        self._token = value
        self._headers = {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'audio/wav'
        }

    @property
    def headers(self):
        """
        Return headers
        """
        return self._headers

    def transcribe(self, fp):
        """
        transcribes given audio file by uploading to wit.ai and returning
        received text from json answer.
        """
        data = fp.read()
        r = requests.post(
            'https://api.wit.ai/speech?v=20230215',
            data=data,
            headers=self.headers,
            stream=True,  # receive chunked http data
        )
        try:
            r.raise_for_status()

            *_, data = r.iter_content(chunk_size=None)  # get last chunk of data
            text = json.loads(data.decode('utf-8'))["text"]

        except requests.exceptions.HTTPError:
            self._logger.critical('Request failed with response: %r',
                                  r.text,
                                  exc_info=True)
            return []
        except requests.exceptions.RequestException:
            self._logger.critical('Request failed.', exc_info=True)
            return []
        except ValueError as e:
            self._logger.critical('Cannot parse response: %s',
                                  e.args[0])
            return []
        except KeyError:
            self._logger.critical('Cannot parse response.',
                                  exc_info=True)
            return []
        transcribed = [text.upper()]
        self._logger.info('Transcribed: %r', transcribed)
        return transcribed
