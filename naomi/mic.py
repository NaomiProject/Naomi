import abc
import audioop
import contextlib
import logging
import os
import random
import sqlite3
import tempfile
import time
import wave
from datetime import datetime
from naomi import i18n
from naomi import paths
from naomi import profile
from naomi import visualizations


class Unexpected(Exception):
    """
    The "Unexpected" class is an exception that is fired if the expect method
    recieves unexpected input. This allows the function to return control to
    the
    """
    def __init__(
        self,
        utterance
    ):
        self.utterance = utterance


class Utterance:
    def __init__(self, **kwargs):
        if ('transcription' in kwargs):
            if isinstance(kwargs['transcription'], list):
                self.transcription = " ".join(kwargs['transcription'])
            else:
                self.transcription = kwargs['transcription']
        else:
            self.transcription = ""
        if ('audio' in kwargs):
            self.audio = kwargs['audio']
        else:
            self.audio = b''

    def __repr__(self):
        if isinstance(self.transcription, list):
            return " ".join(self.transcription)
        else:
            return self.transcription


class Mic(i18n.GettextMixin):
    """
    Calling this class "Mic" seems like a misnomer since it handles both
    input and output. "MicAndSpeaker" might be a better name, or it might
    make sense to implement a separate "Speaker" class for things like
    say.
    """
    actions_thread = None
    Continue = True

    def __init__(self, *args, **kwargs):
        translations = i18n.parse_translations(paths.data('locale'))
        i18n.GettextMixin.__init__(self, translations, profile)
        self.keywords = kwargs['keywords']
        self._input_device = kwargs['input_device']
        self._output_device = kwargs['output_device']
        self.passive_stt_plugin = kwargs['passive_stt_plugin']
        self.active_stt_plugin = kwargs['active_stt_plugin']
        self.special_stt_slug = kwargs['special_stt_slug']
        self.vad_plugin = kwargs['vad_plugin']
        self.tts_engine = kwargs['tts_engine']
        self.brain = kwargs['brain']
        self._logger = logging.getLogger(__name__)
        self._save_passive_audio = profile.get_arg('save_passive_audio', False)
        self._save_active_audio = profile.get_arg('save_active_audio', False)
        self._save_noise = profile.get_arg('save_noise', False)
        self.passive_listen = profile.get_profile_flag(["passive_listen"], False)
        self.verify_keyword = profile.get_arg('verify_keyword', False)
        self._active_stt_reply = profile.get_arg("active_stt_reply")
        self._active_stt_response = profile.get_arg("active_stt_response")
        if (
            (
                self._save_active_audio
            ) or (
                self._save_passive_audio
            ) or (
                self._save_noise
            )
        ):
            self._audiolog = paths.sub("audiolog")
            self._logger.info(
                "Checking audio log directory %s" % self._audiolog
            )
            if not os.path.exists(self._audiolog):
                self._logger.info(
                    "Creating audio log directory %s" % self._audiolog
                )
                os.makedirs(self._audiolog)
            self._audiolog_db = os.path.join(self._audiolog, "audiolog.db")

    @abc.abstractmethod
    def listen(self):
        """
        Fetch the next utterance and check for wake word
        """
        pass

    @abc.abstractmethod
    def active_listen(self, play_prompts=True):
        """
        Fetch the next utterance without checking for wake word
        (to be used when Naomi asks a question)
        """
        pass

    def _log_audio(self, fp, transcription, sample_type="unknown"):
        """
        Copies a file pointed to by a file pointer to a permanent
        file for training purposes
        """
        # Any empty transcriptions are noise regardless of how they are being
        # collected
        if isinstance(transcription, list):
            transcription = " ".join(transcription)
        if transcription == "":
            sample_type = 'noise'
        if (
            (
                sample_type.lower() == "noise" and self._save_noise
            ) or (
                sample_type.lower() == "passive" and self._save_passive_audio
            ) or (
                sample_type.lower() == "active" and self._save_active_audio
            )
        ):
            fp.seek(0)
            # Get the slug from the engine
            if sample_type.lower() == "active":
                engine = type(self.active_stt_plugin).__name__
                if self.active_stt_plugin._vocabulary_name != "default":
                    # we are in a special mode. We don't want to put words
                    # from this sample into the default standard_phrases
                    sample_type = self.active_stt_plugin._vocabulary_name
            else:
                # noise (empty transcript) response is only from passive engine
                engine = type(self.passive_stt_plugin).__name__
            # Now, it is very possible that the file might already exist
            # since the same file could be used for both passive and active
            # parsing. Should we check to see if the file already exists
            # or just go ahead and write over it?
            filename = os.path.basename(fp.name)
            self._logger.info("Audiofile saved as: {}".format(
                os.path.join(self._audiolog, filename)
            ))
            with open(os.path.join(self._audiolog, filename), "wb") as f:
                f.write(fp.read())
            # Also add a line to the sqlite database
            conn = sqlite3.connect(self._audiolog_db)
            c = conn.cursor()
            c.execute(" ".join([
                "create table if not exists audiolog(",
                "   datetime,",
                "   engine,",
                "   filename,",
                "   type,",
                "   tti_engine,",
                "   transcription,",
                "   verified_transcription,",
                "   speaker,",
                "   reviewed,",
                "   intent,",
                "   verified_intent,",
                "   score,",
                "   wer",
                ")"
            ]))
            conn.commit()
            # Additional columns added
            try:
                c.execute("alter table audiolog add column intent")
                conn.commit()
            except sqlite3.OperationalError:
                self._logger.info("intent column exists")
            try:
                c.execute("alter table audiolog add column score")
                conn.commit()
            except sqlite3.OperationalError:
                self._logger.info("score column exists")
            try:
                c.execute("alter table audiolog add column verified_intent")
                conn.commit()
            except sqlite3.OperationalError:
                self._logger.info("verified_intent column exists")
            try:
                c.execute("alter table audiolog add column tti_engine")
                conn.commit()
            except sqlite3.OperationalError:
                self._logger.info("tti_engine column exists")
            c.execute(" ".join([
                "create table if not exists trainings(",
                "   datetime,",
                "   engine,",
                "   description",
                ")"
            ]))
            conn.commit()
            c.execute(
                " ".join([
                    "insert into audiolog(",
                    "   datetime,",
                    "   engine,",
                    "   filename,",
                    "   type,",
                    "   transcription,",
                    "   verified_transcription,",
                    "   speaker,",
                    "   reviewed,",
                    "   wer",
                    ")values(?,?,?,?,?,'','','','')"
                ]),
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    engine,
                    filename,
                    sample_type,
                    transcription
                )
            )
            conn.commit()

    @contextlib.contextmanager
    def _write_frames_to_file(self, frames, volume=None):
        """
        This is used internally to create an audio file
        """
        with tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix=".wav",
            prefix=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ) as f:
            wav_fp = wave.open(f, 'wb')
            wav_fp.setnchannels(self._input_device._input_channels)
            wav_fp.setsampwidth(int(self._input_device._input_bits / 8))
            wav_fp.setframerate(self._input_device._input_rate)
            fragment = b''.join(frames)
            if volume is not None:
                maxvolume = audioop.minmax(
                    fragment,
                    self._input_device._input_bits / 8
                )[1]
                fragment = audioop.mul(
                    fragment,
                    int(self._input_device._input_bits / 8),
                    volume * (2. ** 15) / maxvolume
                )

            wav_fp.writeframes(fragment)
            wav_fp.close()
            f.seek(0)
            yield f

    @contextlib.contextmanager
    def special_mode(self, name, phrases):
        plugin_info = profile.get_arg('plugins').get_plugin(
            self.special_stt_slug,
            category='stt'
        )
        plugin_config = profile.get_profile()

        original_stt_plugin = self.active_stt_plugin

        # If the special_mode engine is not specifically set,
        # copy the settings from the active stt engine.
        try:
            mode_stt_plugin = plugin_info.plugin_class(
                name,
                phrases,
                plugin_info,
                plugin_config
            )
            if (profile.check_profile_var_exists(['special_stt'])):
                if (profile.check_profile_var_exists([
                    'special_stt',
                    'samplerate'
                ])):
                    mode_stt_plugin._samplerate = int(
                        profile.get_profile_var([
                            'special_stt',
                            'samplerate'
                        ])
                    )
                if (profile.check_profile_var_exists([
                    'special_stt',
                    'volume_normalization'
                ])):
                    mode_stt_plugin._volume_normalization = float(
                        profile.get_profile_var([
                            'special_stt',
                            'volume_normalization'
                        ])
                    )
            else:
                mode_stt_plugin._samplerate = original_stt_plugin._samplerate
                mode_stt_plugin._volume_normalization = original_stt_plugin._volume_normalization
            self.active_stt_plugin = mode_stt_plugin
            yield
        finally:
            self.active_stt_plugin = original_stt_plugin

    def check_for_keyword(self, phrase, keywords=None):
        if isinstance(phrase, list):
            phrase = " ".join(phrase)
        if not keywords:
            keywords = self.keywords
        # This allows multi-word keywords like 'Hey Naomi' or 'You there'
        wakewords = []
        for word in keywords:
            if word.upper() in phrase.upper():
                wakewords.append(word.upper())
        return wakewords

    def handleRequest(self, utterance):
        """
        Respond to an utterance
        """
        handled = False
        if utterance.transcription:
            # brain.query is expecting an array of transcriptions, so
            # convert here.
            intent = self.brain.query([utterance.transcription])
            if intent:
                try:
                    self._logger.info(intent)
                    intent['action'](intent, self)
                    handled = True
                except Unexpected as e:
                    # The user responded to a prompt within the intent with a new
                    # request.
                    audio = e.utterance.audio
                    # If passive_listen is true, then use the same audio
                    # for the utterance
                    if (self.passive_listen):
                        # Because the user would have been using a special
                        # listener which may have only been trained to hear
                        # certain phrases, go back and run the same audio
                        # through the standard listener
                        with self._write_frames_to_file(audio) as f:
                            transcription = self.active_stt_plugin.transcribe(f)
                            utterance = Utterance(
                                transcription=transcription,
                                audio=audio
                            )
                    else:
                        # The user responded by saying the assistant's name
                        utterance = self.active_listen()
                    return self.handleRequest(utterance)
                except Exception as e:
                    self._logger.error(
                        'Failed to service intent {}: {}'.format(intent, str(e)),
                        exc_info=True
                    )
                    self.say(self.gettext("I'm sorry."))
                    self.say(self.gettext("I had some trouble with that operation."))
                    self.say(str(e))
                    self.say(self.gettext("Please try again later."))
                    handled = True
                else:
                    self._logger.debug(
                        " ".join([
                            "Handling of phrase '{}'",
                            "by plugin '{}' completed"
                        ]).format(
                            utterance.transcription,
                            intent
                        )
                    )
            else:
                self.say_i_do_not_understand()
                handled = True
        return utterance, handled

    def say_i_do_not_understand(self):
        """
        Handles a response where Naomi does not understand the intention
        """
        self.say(
            random.choice(
                [  # nosec
                    self.gettext("I'm sorry, could you repeat that?"),
                    self.gettext("My apologies, could you try saying that again?"),
                    self.gettext("Say that again?"),
                    self.gettext("I beg your pardon?"),
                    self.gettext("Pardon?")
                ]
            )
        )

    def list_choices(self, choices):
        """
        This method is used with the expect method and reminds the user of
        the available choices if the user said something unexpected.
        """
        if len(choices) == 1:
            self.say(self.gettext("Please say {}").format(choices[0]))
        elif len(choices) == 2:
            self.say(self.gettext("Please respond with {} or {}").format(choices[0], choices[1]))
        else:
            self.say(
                self.gettext("Please respond with one of the following: {}").format(choices)
            )

    def expect(self, prompt, phrases, name='expect', instructions=None):
        """
        The expect method has different implementations depending on whether
        it is synchronous or asynchronous. Most mics are synchronous, so I will
        implement it that way here and override this method in the
        MicAsynchronous class.
        """
        expected_phrases = phrases.copy()
        phrases.extend(
            self.brain.get_plugin_phrases(True)
        )
        # set up the special mode so it is pre-generated later
        with self.special_mode(name, phrases):
            pass
        self.say(prompt)
        # Now start listening for a response
        with self.special_mode(name, phrases):
            while True:
                utterance = self.active_listen()
                if len(utterance.transcription):
                    # Now that we have a transcription, check if it matches
                    # one of the phrases
                    phrase, score = self.brain._intentparser.match_phrase(
                        utterance.transcription,
                        expected_phrases
                    )
                    # If it does, then return the phrase
                    self._logger.info(
                        "Expecting: {} Got: {}".format(
                            expected_phrases,
                            utterance.transcription
                        )
                    )
                    self._logger.info("Score: {}".format(score))
                    if (score > .1):
                        return phrase
                    # Otherwise, raise an Unexpected exception
                    # This will break us back into the main conversation loop
                    else:
                        # If the user is not responding to the prompt, then
                        # assume that they are starting a new request. This
                        # should mean that the wake word would be included.
                        if (self.check_for_keyword(utterance.transcription)):
                            raise Unexpected(utterance)
                        else:
                            # The user just said something unexpected. Remind them of their choices
                            if instructions is None:
                                self.list_choices(expected_phrases)
                            else:
                                self.say(instructions)

    def confirm(self, prompt):
        """
        confirm is a special case of expect which expects "yes" or "no"
        """
        # default to english
        language = profile.get(['language'], 'en-US')[:2]
        POSITIVE = ['YES', 'SURE', 'YES PLEASE']
        NEGATIVE = ['NO', 'NOPE', 'NO THANK YOU']
        if (language == "fr"):
            POSITIVE = ['OUI']
            NEGATIVE = ['NON']
        elif (language == "de"):
            POSITIVE = ['JA']
            NEGATIVE = ['NEIN']
        phrase = self.expect(
            prompt,
            POSITIVE + NEGATIVE,
            name='confirm',
            instructions=self.gettext(
                "Please respond with Yes or No"
            )
        )
        if phrase in POSITIVE:
            return True
        else:
            return False

    def stop(self, wait=False):
        """
        Stop talking, delete the queue, run "stop" on any plugins that have
        a "stop" method
        """
        global queue
        visualizations.run_visualization("output", "Stopping...")
        if (hasattr(self, "current_thread")):
            try:
                queue = []
                if (hasattr(self.current_thread, "is_alive")):
                    # Threads can't be terminated
                    # but we can set a "stop" attribute on self._output_device
                    self._output_device._stop = True
                    if (wait):
                        while not self._output_device._stop:
                            time.sleep(.1)
            except AttributeError:
                # current_thread can't be terminated
                self._logger.info("Can't terminate thread")
        self._logger.info("Stopped")

    # Output methods
    def play_file(self, filename):
        with open(filename, 'rb') as f:
            self._output_device.play_fp(f)
            time.sleep(.5)

    def say(self, phrase):
        visualizations.run_visualization("output", ">> {}".format(phrase))
        with tempfile.SpooledTemporaryFile() as f:
            f.write(self.tts_engine.say(phrase))
            f.seek(0)
            self._output_device.play_fp(f)
            time.sleep(.5)

    def main_loop(self):
        """This is a synchronous main loop"""
        try:
            while self.Continue:
                # put the audio in a queue and call the stt engine
                utterance = self.listen()
                self.handleRequest(utterance)
        except KeyboardInterrupt:
            self.Continue = False
        visualizations.run_visualization(
            "output",
            "Exiting..."
        )

    # The following are no longer necessary and are just wrappers now.
    def say_sync(self, phrase):
        self.say(phrase)

    def say_async(self, phrase):
        self.say(phrase)
