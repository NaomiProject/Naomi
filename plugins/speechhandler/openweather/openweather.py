import re
import pyowm
from semantic.numbers import NumberService

from jasper import plugin

def getWeatherReport(weather,loc,temp_unit='celsius',report='current'):
        weather_report = 'Server Down.'
        wind = weather.get_wind()
        wind_speed = serviceNum.parseMagnitude(wind["speed"])
        humi = serviceNum.parseMagnitude(weather.get_humidity())
        clou = serviceNum.parseMagnitude(weather.get_clouds())
        stat = weather.get_status()
        detstat = weather.get_detailed_status()

        if report == 'current':
            temp = weather.get_temperature(temp_unit)
            temp_max = serviceNum.parseMagnitude(temp['temp_max'])
            temp_min = serviceNum.parseMagnitude(temp['temp_min'])
            curr_temp = serviceNum.parseMagnitude(temp['temp'])
            weather_report = self.gettext("Weather at {loc}. Today is {stat}. There is a chance of   \
                              {detstat}. Now Temperature is {curr_temp} degree   \
                              {temp_unit}. Humidity {humi} percent. Wind Speed   \
                              {wind_speed}. with cloud cover {clou} percent.").format(
                              loc = loc,
                              stat = stat,
                              detstat = detstat,
                              curr_temp = curr_temp,
                              temp_unit = temp_unit,
                              humi = humi,
                              wind_speed = wind_speed,
                              clou = clou)

        elif report == 'tommorow':
            temp = weather.get_temperature(temp_unit)
            temp_morn = serviceNum.parseMagnitude(temp['morn'])
            temp_day = serviceNum.parseMagnitude(temp['day'])
            temp_night = serviceNum.parseMagnitude(temp['night'])
            weather_report = self.gettext("Weather at {loc}. Tomorrow will be {stat}. There will be a chance of   \
                              {detstat}. Temperature in the morning {temp_morn} degree   \
                              {temp_unit}. Days Temperature will be {temp_day} degree   \
                              {temp_unit}. and Temperature at night will be {temp_night} degree   \
                              {temp_unit}. Humidity {humi} percent. Wind Speed   \
                              +wind_speed}. with clouds cover {clou} percent.").format(
                              loc = loc,
                              stat = stat,
                              detstat = detstat,
                              temp_morn = temp_morn,
                              temp_day = temp_day,
                              temp_night = temp_night
                              temp_unit = temp_unit,
                              humi = humi,
                              wind_speed = wind_speed,
                              clou = clou)





        return weather_report







class OpenWeatherPlugin(plugin.SpeechHandlerPlugin):
    def __init__(self, *args, **kwargs):
        super(WeatherPlugin, self).__init__(*args, **kwargs)
        try:
            city_name = self.profile['weather']['city_name']
            country = self.profile['Weather']['country']

            except KeyError:
                raise ValueError('Weather location not configured.')

        try:
            temp_unit = self.profile['weather']['unit']
        except KeyError:
            self._unit = 'f'
        else:
            temp_unit = temp_unit.lower()
            if temp_unit == 'c' or temp_unit == 'celsius':
                self._unit = 'c'
            elif temp_unit == 'f' or temp_unit == 'fahrenheit':
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

    def get_priority(self):
        return 4

    def handle(self, text, mic):

        if self.gettext('CURRENT').upper() || self.gettext('TODAYS').upper() || self.gettext('TODAY').upper() in text.upper():
            cw = owm.weather_at_place(city_name+","+country)
            loc = cw.get_location().get_name()
            weather = cw.get_weather()
            weather_report = getWeatherReport(weather,loc,temp_unit,report='current')
            mic.say(weather_report)

        elif self.gettext('TOMORROWS').upper() || self.gettext('TOMORROW').upper() in text.upper():
            forecast = owm.daily_forecast(city_name)
            fore = forecast.get_forecast()
            loc = fore.get_location().get_name()
            tomorrow = pyowm.timeutils.tomorrow()
            weather = forecast.get_weather_at(tomorrow)
            weather_report = getWeatherReport(weather,loc,temp_unit,report='tommorow')
            mic.say(weather_report)

        elif
            forecast = owm.daily_forecast(city_name)
            fore = forecast.get_forecast()
            loc = fore.get_location().get_name()
            weather_report = getWeeklyWeatherReport(forecast,loc,temp_unit,report='weekly')
        mic.say(weather_report)



    def is_valid(self, text):
        """
        Returns True if the text is related to the weather.
        Arguments:
        text -- user-input, typically transcribed speech
        """
        text = text.upper()
        return (self.gettext('WEATHER').upper() in text or
                self.gettext('TEMPERATURE').upper() in text or
                self.gettext('FORECAST').upper() in text)
