import re
import pyowm
from semantic.numbers import NumberService

from jasper import plugin

class OpenWeatherPlugin(plugin.SpeechHandlerPlugin):
    def __init__(self, *args, **kwargs):
        super(WeatherPlugin, self).__init__(*args, **kwargs)
        try:
            self._woeid = self.profile['weather']['woeid']
        except KeyError:
            try:
                location = self.profile['weather']['location']
            except KeyError:
                raise ValueError('Weather location not configured!')
            self._woeid = get_woeid(location)

        if not self._woeid:
            raise ValueError('Weather location (woeid) invalid!')

        try:
            unit = self.profile['weather']['unit']
        except KeyError:
            self._unit = 'f'
        else:
            unit = unit.lower()
            if unit == 'c' or unit == 'celsius':
                self._unit = 'c'
            elif unit == 'f' or unit == 'fahrenheit':
                self._unit = 'f'
            else:
                raise ValueError('Invalid unit!')

    def get_phrases(self):
        return [
            self.gettext("WEATHER"),
            self.gettext("TODAY"),
            self.gettext("TOMORROW"),
            self.gettext("TEMPERATURE"),
            self.gettext("FORECAST"),
            self.gettext("YES"),
            self.gettext("NO")]
