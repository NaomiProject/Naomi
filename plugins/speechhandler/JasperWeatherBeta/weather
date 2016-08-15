import random
import pyowm
from jasper import plugin

#The next weather module for Jasper, based on the OpenWeatherMap API and the Pyowm project (https://github.com/csparpa/pyowm)

class JasperWeatherPlugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        return [
        self.gettext("WEATHER"),
        self.gettext("TODAY"),
        self.gettext("TOMORROW"),
        self.gettext("TEMPERATURE"),
        self.gettext("FORECAST"),
        self.gettext("YES"),
        self.gettext("NO")

    def handle(self, text, mic):
        """
        Responds to user-input, typically speech text, with a summary of
        the relevant weather for the requested date (typically, weather
        information will not be available for days beyond tomorrow).
        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """
        #Get information of the user: Location, Key, Unit, Language ...

        try:
            location = self.profile['OpenWeatherMap']['location']
            API_key = self.profile['OpenWeatherMap']['key']
        except KeyError:
            raise ValueError('Weather location not configured!')
        self._woeid = get_woeid(location)

        try:
            unit = self.profile['OpenWeatherMap']['unit']
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
        try:
            lang = self.profile['OpenWeatherMap']['Language']
        except KeyError:
            raise ValueError ('Language for JasperWeatherPlugin not configured!')

            for


        owm_key = pyowm.OWM(API_key)
        owm_language = pyowm.OWM('language' = lang)

        if self.gettext('TODAY') and self.gettext("WEATHER"):
            observation = owm.weather_at_place(location)
            w = observation.get_weather()
            mic.say("Today, the weather is", w)

        if self.gettext('TOMORROW') and self.gettext("WEATHER")

            obse
