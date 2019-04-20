# -*- coding: utf-8 -*-
from naomi import plugin, profile
import logging
import requests
import json

_ = None

class WWISWeatherPlugin(plugin.SpeechHandlerPlugin):
    settings = OrderedDict(
        [
            (
                ('wwis_weather','country'),{
                    'type': 'listbox',
                    'title': _('Please select your country from the list'),
                    'description': "".join([
                        _('This value is being used to help locate your Area ID, which will be used to provide weather information')
                    ]),
                    'options': get_countries,
                    'validation': lambda country : country in getcountries()
                }
            ),
            (
                ('wwis_weather','region'),{
                    'type':'listbox',
                    'title':_('Please select your region or city from the list'),
                    'description':_('Please select your region or city from the list, which will be used to provide weather information'),
                    'options': get_regions,
                    'validation':lambda region: True if region in get_regions(self.config.wwis_weather.country) else False,
                    'active': len(self.profile.wwis_weather.country)>0
                }
            ),
            (
                ('wwis_weather','city'),{
                    'type':'listbox',
                    'title':_('Please select your city from the list'),
                    'description':_('Please select your city from the list, which will be used as the default location when providing weather information'),
                    'options': get_cities,
                    'validation':lambda city: True if city in get_cities
                    # This is only active if the currently selected region is a dictionary and not a city
                    'active':lambda city: True
                }
            )
        ]
    )
    config={wwis_weather: {}}
    
    def __init__(self):
        global _
        self._logger = logging.getLogger(__name__)
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations, profile.get_profile())
        _ = translator.gettext
        self.get_location_data()

    def get_countries(self):
        url = "https://worldweather.wmo.int/en/json/Country_en.xml"
        response = requests.get(url)
        jsondoc = str(response.content,'utf-8')

        self.countrydata = json.loads(jsondoc)
        self.countries = {}
        for country in countrydata["member"]:
            if(type(countrydata["member"][country]) is dict):
                memId = countrydata["member"][country]["memId"]
                memName = countrydata["member"][country]["memName"]
                self.countries[memName]=country

    # The actual meaning of this function is "Does the selected county
    # not contain any regions with cities within them?"
    def country_contains_regions(self):
        self._country_contains_regions = False
        regions = {}
        for city in self.countrydata["member"][self.countryid]["city"]:
            if("," in city["cityName"]):
                cityId = city["cityId"]
                cityName,regionName = city["cityName"].split(", ")
                if regionName not in regions.keys():
                    self.regions[regionName]={}
                self.regions[regionName][cityName]=cityId
                regions = True
            else:
                region
        if regions
        return regions
    
    def get_regions(self):
        if(self.country_contains_regions(self.config.wwis_weather.country)):
            for region in sorted(self.regions):
                print("{}".format(state))
            stateName = ""
            while stateName not in states:
                stateName = input("Select region: ")
            print("")
            if(type(states[stateName]) is dict):
                print("Select a city from the list:")
                for city in states[stateName]:
                    print("{}\t{}".format(states[stateName][city], city))
                cityName = ""
                while cityName not in states[stateName]:
                    cityName = input("Select City: ")
                cityId = states[stateName][cityName]
                print("")
            else:
                cityId = states[stateName]

    def get_cities
        if(self.country
            # in this case these are cities not regions
            for city in sorted(states):
                print("{}".format(city))
            cityName = ""
            while cityName not in states:
                cityName = input("Select City: ")
            cityId = states[stateName]

    def get_phrases(self):
        return [
            _("weather")
        ]
    
    def handle(self,text,mic):
        mic.say(_("I don't know. Why don't you look out the window?"))
            
    def is_valid(self,text):
        """
        Returns True if the input is related to the weather.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
