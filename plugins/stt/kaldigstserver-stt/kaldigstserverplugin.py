import logging
import wave
import requests
from collections import OrderedDict
from naomi import i18n
from naomi import paths
from naomi import plugin
from naomi import profile


defaultKaldiServer = 'http://localhost:8888/client/dynamic/recognize'


class KaldiGstServerSTTPlugin(plugin.STTPlugin):
    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger(__name__)
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations, profile.get_profile())
        _ = translator.gettext

        plugin.STTPlugin.__init__(self, *args, **kwargs)

        self._http = requests.Session()

        self._url = profile.get(
            ['kaldigstserver-stt', 'url'],
            defaultKaldiServer
        )

    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ('kaldigstserver-stt', 'url'), {
                        'title': _('Kaldi server URL'),
                        'description': "".join([
                            _('The URL for your local Kaldi server')
                        ]),
                        'default': defaultKaldiServer
                    }
                )
            ]
        )

    def transcribe(self, fp):
        wav = wave.open(fp, 'rb')
        frame_rate = wav.getframerate()
        wav.close()
        data = fp.read()

        headers = {'Content-Type': 'audio/x-raw-int; rate=%s' % frame_rate}
        r = self._http.post(self._url, data=data, headers=headers)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            self._logger.critical('Request failed with http status %d',
                                  r.status_code)
            return []

        response = r.json()
        if not response['status'] == 0:
            if 'message' in response:
                msg = response['message']
            elif response['status'] == 1:
                msg = 'No speech found'
            elif response['status'] == 2:
                msg = 'Recognition aborted'
            elif response['status'] == 9:
                msg = 'All recognizer processes currently in use'
            else:
                msg = 'Unknown error'
            self._logger.critical('Transcription failed: %s', msg)
            return []

        results = []
        for hyp in response['hypotheses']:
            results.append(hyp['utterance'])

        self._logger.info('Transcribed: %r', results)
        return results
