# -*- coding: utf-8 -*-
import os
import unittest
from naomi import paths
from naomi import plugin
from naomi import profile
try:
    from padatious import IntentContainer
except ModuleNotFoundError:
    raise unittest.SkipTest("padatious module not found")


# is_keyword just checks to see if the word is a normal word or a keyword
# (surrounded by curly brackets)
def is_keyword(word):
    word = word.strip()
    response = False
    if("{}{}".format(word[:1], word[-1:]) == "{}"):
        response = True
    return response


# Convert a word ("word") to a keyword ("{word}")
def to_keyword(word):
    return "{}{}{}".format("{", word, "}")


class PadatiousTTIPlugin(plugin.TTIPlugin):
    container = IntentContainer('intent_cache')

    def add_intents(self, intents):
        for intent in intents:
            # this prevents collisions between intents
            intent_base = intent
            intent_inc = 0
            locale = profile.get("language")
            while intent in self.intent_map['intents']:
                intent_inc += 1
                intent = "{}{}".format(intent_base, intent_inc)
            if('locale' in intents[intent_base]):
                # If the selected locale is not available, try matching just
                # the language ("en-US" -> "en")
                if(locale not in intents[intent_base]['locale']):
                    for language in intents[intent_base]['locale']:
                        if(language[:2] == locale[:2]):
                            locale = language
                            break
            while intent in self.intent_map['intents']:
                intent_inc += 1
                intent = "{}{}".format(intent_base, intent_inc)
            self.intent_map['intents'][intent] = {
                'action': intents[intent_base]['action'],
                'name': intent_base,
                'templates': []
            }
            templates = intents[intent_base]['locale'][locale]['templates']
            if('keywords' in intents[intent_base]['locale'][locale]):
                for keyword in intents[intent_base]['locale'][locale]['keywords']:
                    keyword_token = "{}_{}".format(intent, keyword)
                    # print("Keyword_token: {}".format(keyword_token))
                    self.keywords[keyword_token] = {
                        'words': intents[intent_base]['locale'][locale]['keywords'][keyword],
                        'name': keyword
                    }
                    # print("Adding keyword '{}': {}".format(keyword_token,intents[intent_base]['keywords'][keyword]))
                    # map the keywords into the intents
                    templates = [t.replace(keyword, keyword_token) for t in templates]
                    self.container.add_entity(keyword_token, intents[intent_base]['locale'][locale]['keywords'][keyword])
            self.intent_map['intents'][intent]['templates'] = templates
            self.container.add_intent(intent, templates)

    # Call train after loading all the intents.
    def train(self):
        # print("Training")
        self.container.train()
        self.trained = True

    def get_plugin_phrases(self, passive_listen=False):
        phrases = []
        # include the keyword, otherwise
        if(passive_listen):
            phrases.extend(profile.get(["keyword"]))
        # Include any custom phrases (things you say to Naomi
        # that don't match plugin phrases. Otherwise, there is
        # a high probability that something you say will be
        # interpreted as a command. For instance, the
        # "check_email" plugin has only "EMAIL" and "INBOX" as
        # standard phrases, so every time I would say
        # "Naomi, check email" Naomi would hear "NAOMI SHUT EMAIL"
        # and shut down.
        custom_standard_phrases_file = paths.data(
            "standard_phrases",
            "{}.txt".format(profile.get(['language'], 'en-US'))
        )
        if(os.path.isfile(custom_standard_phrases_file)):
            with open(custom_standard_phrases_file, mode='r') as f:
                for line in f:
                    phrase = line.strip()
                    if phrase:
                        phrases.append(phrase)
        # Return a list of phrases Naomi might hear.
        for intent in self.intent_map['intents']:
            # pprint(self.intent_map['intents'][intent]['templates'])
            if('templates' in self.intent_map['intents'][intent]):
                templates = self.intent_map['intents'][intent]['templates']
                # pprint(self.keywords)
                keywords_list = [keyword for keyword in self.keywords]
                # print("Keywords: {}".format(keywords_list))
                for keyword in keywords_list:
                    # This will not replace keywords that do not have a list associated with them, like regex and open keywords
                    if(keyword[:len(intent) + 1] == "{}_".format(intent)):
                        # print("Replacing {} with words from {} in templates".format(keyword,self.keywords[keyword]['words']))
                        for template in templates:
                            if(to_keyword(keyword) in template):
                                templates.extend([template.replace(to_keyword(keyword), word.upper()) for word in self.keywords[keyword]['words']])
                            # Now that we have expanded every instance of keyword in templates, delete any template that still contains keyword
                            templates = [template for template in templates if not to_keyword(keyword) in template]
                phrases.extend(templates)
        return sorted(phrases)

    def determine_intent(self, phrase):
        response = {}
        intent = self.container.calc_intent(phrase)
        if(intent):
            matches = {}
            for match in intent.matches:
                if match in self.keywords:
                    matches.update({self.keywords[match]['name']: [intent[match]]})
                else:
                    matches.update({match: [intent[match]]})
            response = {
                intent.name: {
                    'action': self.intent_map['intents'][intent.name]['action'],
                    'input': phrase,
                    'matches': [{self.keywords[match]['name'] if match in self.keywords else match: [intent[match]]} for match in intent.matches],
                    'score': intent.conf
                }
            }
        return response
