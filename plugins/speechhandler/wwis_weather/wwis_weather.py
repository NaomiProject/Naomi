# -*- coding: utf-8 -*-
import datetime
import requests
import json
from collections import OrderedDict
from naomi import plugin
from naomi import profile


class WWISWeatherPlugin(plugin.SpeechHandlerPlugin):

    def intents(self):
        _ = self.gettext
        return {
            'WeatherIntent': {
                'keywords': {
                    'WeatherTypePresentKeyword': [
                        _('snowing'),
                        _('raining'),
                        _('windy'),
                        _('sleeting'),
                        _('sunny')
                    ],
                    'WeatherTypeFutureKeyword': [
                        _('snow'),
                        _('rain'),
                        _('be windy'),
                        _('wind'),
                        _('sleet'),
                        _('be sunny'),
                        _('sun')
                    ],
                    # FIXME The following should really be populated
                    # by the cities from get_location_data, and region
                    # and country information should also be used to
                    # figure out where you are asking about, especially
                    # since that structure respects the user's language.
                    #
                    # LocationKeyword itself then should be constructed
                    # from other keywords: ie:
                    #   '{city} {region}',
                    #   '{city} {country}',
                    #   '{city} {region} {country}',
                    #   '{region}',
                    #   '{region} {country}',
                    #   '{country}'
                    'LocationKeyword': [
                        'seattle',
                        'san francisco',
                        'tokyo'
                    ],
                    'TimeKeyword': [
                        _("morning"),
                        _("afternoon"),
                        _("evening"),
                        _("night")
                    ],
                    'DayKeyword': [
                        _("today"),
                        _("tomorrow"),
                        _("sunday"),
                        _("monday"),
                        _("tuesday"),
                        _("wednesday"),
                        _("thursday"),
                        _("friday"),
                        _("saturday")
                    ],
                    'PossessiveDayKeyword': [
                        _("today's"),
                        _("tomorrow's"),
                        _("sunday's"),
                        _("monday's"),
                        _("tuesday's"),
                        _("wednesday's"),
                        _("thursday's"),
                        _("friday's"),
                        _("saturday's")
                    ]
                },
                'templates': [
                    _("what's the weather in {LocationKeyword}"),
                    _("what's the forecast for {DayKeyword}"),
                    _("what's the forecast for {LocationKeyword}"),
                    _("what's {PossessiveDayKeyword} forecast"),
                    _("what will {PossessiveDayKeyword} weather be"),
                    _("what's the forecast for {LocationKeyword} on {DayKeyword}"),
                    _("what's the forecast for {LocationKeyword} on {DayKeyword} {TimeKeyword}"),
                    _("is it {WeatherTypePresentKeyword} in {LocationKeyword}"),
                    _("will it {WeatherTypeFutureKeyword} this {TimeKeyword}"),
                    _("will it {WeatherTypeFutureKeyword} {DayKeyword}"),
                    _("will it {WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}"),
                    _("when will it {WeatherTypeFutureKeyword}"),
                    _("when will it {WeatherTypeFutureKeyword} in {LocationKeyword}")
                ],
                'action': self.handle
            }
        }

    def settings(self):
        self.get_location_data()
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
        countries = {}
        for country in self.locations:
            countries[country] = country
        return countries

    def get_regions(self):
        _ = self.gettext
        regions = {}
        country = profile.get_profile_var(['wwis_weather', 'country'])
        for region in self.locations[country]:
            regions[region] = region
        if(not regions):
            print(_("Weather information is not available in {}.").format(country))
            print(_("Please check nearby cities in other countries"))
        return regions

    def get_cities(self):
        cities = {}
        for city in self.locations[profile.get_profile_var(["wwis_weather", "country"])][profile.get_profile_var(["wwis_weather", "region"])]:
            cities[city] = city
        return cities

    def get_city_id(self):
        cityId = None
        country = profile.get_profile_var(['wwis_weather', 'country'], "")
        region = profile.get_profile_var(['wwis_weather', 'region'], "")
        city = profile.get_profile_var(['wwis_weather', 'city'], "")
        # check if we have a city or region
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
        WEEKDAY_NAMES = {
            0: _('Monday'),
            1: _('Tuesday'),
            2: _('Wednesday'),
            3: _('Thursday'),
            4: _('Friday'),
            5: _('Saturday'),
            6: _('Sunday')
        }
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
                forecast[day["forecastDate"]]["high"] = day["maxTempF"]
                forecast[day["forecastDate"]]["low"] = day["minTempF"]
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
            elif("tomorrow" in text.lower()):
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
        if snark:
            mic.say(_("I don't know. Why don't you look out the window?"))
