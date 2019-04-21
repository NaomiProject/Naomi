# -*- coding: utf-8 -*-
from collections import OrderedDict
from naomi import i18n, paths, plugin, profile
import logging
import requests
import json


_ = None

class WWISWeatherPlugin(plugin.SpeechHandlerPlugin):
    
    def __init__(self, *args, **kwargs):
        global _
        self._logger = logging.getLogger(__name__)
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations, profile.get_profile())
        _ = translator.gettext
        self._logger.debug("WWIS_Weather INIT")
        self.settings = OrderedDict(
            [
                (
                    ('wwis_weather','country'),{
                        'type': 'listbox',
                        'title': _('Please select your country from the list'),
                        'description': "".join([
                            _('This value is being used to help locate your Area ID, which will be used to provide weather information')
                        ]),
                        'options': self.get_countries,
                        'validation': lambda country : country in self.getcountries()
                    }
                ),
                (
                    ('wwis_weather','region'),{
                        'type':'listbox',
                        'title':_('Please select your region or city from the list'),
                        'description':_('Please select your region or city from the list, which will be used to provide weather information'),
                        'options': self.get_regions,
                        'validation':lambda region: True if region in self.get_regions(profile.get_profile_var(["wwis_weather","country"])) else False,
                        'active': True if profile.check_profile_var_exists(['wwis_weather','country']) and len(profile.get_profile_var(["wwis_weather","country"]))>0 else False
                    }
                ),
                (
                    ('wwis_weather','city'),{
                        'type':'listbox',
                        'title':_('Please select your city from the list'),
                        'description':_('Please select your city from the list, which will be used as the default location when providing weather information'),
                        'options': self.get_cities,
                        'validation':lambda city: True if city in self.get_cities(profile.get_profile_var(["wwis_weather","country"]),profile.get_profile_var(["wwis_weather","region"])) else False,
                        # This is only active if the currently selected region is a dictionary and not a city
                        'active':lambda city: True
                    }
                )
            ]
        )

    def get_countries(self):
        url = "https://worldweather.wmo.int/en/json/Country_en.xml"
        response = requests.get(url)
        jsondoc = str(response.content,'utf-8')

        self.countrydata = json.loads(jsondoc)
        countries = {}
        for country in countrydata["member"]:
            if(type(countrydata["member"][country]) is dict):
                memId = countrydata["member"][country]["memId"]
                memName = countrydata["member"][country]["memName"]
                countries[memName]=country
        return countries

    def get_regions(country):
        return ["Virgina", "West Virginia"]
    
    def get_cities(country,region):
        return ["Bellingham", "Lewisburg", "Richmond"]
        
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
