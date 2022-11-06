# -*- coding: utf-8 -*-
from collections import OrderedDict
from naomi import plugin
from naomi import profile


class default_sr(plugin.SRPlugin):
    def settings(self):
        return OrderedDict(
            [
                (
                    ('first_name',), {
                        'title': self.gettext('Please tell me your name'),
                        'description': self.gettext('This is how I will refer to you. You may leave it blank')
                    }
                )
            ]
        )

    # Takes the name of the file containing the audio to be identified
    # Returns the name of the speaker, the cosine distance, and the STT transcription
    def recognize_speaker(self, fp, stt_engine):
        utterance = [word.upper() for word in stt_engine.transcribe(fp)]
        return {
            'speaker': profile.get(['first_name'], ''),
            'confidence': 0,
            'utterance': utterance
        }
