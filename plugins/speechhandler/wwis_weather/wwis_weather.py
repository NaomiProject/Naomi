# -*- coding: utf-8 -*-
import datetime
import requests
import json
from collections import OrderedDict
from naomi import plugin
from naomi import profile


WEEKDAY_NAMES = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
}


class WWISWeatherPlugin(plugin.SpeechHandlerPlugin):

    def intents(self):
        return {
            'WeatherIntent': {
                'locale': {
                    'en-US': {
                        'keywords': {
                            'ForecastKeyword': [
                                'WEATHER',
                                'FORECAST',
                                'WEATHER REPORT',
                                'WEATHER FORECAST'
                            ],
                            'WeatherTypePresentKeyword': [
                                'SNOWING',
                                'RAINING',
                                'WINDY',
                                'SLEETING',
                                'SUNNY'
                            ],
                            'WeatherTypeFutureKeyword': [
                                'SNOW',
                                'RAIN',
                                'BE WINDY',
                                'SLEET',
                                'BE SUNNY'
                            ],
                            'LocationKeyword': [
                                'SEATTLE',
                                'SAN FRANCISCO',
                                'TOKYO'
                            ],
                            'TimeKeyword': [
                                "MORNING",
                                "AFTERNOON",
                                "EVENING",
                                "NIGHT"
                            ],
                            'DayKeyword': [
                                "TODAY",
                                "TOMORROW",
                                "SUNDAY",
                                "MONDAY",
                                "TUESDAY",
                                "WEDNESDAY",
                                "THURSDAY",
                                "FRIDAY",
                                "SATURDAY"
                            ]
                        },
                        'templates': [
                            "WHAT IS THE {ForecastKeyword} IN {LocationKeyword}",
                            "WHAT IS THE {ForecastKeyword} FOR {DayKeyword}",
                            "WHAT IS THE {ForecastKeyword} FOR {LocationKeyword}",
                            "WHAT IS THE {ForecastKeyword} FOR {LocationKeyword} ON {DayKeyword}",
                            "WHAT IS THE {ForecastKeyword} FOR {LocationKeyword} ON {DayKeyword} {TimeKeyword}",
                            "IS IT {WeatherTypePresentKeyword} IN {LocationKeyword}",
                            "WILL IT {WeatherTypeFutureKeyword} THIS {TimeKeyword}",
                            "WILL IT {WeatherTypeFutureKeyword} {DayKeyword}",
                            "WILL IT {WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}",
                            "WHEN WILL IT {WeatherTypeFutureKeyword}",
                            "WHEN WILL IT {WeatherTypeFutureKeyword} IN {LocationKeyword}"
                        ]
                    },
                    'fr-FR': {
                        'keywords': {
                            'WeatherTypePresentKeyword': [
                                'IL NEIGE',
                                'IL PLUIE',
                                'IL VENT'
                            ],
                            'WeatherTypeTodayFutureKeyword': [
                                'SERA-T-IL NEIGE',
                                'PLEUVRA-T-IL',
                                'DU VENT',
                                'SERA-CE VENTEUX',
                                'SERA-T-IL DU VENT',
                                'SERA-T-IL ENSOLEILLÉ'
                            ],
                            'WeatherTypeTomorrowFutureKeyword': [
                            ],
                            'LocationKeyword': [
                                'SEATTLE',
                                'SAN FRANCISCO',
                                'TOKYO'
                            ],
                            'TimeKeyword': [
                                "MATIN",
                                "MIDI",
                                "SOIR"
                            ],
                            'DayKeyword': [
                                "AUJOURD'HUI",
                                "DEMAIN",
                                "DIMANCHE",
                                "LUNDI",
                                "MARDI",
                                "MERCREDI",
                                "JEUDI",
                                "VENDREDI",
                                "SAMEDI"
                            ]
                        },
                        'templates': [
                            "QUELLE EST LA MÉTÉO À {LocationKeyword}",
                            "QUELLES SONT LES PRÉVISIONS POUR {DayKeyword}",
                            "QUELLES SONT LES PRÉVISIONS POUR {LocationKeyword}",
                            "QUELLES SONT LES PRÉVISIONS POUR {LocationKeyword} {DayKeyword}",
                            "QUELLES SONT LES PRÉVISIONS POUR {LocationKeyword} LE {DayKeyword} {TimeKeyword}",
                            "{WeatherTypePresentKeyword} À {LocationKeyword}",
                            "{WeatherTypeFutureKeyword} CET {TodayTimeKeyword}",
                            "{WeatherTypeFutureKeyword} {DayKeyword}",
                            "{WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}",
                            "{WeatherTypeFutureKeyword}",
                            "{WeatherTypeFutureKeyword} À {LocationKeyword}"
                        ]
                    }
                },
                'action': self.handle
            }
        }

    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ('wwis_weather', 'country'), {
                        'type': 'listbox',
                        'title': _('Please select your country from the list'),
                        'description': "".join([
                            _('This value is being used to help locate your Area ID, which will be used to provide weather information')
                        ]),
                        'options': self.get_countries
                    }
                ),
                (
                    ('wwis_weather', 'region'), {
                        'type': 'listbox',
                        'title': _('Please select your region or city from the list'),
                        'description': _('Please select your region or city from the list, which will be used to provide weather information'),
                        'options': self.get_regions,
                        'active': lambda: True if profile.check_profile_var_exists(['wwis_weather', 'country']) and len(profile.get_profile_var(["wwis_weather", "country"])) > 0 else False
                    }
                ),
                (
                    ('wwis_weather', 'city'), {
                        'type': 'listbox',
                        'title': _('Please select your city from the list'),
                        'description': _('Please select your city from the list. This will be used as the default location when providing weather information'),
                        'options': self.get_cities,
                        # This is only active if the currently selected region is a dictionary and not a city
                        # 'active': lambda: True if isinstance(self.locations[profile.get_profile_var(["wwis_weather", "country"])][profile.get_profile_var(["wwis_weather", "region"])], dict) else False
                        'active': self.city_isactive
                    }
                ),
                (
                    ('wwis_weather', 'temperature'), {
                        'type': 'listbox',
                        'title': _("Would you prefer weather in Celcius or Fahrenheit?"),
                        'description': _("Allows you to receive your weather forecast in either Celcius or Fahrenheit"),
                        'options': ['Celcius', 'Fahrenheit'],
                        'active': lambda: True if profile.check_profile_var_exists(['wwis_weather', 'country']) and len(profile.get_profile_var(["wwis_weather", "country"])) > 0 else False,
                        'default': 'Fahrenheit'
                    }
                )
            ]
        )

    def city_isactive(self):
        response = False
        country = profile.get_profile_var(["wwis_weather", "country"])
        if country:
            if(isinstance(self.locations[country], dict)):
                return True if isinstance(self.locations[country][profile.get_profile_var(["wwis_weather", "region"])], dict) else False
        return response

    def get_location_data(self):
        if 'locations' not in dir(self):
            # Set the language used for the location data
            language = profile.get_profile_var(["language"], "en")[:2]
            url = "https://worldweather.wmo.int/en/json/Country_{}.xml".format(language)
            response = requests.get(url, timeout=2)
            jsondoc = str(response.content, 'utf-8')
            self.locationdata = json.loads(jsondoc)
            # Make a list of locations
            self.locations = {}
            # Country here is just an index
            for country in self.locationdata["member"]:
                if(isinstance((self.locationdata["member"][country]), dict)):
                    memName = self.locationdata["member"][country]["memName"]
                    self.locations[memName] = {}
                    for city in self.locationdata["member"][country]["city"]:
                        if(", " in city["cityName"]):
                            cityId = city["cityId"]
                            cityName, regionName = city["cityName"].split(", ")
                            if regionName not in self.locations[memName].keys():
                                self.locations[memName][regionName] = {}
                            self.locations[memName][regionName][cityName] = cityId
                        else:
                            cityName = city["cityName"]
                            cityId = city["cityId"]
                            self.locations[memName][cityName] = cityId

    def get_countries(self):
        self.get_location_data()
        countries = {}
        for country in self.locations:
            countries[country] = country
        return countries

    def get_regions(self):
        self.get_location_data()
        regions = {}
        country = profile.get_profile_var(['wwis_weather', 'country'])
        for region in self.locations[country]:
            regions[region] = region
        if(not regions):
            print("Weather information is not available in {}.".format(country))
            print("Please check nearby cities in other countries")
        return regions

    def get_cities(self):
        self.get_location_data()
        cities = {}
        for city in self.locations[profile.get_profile_var(["wwis_weather", "country"])][profile.get_profile_var(["wwis_weather", "region"])]:
            cities[city] = city
        return cities

    def get_city_id(self):
        self.get_location_data()
        cityId = None
        country = profile.get_profile_var(['wwis_weather', 'country'], "")
        region = profile.get_profile_var(['wwis_weather', 'region'], "")
        city = profile.get_profile_var(['wwis_weather', 'city'], "")
        # check if we have a city or region
        try:
            if(isinstance((self.locations[country][region]), dict)):
                try:
                    cityId = self.locations[country][region][city]
                except KeyError:
                    city = None
            else:
                try:
                    cityId = self.locations[country][region]
                    city = region
                except KeyError:
                    city = None
        except KeyError:
            city = None
        return city, cityId

    def handle(self, intent, mic):
        # Ideally, we could use our list of countries to check if any country
        # appears in the input, then check for regions in the current country,
        # and finally cities in the selected region, so I should be able to
        # ask for the weather in Paris, France and have it tell me even if my
        # base location is Hoboken, New Jersey.
        # For now we just check to see if "Today" or "Tomorrow" appear
        # in the text, and return the requested day's weather.
        # First, establish the cityId
        _ = self.gettext
        text = intent['input']
        city, cityId = self.get_city_id()
        country = profile.get_profile_var(["wwis_weather", "country"])
        # text = intent.input
        snark = True
        if(cityId):
            # Next, pull the weather data for City
            language = profile.get_profile_var(["language"], "en")[:2]
            url = "https://worldweather.wmo.int/en/json/{}_{}.xml".format(cityId, language)
            # print( "Requesting url {}".format(url) )
            response = requests.get(url)
            # print( "Request finished" )
            jsondoc = str(response.content, 'utf-8')
            weatherdata = json.loads(jsondoc)
            # print(json.dumps(weatherdata, indent=4, sort_keys=True))

            forecast = {}
            for day in weatherdata["city"]["forecast"]["forecastDay"]:
                forecast[day["forecastDate"]] = {}
                forecast[day["forecastDate"]]["weather"] = day["weather"]
                if profile.get(['wwis_weather', 'temperature'], "f")[:1].lower() == "f":
                    forecast[day["forecastDate"]]["high"] = day["maxTempF"]
                    forecast[day["forecastDate"]]["low"] = day["minTempF"]
                else:
                    forecast[day["forecastDate"]]["high"] = day["maxTemp"]
                    forecast[day["forecastDate"]]["low"] = day["minTemp"]
            if(not forecast):
                mic.say(
                    _("Sorry, forecast information is not currently available for {} in {}").format(
                        weatherdata["city"]["cityName"],
                        country
                    )
                )
            today = datetime.date.today()
            todaydate = "{:4d}-{:02d}-{:02d}".format(
                today.year,
                today.month,
                today.day
            )
            tomorrow = today + datetime.timedelta(days=1)
            tomorrowdate = "{:4d}-{:02d}-{:02d}".format(
                tomorrow.year,
                tomorrow.month,
                tomorrow.day
            )
            if(_("today") in text.lower()):
                if(todaydate in forecast.keys()):
                    mic.say(
                        _("The weather today in {} is {}").format(
                            city, forecast[todaydate]["weather"]
                        )
                    )
                    snark = False
            elif(_("tomorrow") in text.lower()):
                if(tomorrowdate in forecast.keys()):
                    mic.say(
                        _("The weather tomorrow in {} will be {}").format(
                            city,
                            forecast[tomorrowdate]["weather"]
                        )
                    )
                    snark = False
            else:
                first = True
                for day in sorted(forecast.keys()):
                    if(day == todaydate):
                        DOW = _("today")
                    elif(day == tomorrowdate):
                        DOW = _("tomorrow")
                    else:
                        DOW = WEEKDAY_NAMES[datetime.datetime.strptime(day, "%Y-%m-%d").weekday()]
                    if(first):
                        response = _("{} in {}, the weather will be {}").format(
                            DOW,
                            city,
                            forecast[day]["weather"]
                        )
                        first = False
                    else:
                        response = _("{}, the weather will be {}").format(
                            DOW,
                            forecast[day]["weather"]
                        )
                    if(forecast[day]["low"] and forecast[day]["high"]):
                        response += _(" with a low of {} and a high of {} degrees").format(
                            forecast[day]["low"],
                            forecast[day]["high"]
                        )
                    elif(forecast[day]["low"]):
                        response += _(" with a low of {} degrees").format(
                            forecast[day]["low"]
                        )
                    elif(forecast[day]["high"]):
                        response += _(" with a high of {} degrees").format(
                            forecast[day]["high"]
                        )
                    mic.say(response)
                    snark = False
        else:
            mic.say("I have no location on record. Please run Naomi --repopulate and select a city.")
            snark = False
        if snark:
            mic.say(_("I don't know. Why don't you look out the window?"))
