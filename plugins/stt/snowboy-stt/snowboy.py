import snowboydetect
from jasper import plugin
from jasper import paths


class SnowboySTTPlugin(plugin.STTPlugin):
    """
    Hotword Detection which relies on Snowboy.

    Excerpt from sample profile.yml:

        ...
        snowboy-stt:
            model: Hello_Jasper.pmdl

    """

    def __init__(self, *args, **kwargs):
        plugin.STTPlugin.__init__(self, *args, **kwargs)

        self.resource_file = paths.PLUGIN_PATH + "/stt/snowboy-stt/common.res"
        self.model = self.profile['snowboy']['model']
        try:
            self.sensitivity = self.profile['snowboy']['sensitivity']
        except KeyError:
            self.sensitivity = "0.5"

        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=self.resource_file,
            model_str=self.model)
        self.detector.SetAudioGain(1)
        self.detector.SetSensitivity(self.sensitivity)

    def transcribe(self, fp):
        fp.seek(44)
        data = fp.read()

        ans = self.detector.RunDetection(data)

        if ans:
            return [self._vocabulary_phrases[-1]]
        else:
            return []
