# -*- coding: utf-8 -*-
#created by G10Dras
from jasper import plugin
from semantic.numbers import NumberService
import pyowm
import re

class JasperWeatherplugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        return [
            self.gettext("WEATHER"),
            self.gettext("FORECAST"),
            self.gettext("TOMORROW"),
            self.gettext("NEXT"),
            self.gettext("WEEK"),
            self.gettext("TEMPERATURE"),
            self.gettext("WIND")
                ]

    def handle(self, text, mic):

        serviceNum = NumberService()
        try:
            api_key = self.profile['OpenWeatherMap']['api_key']
            city_name = self.profile['OpenWeatherMap']['city_name']
            country = self.profile['OpenWeatherMap']['country']
            temp_unit = self.profile['OpenWeatherMap']['temp_unit']
            lang = self.profile['OpenWeatherMap']['lang']
            owm = pyowm.OWM(apikey, language= lang)
        except:
            mic.say(self.gettext("Openweathermap not found in profile."))



    def formatTimeStamp(unix_time):
        return datetime.fromtimestamp(unix_time).strftime("%B %d")

    def getWeeklyWeatherReport(forecast, loc,temp_unit='celsius', report='current'):
        weather_report = "Weather forecast for next week at "+loc +". "
        rainy_days = len(forecast.when_rain())
        if rainy_days > 0:
            rainy_days_str = "Rainy Days are. "
            for d in range(rainy_days):
                rain_day = forecast.when_rain()[d].get_reference_time()
                date_str = formatTimeStamp(rain_day)
                ainy_days_str += date_str + ". "
                weather_report += rainy_days_str
                date_str = ''

        most_rainy = forecast.most_rainy()
        if most_rainy:
            weather_report += "You will observe heavy rain on. "
            ref_time = most_rainy.get_reference_time()
            date_str = formatTimeStamp(ref_time)
            weather_report += date_str + ". "
            date_str = ''

        sunny_days = len(forecast.when_sun())
        if sunny_days > 0:
            sunny_days_str = "Sunny Days are. "
            for d in range(sunny_days):
                sunny_day = forecast.when_rain()[d].get_reference_time()
                date_str = formatTimeStamp(sunny_day)
                sunny_days_str += date_str + ". "

        weather_report += sunny_days_str
        date_str = ''

        most_hot = forecast.most_hot()
        if most_hot:
            weather_report += "You will feel heat on. "
            ref_time = most_hot.get_reference_time()
            date_str = formatTimeStamp(ref_time)
            weather_report += date_str + ". "
            date_str = ''

            most_windy = forecast.most_windy()
            if most_windy:
                weather_report += "Most windy day will be. "
                ref_time = most_windy.get_reference_time()
                date_str = formatTimeStamp(ref_time)
                weather_report += date_str + ". "
                date_str = ''

            most_humid = forecast.most_humid()
            if most_humid:
                weather_report += "Most humid day will be. "
                ref_time = most_humid.get_reference_time()
                date_str = formatTimeStamp(ref_time)
                weather_report += date_str + ". "
                date_str = ''

            most_cold = forecast.most_cold()
            if most_cold:
                weather_report += "Coolest day will be. "
                ref_time = most_cold.get_reference_time()
                date_str = formatTimeStamp(ref_time)
                weather_report += date_str + ". "
                date_str = ''

        return weather_report

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
                weather_report = self.gettext("\n Weather at {}. Today is {}. There is a chance of "+
                                              "{}. Now Temperature is {} degree "+
                                              "{}. Humidity {} percent. Wind Speed "+
                                              "{}. with cloud cover {} percent.\n".format(loc, stat, detstat, curr_temp, temp_unit, humi, wind_speed, clou))

            elif report == 'tommorow':
                temp = weather.get_temperature(temp_unit)
                temp_morn = serviceNum.parseMagnitude(temp['morn'])
                temp_day = serviceNum.parseMagnitude(temp['day'])
                temp_night = serviceNum.parseMagnitude(temp['night'])
                weather_report = self.gettext("\nWeather at {}. Tomorrow will be {}. There will be a chance of "+
                                              "{}. Temperature in the morning {} degree "+
                                              "{}. Days Temperature will be  degree "+
                                              "{}. and Temperature at night will be {} degree "+
                                              "{}. Humidity {} percent. Wind Speed "+
                                              "{}. with clouds cover {} percent.\n".format(loc, stat, detstat, temp_morn, temp_unit, temp_day, temp_unit, temp_night, temp_unit, humi ))

            return weather_report




            owm = pyowm.OWM(api_key)

            if re.search(r'\b(CURRENT|TODAYS|TODAY)\b',text,re.IGNORECASE):
                cw = owm.weather_at_place(city_name+","+country)
                loc = cw.get_location().get_name()
                weather = cw.get_weather()
                weather_report = getWeatherReport(weather,loc,temp_unit,report='current')
                mic.say(weather_report)

            elif re.search(r'\b(TOMORROWS|TOMORROW)\b',text,re.IGNORECASE):
                forecast = owm.daily_forecast(city_name)
                fore = forecast.get_forecast()
                loc = fore.get_location().get_name()
                tomorrow = pyowm.timeutils.tomorrow()
                weather = forecast.get_weather_at(tomorrow)
                weather_report = getWeatherReport(weather,loc,temp_unit,report='tommorow')
                mic.say(weather_report)

            elif re.search(r'\b(WEEKLY)\b',text,re.IGNORECASE):
                forecast = owm.daily_forecast(city_name)
                fore = forecast.get_forecast()
                loc = fore.get_location().get_name()
                weather_report = getWeeklyWeatherReport(forecast,loc,temp_unit,report='weekly')
                mic.say(weather_report)

    def is_valid(self, text):
        return any(p.lower() in text.lower() for p in self.get_phrases())
