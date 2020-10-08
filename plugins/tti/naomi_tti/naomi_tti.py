# -*- coding: utf-8 -*-
import logging
import os
import re
from jiwer import wer
from naomi import paths
from naomi import plugin
from naomi import profile
# from pprint import pprint


# Replace the nth occurrance of sub
# based on an answer by aleskva at
# https://stackoverflow.com/questions/35091557/replace-nth-occurrence-of-substring-in-string
def replacenth(search_for, replace_with, string, n):
    try:
        # print("Searching for: '{}' in '{}'".format(search_for, string))
        # pprint([m.start() for m in re.finditer(search_for, string)])
        where = [m.start() for m in re.finditer(search_for, string)][n - 1]
        before = string[:where]
        # print("Before: {}".format(before))
        after = string[where:]
        # print("After: {}".format(after))
        after = after.replace(search_for, replace_with, 1)
        # print("After: {}".format(after))
        string = before + after
        # print("String: {}".format(string))
    except IndexError:
        # print("IndexError {}".format(n))
        pass
    return string


# is_keyword just checks to see if the word is a normal word or a keyword
# (surrounded by curly brackets)
def is_keyword(word):
    word = word.strip()
    response = False
    if("{}{}".format(word[:1], word[-1:]) == "{}"):
        response = True
    return response

# converts all non-keyword words to upper case in a template. This allows
# case insensitive matching.
def convert_template_to_upper(template):
    return " ".join([word if is_keyword(word) else word.upper() for word in template.split()])

class NaomiTTIPlugin(plugin.TTIPlugin):
    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger(__name__)

    def add_intents(self, intents):
        for intent in intents:
            # this prevents collisions between intents by different authors
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
            if(locale not in intents[intent_base]['locale']):
                raise KeyError("Language not supported")
            if('keywords' in intents[intent_base]['locale'][locale]):
                if intent not in self.keywords:
                    self.keywords[intent] = {}
                for keyword in intents[intent_base]['locale'][locale]['keywords']:
                    if keyword not in self.keywords[intent]:
                        self.keywords[intent][keyword] = []
                    self.keywords[intent][keyword].extend([word.upper() for word in intents[intent_base]['locale'][locale]['keywords'][keyword]])
            self.intent_map['intents'][intent] = {
                'action': intents[intent_base]['action'],
                'name': intent_base,
                'templates': [],
                'words': {}
            }
            for phrase in intents[intent_base]['locale'][locale]['templates']:
                # Save the phrase so we can search for undefined keywords
                # Convert the template to upper case
                phrase = convert_template_to_upper(phrase)
                self.intent_map['intents'][intent]['templates'].append(phrase)
                for word in phrase.split():
                    if not is_keyword(word):
                        word = word.upper()
                    # Make a list of words to ignore when building intents
                    # This should get better over time, but at the moment
                    # since we have so few intents, these common words are
                    # having a way oversized impact.
                    if(
                        word not in profile.get(
                            ['naomi_tti', 'words_to_ignore'],
                            ['ANY', 'ARE', 'DO', 'IN', 'IS', 'THE', 'TO', 'WHAT']
                        )
                    ):
                        try:
                            self.intent_map['intents'][intent]['words'][word] += 1
                        except KeyError:
                            self.intent_map['intents'][intent]['words'][word] = 1
                        # keep a list of the intents a word appears in
                        try:
                            self.words[word].update({intent: True})
                        except KeyError:
                            self.words[word] = {intent: True}
            # for each word in each intent, divide the word frequency by the
            # number of examples (this way words that are used frequently
            # get a higher weight, while those appearing in only one template
            # get a much lower weight.
            phrase_count = len(intents[intent_base]['locale'][locale]['templates'])
            for word in self.intent_map['intents'][intent]['words']:
                self.intent_map['intents'][intent]['words'][word] /= phrase_count
                self._logger.info("word {} appears {} times in {}: {}".format(word, phrase_count, intent, self.intent_map['intents'][intent]['words'][word]))

    def train(self):
        # Here we want to go through a list of all the words in all the intents
        # and get a count of the number of intents the word appears in, then
        # divide the weight of every instance by the number of intents it
        # appears in. That way a word that appears a lot (like "what") will
        # get a much lower weight
        wordcounts = {}
        for intent in self.intent_map['intents']:
            for word in self.intent_map['intents'][intent]['words']:
                if word in wordcounts:
                    wordcounts[word] += 1
                else:
                    wordcounts[word] = 1
        for word in wordcounts:
            if wordcounts[word] > 1:
                for intent in self.intent_map['intents']:
                    if word in self.intent_map['intents'][intent]['words']:
                        self.intent_map['intents'][intent]['words'][word] /= wordcounts[word]
                        self._logger.info("{} appears in {} intents: reduced to {} in {}".format(word, wordcounts[word], self.intent_map['intents'][intent]['words'][word], intent))
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

        # for plugin in self._plugins:
        #     phrases.extend(plugin.get_phrases())
        # print("**************************************************************")
        # pprint(self._intentparser)
        # pprint(self._intentparser.keywords)
        # print("**************************************************************")
        for word in self.words:
            if(is_keyword(word)):
                # read in the associated list
                for intent in self.keywords:
                    for keyword in self.keywords[intent]:
                        for word in self.keywords[intent][keyword]:
                            phrases.append(word)
            else:
                phrases.append(word)

        return sorted(list(set(phrases)))

    def determine_intent(self, phrase):
        phrase = phrase.upper()
        score = {}
        allvariants = {phrase: {}}
        for intent in self.keywords:
            variants = {phrase: {}}
            for keyword in self.keywords[intent]:
                for word in self.keywords[intent][keyword]:
                    count = 0  # count is the index of the match we are looking for
                    countadded = 0  # keep track of variants added for this count
                    while True:
                        added = 0  # if we get through all the variants without
                        # adding any new variants, then increase the count.
                        for variant in variants:
                            # print("Count: {} Added: {} CountAdded: {}".format(count, added, countadded))
                            # print()
                            # print("word: '{}' variant: '{}'".format(word,variant))
                            # subs is a list of substitutions
                            subs = dict(variants[variant])
                            # check and see if we can make a substitution and
                            # generate a new variant.
                            # print("replacenth('{}', '{}', '{}', {})".format(word, '{'+keyword+'}', variant, count))
                            new = replacenth(word, "{}{}{}".format('{', keyword, '}'), variant, count)
                            # print(new)
                            # print()
                            # print(new)
                            if new not in variants:
                                # print(new)
                                try:
                                    subs[keyword].append(word)
                                except KeyError:
                                    subs[keyword] = [word]
                                # print(subs[keyword])
                                # print()
                                variants[new] = subs
                                # pprint(variants)
                                added += 1
                                countadded += 1
                                # start looping over variants again
                                break
                        # check if we were able to loop over all the variants
                        # without creating any new ones
                        if added == 0:
                            if countadded == 0:
                                break
                            else:
                                count += 1
                                countadded = 0
            allvariants.update(variants)
        # Now calculate a total score for each variant
        variantscores = {}
        for variant in allvariants:
            # print("************VARIANT**************")
            # print(variant)
            variantscores[variant] = {}
            words = variant.split()
            intentscores = {}
            for intent in self.intent_map['intents']:
                score = 0
                # build up a score based on the words that match.
                for word in words:
                    if word in self.intent_map['intents'][intent]['words']:
                        intents_count = len(self.intent_map['intents'])
                        word_appears_in = len(self.words[word])
                        score += self.intent_map['intents'][intent]['words'][word] * (intents_count - word_appears_in) / intents_count
                # penalize the variant if it does not contain important words
                # highscore would be if the variant contains at least each of
                # the keywords
                highscore = sum(self.intent_map['intents'][intent]['words'].values())
                penalty = 0
                for word in self.intent_map['intents'][intent]['words']:
                    if word not in words:
                        penalty += self.intent_map['intents'][intent]['words'][word]
                intentscores[intent] = score * (highscore - penalty) / highscore
            # list intents and scores
            for intent in intentscores.keys():
                self._logger.info("\t{}: {}".format(intent, intentscores[intent]))
                # print("\t{}: {}".format(intent, intentscores[intent]))
            # Take the intent with the highest score
            # print("==========intentscores============")
            # pprint(intentscores)
            bestintent = max(intentscores, key=lambda key: intentscores[key])
            variantscores[variant] = {
                'intent': bestintent,
                'input': phrase,
                'score': intentscores[bestintent],
                'matches': allvariants[variant],
                'action': self.intent_map['intents'][bestintent]['action']
            }
        bestvariant = max(variantscores, key=lambda key: variantscores[key]['score'])
        # print("BEST: {}".format(bestvariant))
        # pprint(variantscores[bestvariant])
        # find the template with the smallest levenshtein distance
        templates = {}
        for template in self.intent_map['intents'][bestintent]['templates']:
            templates[template] = wer(template, variant)
            # print("distance from '{}' to '{}' is {}".format(variant,template,templates[template]))
        besttemplate = min(templates, key=lambda key: templates[key])
        # The next thing we have to do is match up all the substitutions
        # that have been made between the template and the current variant
        # This is so that if there are multiple match indicators we can eliminate
        # the ones that have matched.
        # Consider the following:
        #   Team: ['bengals','patriots']
        #   Template: will the {Team} play the {Team} {Day}
        #   Input: will done browns play the bengals today
        #   Input with matches: will done browns play the {Team} {Day}
        #   Matches: {Team: bengals, Day: today}
        # Obviously there is a very low Levenshtein distance between the template
        # and the input with matches, but it's not that easy to figure out which
        # Team in the template has been matched. So loop through the matches and
        # words and match the word with each possible location in the template
        # and take the best as the new template.
        #   Template1: will the bengals play the {Team} {Day}
        #   input: will done browns play the bengals {Day}
        #   distance: .42
        #
        #   Template2: will the {Team} play the bengals {Day}
        #   input: will done browns play the bengals {Day}
        #   distance: .28
        #
        # since we are looking for the smallest distance, Template2 is obviously
        # a better choice.
        # print("Best variant: {}".format(bestvariant))
        # print("Best template: {}".format(besttemplate))
        currentvariant = bestvariant
        currenttemplate = besttemplate
        for matchlist in variantscores[bestvariant]['matches']:
            for word in variantscores[bestvariant]['matches'][matchlist]:
                # Substitute word into the variant (we know this matches the
                # first occurrance of {matchlist})
                currentvariant = bestvariant.replace(
                    "{}{}{}".format('{', matchlist, '}'),
                    word,
                    1
                )
                # print("Bestvariant with substitutions: {}".format(currentvariant))
                templates = {}
                # Get a count of the number of matches for the
                # current matchlist in template
                possiblesubstitutions = currenttemplate.count(
                    '{}{}{}'.format('{', matchlist, '}')
                )
                # print("Matchlist: {} Word: {} Subs: {}".format(matchlist, word, possiblesubstitutions))
                # We don't actually know if there are actually any
                # substitutions in the template
                if(possiblesubstitutions > 0):
                    for i in range(possiblesubstitutions):
                        # print("replacenth('{}','{}','{}',{})".format(
                        #     '{}{}{}'.format('{', matchlist, '}'),
                        #     word,
                        #     currenttemplate,
                        #     i + 1
                        # ))
                        currenttemplate = replacenth(
                            '{}{}{}'.format('{', matchlist, '}'),
                            word,
                            currenttemplate,
                            i + 1
                        )
                        # print("CurrentTemplate = {}".format(currenttemplate))
                        templates[currenttemplate] = wer(
                            currentvariant,
                            currenttemplate
                        )
                    currenttemplate = min(
                        templates,
                        key=lambda key: templates[key]
                    )
                    # print(currenttemplate)
                # print("{}: {}".format(word,currenttemplate))
            # print("{}: {}".format(matchlist,currenttemplate))
        # Now that we have a matching template, run through a list of all
        # substitutions in the template and see if there are any we have not
        # identified yet.
        substitutions = re.findall(r'{(.*?)}', currenttemplate)
        # print("Substitutions: {}".format(substitutions))
        if(substitutions):
            for substitution in substitutions:
                subvar = "{}{}{}".format('{', substitution, '}')
                # print("Searching for {}".format(subvar))
                # So now we know that we are missing the variable contained
                # in substitution.
                # What we have to do now is figure out where in the string
                # to insert that variable in order to minimize the levenshtein
                # distance between bestvariant and besttemplate
                # print("Minimizing distance from '{}' to '{}' by substituting in '{}'".format(currentvariant,currenttemplate,subvar))
                # print("Variant: {}".format(currentvariant))
                variant = currentvariant.split()
                variant.append("<END>")
                # print("Template: {}".format(currenttemplate))
                template = currenttemplate.split()
                template.append("<END>")
                n = len(variant) + 1
                m = len(template) + 1
                # print("Variant: '{}' length: {}".format(variant,n))
                # print("Template: '{}' length: {}".format(template,m))
                # Find out which column contains the first instance of substitution
                s = template.index(subvar) + 1
                # print("subvar={} s={}".format(subvar,s))
                match = []
                a = []
                for i in range(n + 1):
                    a.append([1] * (m + 1))
                    a[i][0] = i
                for j in range(m + 1):
                    a[0][j] = j
                for i in range(1, n):
                    for j in range(1, m):
                        # print("{},{} V: {} T: {}".format(i,j,variant[i-1],template[j-1]))
                        if(variant[i - 1] == template[j - 1]):
                            c = 0
                        else:
                            c = 1
                        a[i][j] = c
                # pprint(a)
                # examine the resulting list of matched words
                # to locate the position of the unmatched keyword
                matched = ""
                for i in range(1, n - 1):
                    # print("i: {} s: {}".format(i,s))
                    if(a[i - 1][s - 1] == 0):
                        # the previous item was a match
                        # so start here and work to the right until there is another match
                        k = i
                        start = k
                        end = n - 1
                        compare = [k]
                        compare.extend([1] * (m))
                        # print(variant[k])
                        # print("Comparing {} to {}".format(a[k],compare))
                        while((a[k] == compare) and (k < (n))):
                            # print("k = {}".format(k))
                            match.append(variant[k - 1])
                            # print(match)
                            k += 1
                            compare = [k]
                            compare.extend([1] * (m))
                            # print("Comparing {} to {}".format(a[k],compare))
                            end = k
                        matched = " ".join(match)
                        # print("Variant:")
                        # pprint(variant)
                        # print("Start: {} End: {}".format(start,end))
                        substitutedvariant = variant[:start]
                        substitutedvariant.append(subvar)
                        substitutedvariant.extend(variant[end:])
                        # print("SubstitutedVariant: {}".format(substitutedvariant))
                        break
                    elif(a[i + 1][s + 1] == 0):
                        # the next item is a match, so start working backward
                        k = i
                        end = k
                        start = 0
                        compare = [k]
                        compare.extend([1] * (m))
                        # print("Comparing {} to {}".format(a[k],compare))
                        while(a[k] == compare):
                            match.append(variant[k - 1])
                            # print(match)
                            k -= 1
                            compare = [k]
                            compare.extend([1] * (m))
                            # print("Comparing {} to {}".format(a[k],compare))
                            start = k
                        matched = " ".join(reversed(match))
                        # print("Variant:")
                        # pprint(variant)
                        # print("Start: {} End: {}".format(start,end))
                        substitutedvariant = variant[:start]
                        substitutedvariant.append(subvar)
                        substitutedvariant.extend(variant[end:])
                        # print("SubstitutedVariant: {}".format(substitutedvariant))
                        break
                if(len(matched)):
                    # print("Match: '{}' to '{}'".format(substitution, matched))
                    try:
                        variantscores[bestvariant]['matches'][substitution].append(matched)
                    except KeyError:
                        variantscores[bestvariant]['matches'][substitution] = [matched]
        # variantscores[bestvariant]['template']=besttemplate
        return {
            self.intent_map['intents'][variantscores[bestvariant]['intent']]['name']: {
                'action': variantscores[bestvariant]['action'],
                'input': phrase,
                'matches': variantscores[bestvariant]['matches'],
                'score': variantscores[bestvariant]['score']
            }
        }
