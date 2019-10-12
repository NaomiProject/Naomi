# -*- coding: utf-8 -*-
import logging
import os
from . import paths
from . import profile


class Brain(object):
    def __init__(self, *args, **kwargs):
        """
        Instantiates a new Brain object, which cross-references user
        input with a list of modules. Note that the order of brain.modules
        matters, as the Brain will return the first module
        that accepts a given input.
        """

        self._plugins = []
        self._logger = logging.getLogger(__name__)

    def add_plugin(self, plugin):
        self._plugins.append(plugin)
        self._plugins = sorted(
            self._plugins,
            key=lambda p: p.get_priority(),
            reverse=True
        )

    def get_plugins(self):
        return self._plugins

    def get_standard_phrases(self):
        """
        Gets the standard phrases (i.e. phrases that occur frequently in
        normal conversations) from a file in the naomi data dir.

        Returns:
            A list of standard phrases.
        """
        language = profile.get(['language'], 'en-US')

        phrases = profile.get(['keyword'])

        # Get the contents of the
        # .naomi/data/standard_phrases/{language}.txt
        # file
        # The purpose of this file is to provide some
        # words that Naomi can recognize rather than only
        # recognizing wakeword. If the only word it knows
        # is the wake word, you will get a lot of false
        # positives.
        custom_standard_phrases_file = paths.sub(os.path.join(
            "data",
            "standard_phrases",
            "{}.txt".format(language)
        ))
        if(os.path.isfile(custom_standard_phrases_file)):
            with open(custom_standard_phrases_file, mode='r') as f:
                for line in f:
                    phrase = line.strip()
                    if phrase:
                        phrases.append(phrase)
        if(len(phrases) < 10):
            # Get the contents of the naomi/data/standard_phrases/{language}.txt
            # file. This file is built from words you actually say to Naomi
            # that are not the wakeword or in the plugin phrases.
            with open(paths.data('standard_phrases', "%s.txt" % language), mode="r") as f:
                for line in f:
                    phrase = line.strip()
                    if phrase:
                        phrases.append(phrase)
        return sorted(list(set(phrases)))

    def get_plugin_phrases(self, passive_listen=False):
        """
        Gets phrases from all plugins.

        Returns:
            A list of phrases from all plugins.
        """
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

        for plugin in self._plugins:
            phrases.extend(plugin.get_phrases())
        return sorted(list(set(phrases)))

    def get_all_phrases(self):
        """
        Gets a combined list consisting of standard phrases and plugin phrases.

        Returns:
            A list of phrases.
        """
        phrases = self.get_standard_phrases()
        phrases.extend(self.get_plugin_phrases())
        return sorted(list(set(phrases)))

    def query(self, texts):
        """
        Passes user input to the appropriate module, testing it against
        each candidate module's isValid function.

        Arguments:
        text -- user input, typically speech, to be parsed by a module

        Returns:
            A tuple containing a text and the module that can handle it
        """
        for plugin in self._plugins:
            for text in texts:
                if plugin.is_valid(text):
                    self._logger.debug(
                        "'{}' is a valid phrase for module '{}'".format(
                            text,
                            plugin.info.name
                        )
                    )
                    return (plugin, text)
        self._logger.debug(
            "No module was able to handle any of these phrases: {}".format(
                str(texts)
            )
        )
        return (None, None)
