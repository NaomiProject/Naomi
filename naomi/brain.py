# -*- coding: utf-8 -*-
import logging
import os
import sqlite3
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
        self._intentparser = args[0]

    def add_plugin(self, plugin):
        self._plugins.append(plugin)
        # print("Checking {} for intents".format(plugin._plugin_info.name))
        if(hasattr(plugin, "intents")):
<<<<<<< HEAD
            # print("Found intents")
            # print(plugin)
            # print(dir(plugin))
=======
>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
            self._intentparser.add_intents(plugin.intents())

    def train(self):
        self._intentparser.train()

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

        keyword = profile.get(['keyword'])
        if isinstance(keyword, str):
            keyword = [keyword]
            profile.set_profile_var(['keyword'], keyword)
            profile.save_profile()

        phrases = keyword.copy()

        # Get the contents of the
        # .config/naomi/data/standard_phrases/{language}.txt
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
            with open(
                paths.data(
                    'standard_phrases',
                    "{}.txt".format(language)
                ),
                mode="r"
            ) as f:
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
        return self._intentparser.get_plugin_phrases(passive_listen)

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

        Note, this should be set up as a generator so that multiple intents
        can be returned. As it is, we are relying on the intent parser to
        pass the intents back in order of highest score to lowest.

        Arguments:
        text -- user input, typically speech, to be parsed by a module

        Returns:
            A tuple containing a text and the module that can handle it
        """
        for text in texts:
            intents = self._intentparser.determine_intent(text)
            for intent in intents:
                # Add the intent to the response so the handler method
                # can find out which intent activated it
                intents[intent]['intent'] = intent
<<<<<<< HEAD
=======
                if(profile.get_arg("print_transcript")):
                    print("{} {}".format(intent, intents[intent]['score']))
                if(profile.get_arg('save_active_audio')):
                    # Write the intent information to audiolog
                    # We don't actually know what record we are on, so
                    # just add the information to the most recent active
                    # record.
                    audiolog = paths.sub("audiolog")
                    audiolog_db = os.path.join(audiolog, "audiolog.db")
                    conn = sqlite3.connect(audiolog_db)
                    c = conn.cursor()
                    c.execute(
                        " ".join([
                            "update audiolog set",
                            "   intent = ?,",
                            "   score = ?,",
                            "   tti_engine = ?",
                            "where filename =(",
                            "   select filename",
                            "   from audiolog",
                            "   where datetime=(",
                            "       select max(datetime) from audiolog",
                            "   )",
                            ")"
                        ]),
                        (
                            intent,
                            intents[intent]['score'],
                            str(self._intentparser.__class__)
                        )
                    )
                    conn.commit()

>>>>>>> 4807170d0d65eecc9e80d62e2084e7482de024c8
                if intents[intent]['score'] > 0.05:
                    return(intents[intent])
            self._logger.debug(
                "No module was able to handle any of these phrases: {}".format(
                    str(texts)
                )
            )
            return (None)
