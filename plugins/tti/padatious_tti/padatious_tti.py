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


class PadatiousTTIPlugin(plugin.TTIPlugin):
    container = IntentContainer('intent_cache')

    def add_intents(self, intents):
        for intent in intents:
            # this prevents collisions between intents
            intent_base = intent
            intent_inc = 0
            while intent in self.intent_map['intents']:
                intent_inc += 1
                intent = "{}{}".format(intent_base, intent_inc)
            self.intent_map['intents'][intent] = {
                'action': intents[intent_base]['action'],
                'name': intent_base,
                'templates': []
            }
            templates = intents[intent_base]['templates']
            if('keywords' in intents[intent_base]):
                for keyword in intents[intent_base]['keywords']:
                    keyword_token = "{}_{}".format(intent, keyword)
                    self.keywords[keyword_token] = {
                        'words': intents[intent_base]['keywords'][keyword],
                        'name': keyword
                    }
                    # print("Adding keyword '{}': {}".format(keyword_token,intents[intent_base]['keywords'][keyword]))
                    # map the keywords into the intents
                    templates = [t.replace(keyword, keyword_token) for t in templates]
                    self.container.add_entity(keyword_token, intents[intent_base]['keywords'][keyword])
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
        # There was no need to make a list of words while
        # parsing the intent, so in this case, parse the
        # words directly from the templates and keyword
        # lists
        for intent in self.intent_map['intents']:
            # print("Search {} for words".format(intent))
            for phrase in self.intent_map['intents'][intent]['templates']:
                # print("Parsing '{}'".format(phrase))
                template_words = phrase.split()
                for template_word in template_words:
                    if is_keyword(template_word):
                        # The keyword group name in self.keywords
                        # does not include the curly braces, so strip
                        # them off
                        keyword = template_word[1:][:-1]
                        if(keyword in self.keywords):
                            for word in self.keywords[keyword]['words']:
                                # print("Adding word: {} for keyword list: {}".format(word, keyword))
                                phrases.append(word.upper())
                    else:
                        # print("Adding word: {}".format(template_word))
                        phrases.append(template_word.upper())
        return sorted(list(set(phrases)))

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
