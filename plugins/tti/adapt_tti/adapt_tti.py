# -*- coding: utf-8 -*-
import json
import os
import re
import sys
from adapt.entity_tagger import EntityTagger
from adapt.tools.text.tokenizer import EnglishTokenizer
from adapt.tools.text.trie import Trie
from adapt.intent import IntentBuilder
from adapt.parser import Parser
from adapt.engine import IntentDeterminationEngine
from naomi import paths
from naomi import plugin
from naomi import profile


def weight(count, examples):
    weight = 0
    if count == examples:
        weight = 1
    elif count < examples:
        weight = .5
    return weight


def makeindex(num):
    char = []
    while num>0:
        char.insert(0, chr(97 + (num % 26)))
        num = num // 26
    return "".join(char)


# is_keyword just checks to see if the word is a normal word or a keyword
# (surrounded by curly brackets)
def is_keyword(word):
    word = word.strip()
    response = False
    if("{}{}".format(word[:1],word[-1:]) == "{}"):
        response = True
    return response


class AdaptTTIPlugin(plugin.TTIPlugin):
    tokenizer = EnglishTokenizer()
    trie = Trie()
    tagger = EntityTagger(trie, tokenizer)
    parser = Parser(tokenizer, tagger)
    engine = IntentDeterminationEngine()

    def add_word(self, intent, word):
        # Check if this is a collection
        if word[:1]+word[-1:]=="{}":
            keyword_name = "{}_{}".format(intent,word[1:][:-1])
            # print("Registering words for '{}'".format(keyword_name))
            # This doesn't have to exist:
            if keyword_name in self.keywords:
                for keyword_word in self.keywords[keyword_name]['words']:
                    # print("Registering '{}'".format(keyword_word))
                    self.engine.register_entity(keyword_word, keyword_name)
            if keyword_name in self.regex:
                for regex in self.regex[keyword_name]:
                    self.engine.register_regex_entity(regex)
        else:
            # Just register the word as a required word
            self.keyword_index+=1
            keyword_name = "{}_{}".format(intent, makeindex(self.keyword_index))
            # print("Registering word '{}' as {}".format(word,keyword_name))
            self.engine.register_entity(word, keyword_name)
        return keyword_name

    def add_intents(self, intents):
        for intent in intents:
            # print("Adding intent {}".format(intent))
            # this prevents collisions between intents
            intent_base = intent
            intent_inc = 0
            while intent in self.intent_map['intents']:
                intent_inc += 1
                intent = "{}{}".format(intent_base, intent_inc)
            if('keywords' in intents[intent_base]):
                for keyword in intents[intent_base]['keywords']:
                    keyword_token = "{}_{}".format(intent,keyword)
                    self.keywords[keyword_token]={
                        'words': intents[intent_base]['keywords'][keyword],
                        'name': keyword
                    }
            if('regex' in intents[intent_base]):
                for regex_name in intents[intent_base]['regex']:
                    regex_token = "{}_{}".format(intent,regex_name)
                    self.regex[regex_token]=[]
                    for regex in intents[intent_base]['regex'][regex_name]:
                        self.regex[regex_token].append(regex.replace(regex_name, regex_token))
                # pprint(self.regex)
            self.intent_map['intents'][intent] = {
                'action': intents[intent_base]['action'],
                'name': intent_base,
                'templates': [],
                'words': {}
            }
            for phrase in intents[intent_base]['templates']:
                # Save the phrase so we can search for undefined keywords
                self.intent_map['intents'][intent]['templates'].append(phrase)
                # Make a count of word frequency. The fact that small connector
                # type words sometimes appear multiple times in a single
                # sentence while the focal words usually only appear once is
                # giving too much weight to those connector words.
                words = list(set(phrase.split()))
                for word in words:
                    if not is_keyword(word):
                        word = word.upper()
                    # Count the number of times the word ap
                    try:
                        self.intent_map['intents'][intent]['words'][word]['count'] += 1
                    except KeyError:
                        self.intent_map['intents'][intent]['words'][word] = {'count': 1, 'weight': None, 'required': False}
                    # A
                    try:
                        self.words[word].update({intent: True})
                    except KeyError:
                        self.words[word]={intent: True}
            # for each word in each intent, divide the word frequency by the number of examples.
            # Since a word is only counted once per example, regardless of how many times it appears,
            # if the number of times it was counted matches the number of examples, then
            # this is a "required" word.
            phrase_count = len(intents[intent_base]['templates'])
            for word in self.intent_map['intents'][intent]['words']:
                # print("Word: '{}' Count: {} Phrases: {} Weight: {}".format(word, self.intent_map['intents'][intent]['words'][word], phrase_count, weight(self.intent_map['intents'][intent]['words'][word], phrase_count)))
                Weight = weight(self.intent_map['intents'][intent]['words'][word]['count'], phrase_count)
                self.intent_map['intents'][intent]['words'][word]['weight'] = Weight
                if Weight == 1:
                    self.intent_map['intents'][intent]['words'][word]['required'] = True

    # Call train after loading all the intents.
    def train(self):
        # print("Words:")
        # pprint(self.words)
        # print("")
        # print("Intents:")
        # pprint(self.intent_map['intents'])
        # print("Keywords:")
        # pprint(self.keywords)
        for intent in self.intent_map['intents']:
            required_words = []
            optional_words = []
            # print("Training {}".format(intent))
            # pprint(self.keywords)
            for word in self.intent_map['intents'][intent]['words']:
                weight = self.intent_map['intents'][intent]['words'][word]
                intents_count = len(self.intent_map['intents'])
                word_appears_in = len(self.words[word])
                # print("Word: {} Weight: {} Intents: {} Appears in: {}".format(word, weight, intents_count, word_appears_in))
                self.intent_map['intents'][intent]['words'][word]['weight'] = self.intent_map['intents'][intent]['words'][word]['weight'] * (intents_count - word_appears_in) / intents_count
                word_token = "{}_{}".format(intent, word)
                if(self.intent_map['intents'][intent]['words'][word]['required']):
                    # add the word as required.
                    # print("adding '{}' as required".format(word_token))
                    required_words.append(self.add_word(intent,word))
                else:
                    # if the word is a keyword list, add it
                    if(word[:1] + word[-1:] == "{}"):
                        optional_words.append(self.add_word(intent,word))
                    else:
                        if(self.intent_map['intents'][intent]['words'][word]['weight'] > 0.35):
                            # print("adding '{}' as optional".format(word_token))
                            optional_words.append(self.add_word(intent,word))
            a=IntentBuilder(intent)
            for keyword in required_words:
                # print("Required word: {}".format(keyword))
                a=a.require(keyword)
            for keyword in optional_words:
                # print("Optional word: {}".format(keyword))
                a=a.optionally(keyword)
            if(a):
                # print("Building {}".format(intent))
                self.engine.register_intent_parser(a.build())
        # pprint(self.intent_map['intents'])
        # print("")
        self.trained = True

    def get_plugin_phrases(self, passive_listen):
        phrases = []
        # include the keyword, otherwise
        if(passive_listen):
            phrases = [profile.get(["keyword"])]
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

        # for plugin in self._plugins:
        #     phrases.extend(plugin.get_phrases())
        # print("**************************************************************")
        # pprint(self._intentparser)
        # pprint(self._intentparser.keywords)
        # print("**************************************************************")
        for word in self.words:
            if("{}{}".format(word[:1], word[-1:]) == "{}"):
                # read in the associated list
                for keyword in self.keywords:
                    for word in self.keywords[keyword]:
                        phrases.append(word)
            else:
                phrases.append(word)

        return sorted(list(set(phrases)))

    def determine_intent(self, phrase):
        response = {}
        try:
            for intent in self.engine.determine_intent(phrase):
                if intent and intent.get("confidence")>0:
                    keywords = {}
                    for keyword in intent:
                        if keyword not in ['confidence','intent_type','target']:
                            if keyword in self.keywords:
                                # Since the Naomi parser can return a list of matching words,
                                # this needs to be a list
                                keywords[self.keywords[keyword]['name']] = [intent[keyword]]
                    response.update(
                        {
                            self.intent_map['intents'][intent['intent_type']]['name']: {
                                'action': self.intent_map['intents'][intent['intent_type']]['action'],
                                'input': phrase,
                                'matches': keywords,
                                'score': intent['confidence']
                            }
                        }
                    )
        except ZeroDivisionError:
            print("Could not determine an intent")
        return response
