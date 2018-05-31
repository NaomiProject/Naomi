# -*- coding: utf-8 -*-
import re
import pyowm
from semantic.numbers import NumberService

from jasper import plugin


class OpenWeatherPlugin(plugin.SpeechHandlerPlugin):
    def __init__(self, *args, **kwargs):
        super(OpenWeatherPlugin, self).__init__(*args, **kwargs)
        try:
            self.city_name = self.profile['weather']['city_name']
            self.country = self.profile['weather']['country']
        except KeyError:
            raise ValueError('Weather location not configured.')

        try:
            self.temp_unit = self.profile['weather']['unit']
        except KeyError:
            raise ValueError('Weather unit not configured.')
        try:
            self.api_key = self.profile['weather']['api_key']
        except KeyError:
            raise ValueError('No openweathermap API key provided.')

    def get_phrases(self):
                return [
                        self.gettext("WEATHER"),
                        self.gettext("TODAY"),
                        self.gettext("TOMORROW"),
                        self.gettext("TEMPERATURE"),
                        self.gettext("FORECAST"),
                        self.gettext("YES"),
                        self.gettext("NO"),
                        self.gettext("CURRENT")
                        ]

    def handle(self, text, mic):
        owm = pyowm.OWM(API_key=self.api_key)

        serviceNum = NumberService()

        weather_report = 'Server Down.'
        cw = owm.weather_at_place(self.city_name+','+self.country)

        loc = cw.get_location().get_name()
        weather = cw.get_weather()

        wind = weather.get_wind()
        wind_speed = serviceNum.parseMagnitude(wind["speed"])
        humi = serviceNum.parseMagnitude(weather.get_humidity())
        # clou = serviceNum.parseMagnitude(weather.get_clouds())
        stat = weather.get_status()
        detstat = weather.get_detailed_status()

        if (self.gettext('CURRENT').upper() in text.upper()
                or self.gettext('TODAY').upper() in text.upper()):
            temp = weather.get_temperature(self.temp_unit)
            temp_unit = self.temp_unit
            temp_max = serviceNum.parseMagnitude(temp['temp_max'])
            temp_min = serviceNum.parseMagnitude(temp['temp_min'])
            curr_temp = serviceNum.parseMagnitude(temp['temp'])
            weather_report = self.gettext("Weather at {loc}. Today is {stat}. "
                                          + "There is a chance of {detstat}. "
                                          + "Now Temperature is {curr_temp} "
                                          + "degree {temp_unit} "
                                          + "Humidity {humi} percent."
                                          + " Wind Speed {wind_speed}."
                                          ).format(
                        loc=loc,
                        stat=stat,
                        detstat=detstat,
                        curr_temp=curr_temp,
                        temp_unit=self.temp_unit,
                        humi=humi,
                        wind_speed=wind_speed)
            mic.say(weather_report)

        elif self.gettext('TOMORROW').upper() in text.upper():
            forecast = owm.daily_forecast(self.city_name)
            fore = forecast.get_forecast()
            loc = fore.get_location().get_name()
            temp_unit = self.temp_unit
            tomorrow = pyowm.timeutils.tomorrow()
            weather = forecast.get_weather_at(tomorrow)
            temp = weather.get_temperature(self.temp_unit)
            temp_morn = serviceNum.parseMagnitude(temp['morn'])
            temp_day = serviceNum.parseMagnitude(temp['day'])
            temp_night = serviceNum.parseMagnitude(temp['night'])
            weather_report = self.gettext("Weather at {loc}. Tomorrow "
                                          + "will be {stat}. "
                                          + "There will be a chance of "
                                          + "{detstat}. Temperature in the "
                                          + "morning {temp_morn} degree "
                                          + "{temp_unit}. Days Temperature "
                                          + "will be {temp_day} degree "
                                          + "{temp_unit}. and Temperature at "
                                          + "night will be {temp_night} degree"
                                          + " {temp_unit}. Humidity {humi}"
                                          + " percent. Wind Speed "
                                          + "{wind_speed}.").format(
                            loc=loc,
                            stat=stat,
                            detstat=detstat,
                            temp_morn=temp_morn,
                            temp_day=temp_day,
                            temp_night=temp_night,
                            temp_unit=temp_unit,
                            humi=humi,
                            wind_speed=wind_speed)
            mic.say(weather_report)
        elif (self.gettext('FORECAST').upper() in text.upper()
              or self.gettext('WEEKLY').upper() in text.upper()):
            forecast = owm.daily_forecast(city_name)
            fore = forecast.get_forecast()
            loc = fore.get_location().get_name()
            weather_report = getWeeklyWeatherReport(forecast, loc,
                                                    temp_unit, report='weekly')
            mic.say(weather_report)
        else:
            cw = owm.weather_at_place(self.city_name+','+self.country)
            loc = cw.get_location().get_name()
            weather = cw.get_weather()
            temp = weather.get_temperature(self.temp_unit)
            temp_unit = self.temp_unit
            temp_max = serviceNum.parseMagnitude(temp['temp_max'])
            temp_min = serviceNum.parseMagnitude(temp['temp_min'])
            curr_temp = serviceNum.parseMagnitude(temp['temp'])
            weather_report = self.gettext("Weather at {loc}. Today is {stat}."
                                          + "There is a chance of "
                                          + "{detstat}. Now Temperature is"
                                          + "{curr_temp} degree"
                                          + "{temp_unit}.").format(
                            loc=loc,
                            stat=stat,
                            detstat=detstat,
                            curr_temp=curr_temp,
                            temp_unit=self.temp_unit
                            )
            mic.say(weather_report)

    def is_valid(self, text):
        """
        Returns True if the input is related to birthdays.

        Arguments:
        ext -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
