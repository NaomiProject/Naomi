import pyowm
from jasper import plugin

class WeatherPlugin(plugin_Spee):
    def get_phrases(self):
        return [self.gettext("Weather")]
