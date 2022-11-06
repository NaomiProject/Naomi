# -*- coding: utf-8 -*-
from datetime import datetime
from naomi import alteration
from naomi import paths
from naomi import profile
from naomi import visualizations
import audioop
import contextlib
import logging
import os
import sqlite3
import sys
import tempfile
import threading
import time
import wave


# global action queue
queue = []


class Unexpected(Exception):
    def __init__(
        self,
        utterance
    ):
        self.utterance = utterance


class Mic(object):
    """
    The Mic class handles all interactions with the microphone and speaker.
    """
    current_thread = None

    def __init__(
        self
    ):
        self._logger = logging.getLogger(__name__)
        keyword = profile.get_profile_var(['keyword'], ['NAOMI'])
        if isinstance(keyword, str):
            keyword = [keyword]
        self._keyword = keyword
        self.tts_engine = profile.get_arg('tts_plugin')
        self.sr_engine = profile.get_arg('sr_plugin')
        self.passive_stt_engine = profile.get_arg('passive_stt_plugin')
        self.active_stt_engine = profile.get_arg('active_stt_plugin')
        self.special_stt_slug = profile.get_arg('special_stt_slug')
        self.plugins = profile.get_arg('plugins')
        self._input_device = profile.get_arg('input_device')
        self._output_device = profile.get_arg('output_device')
        self._vad_plugin = profile.get_arg('vad_plugin')
        self._active_stt_reply = profile.get_arg('active_stt_reply')
        self._active_stt_response = profile.get_arg('active_stt_response')
        self.passive_listen = profile.get_arg('passive_listen')
        # transcript for monitoring
        self._print_transcript = profile.get_arg('print_transcript')
        # audiolog for training
        if(profile.get_arg('save_audio', False)):
            self._save_passive_audio = True
            self._save_active_audio = True
            self._save_noise = True
        else:
            self._save_passive_audio = profile.get_arg('save_passive_audio', False)
            self._save_active_audio = profile.get_arg('save_active_audio', False)
            self._save_noise = profile.get_arg('save_noise', False)
        if(
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
            self._conn = sqlite3.connect(self._audiolog_db)

    # Copies a file pointed to by a file pointer to a permanent
    # file for training purposes
    def _log_audio(self, fp, transcription, sample_type="unknown"):
        # Any empty transcriptions are noise regardless of how they are being
        # collected
        if(" ".join(transcription) == ""):
            sample_type = 'noise'
        if(
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
            if(sample_type.lower() == "active"):
                engine = type(self.active_stt_engine).__name__
                if(self.active_stt_engine._vocabulary_name != "default"):
                    # we are in a special mode. We don't want to put words
                    # from this sample into the default standard_phrases
                    sample_type = self.active_stt_engine._vocabulary_name
            else:
                # noise (empty transcript) response is only from passive engine
                engine = type(self.passive_stt_engine).__name__
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
            c = self._conn.cursor()
            c.execute(" ".join([
                "create table if not exists audiolog(",
                "   datetime,",
                "   engine,",
                "   filename,",
                "   type,",
                "   transcription,",
                "   verified_transcription,",
                "   speaker,",
                "   reviewed,",
                "   wer",
                ")"
            ]))
            self._conn.commit()
            # Additional columns added
            try:
                c.execute("alter table audiolog add column intent")
                self._conn.commit()
            except sqlite3.OperationalError:
                self._logger.info("intent column exists")
            try:
                c.execute("alter table audiolog add column score")
                self._conn.commit()
            except sqlite3.OperationalError:
                self._logger.info("score column exists")
            try:
                c.execute("alter table audiolog add column verified_intent")
                self._conn.commit()
            except sqlite3.OperationalError:
                self._logger.info("verified_intent column exists")
            try:
                c.execute("alter table audiolog add column tti_engine")
                self._conn.commit()
            except sqlite3.OperationalError:
                self._logger.info("tti_engine column exists")
            c.execute(" ".join([
                "create table if not exists trainings(",
                "   datetime,",
                "   engine,",
                "   description",
                ")"
            ]))
            self._conn.commit()
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
                    " ".join(transcription)
                )
            )
            self._conn.commit()

    @contextlib.contextmanager
    def special_mode(self, name, phrases):
        plugin_info = self.plugins.get_plugin(
            self.special_stt_slug,
            category='stt'
        )
        plugin_config = profile.get_profile()

        original_stt_engine = self.active_stt_engine

        # If the special_mode engine is not specifically set,
        # copy the settings from the active stt engine.
        try:
            mode_stt_engine = plugin_info.plugin_class(
                name,
                phrases,
                plugin_info,
                plugin_config
            )
            if(profile.check_profile_var_exists(['special_stt'])):
                if(profile.check_profile_var_exists([
                    'special_stt',
                    'samplerate'
                ])):
                    mode_stt_engine._samplerate = int(
                        profile.get_profile_var([
                            'special_stt',
                            'samplerate'
                        ])
                    )
                if(profile.check_profile_var_exists([
                    'special_stt',
                    'volume_normalization'
                ])):
                    mode_stt_engine._volume_normalization = float(
                        profile.get_profile_var([
                            'special_stt',
                            'volume_normalization'
                        ])
                    )
            else:
                mode_stt_engine._samplerate = original_stt_engine._samplerate
                mode_stt_engine._volume_normalization = original_stt_engine._volume_normalization
            self.active_stt_engine = mode_stt_engine
            yield
        finally:
            self.active_stt_engine = original_stt_engine

    @contextlib.contextmanager
    def _write_frames_to_file(self, frames, framerate, volume):
        with tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix=".wav",
            prefix=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ) as f:
            wav_fp = wave.open(f, 'wb')
            wav_fp.setnchannels(self._input_device._input_channels)
            wav_fp.setsampwidth(int(self._input_device._input_bits / 8))
            wav_fp.setframerate(framerate)
            if self._input_device._input_rate == framerate:
                fragment = b''.join(frames)
            else:
                fragment = audioop.ratecv(
                    ''.join(frames),
                    int(self._input_device._input_bits / 8),
                    self._input_device._input_channels,
                    self._input_device._input_rate,
                    framerate,
                    None
                )[0]
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

    def check_for_keyword(self, phrase, keyword=None):
        if not keyword:
            keyword = self._keyword
        wakewords = [
            word.upper()
            for word in keyword
            for w in phrase if w
            if word.upper() in w.upper()
        ]
        if any(wakewords):
            return True
        return False

    def wait_for_keyword(self, keyword=None):
        if not keyword:
            keyword = self._keyword
        while not profile.get_arg("resetmic"):
            transcribed = []
            with self._write_frames_to_file(
                self._vad_plugin.get_audio(),
                self.passive_stt_engine._samplerate,
                self.passive_stt_engine._volume_normalization
            ) as f:
                try:
                    transcribed = [word.upper() for word in self.passive_stt_engine.transcribe(f)]
                except Exception:
                    transcribed = []
                    dbg = (self._logger.getEffectiveLevel() == logging.DEBUG)
                    self._logger.error(
                        "Passive transcription failed!",
                        exc_info=dbg
                    )
                else:
                    if(len(transcribed)):
                        if(self._print_transcript):
                            visualizations.run_visualization(
                                "output",
                                f"<  {transcribed}"
                            )
                        if self.check_for_keyword(transcribed, keyword):
                            self._log_audio(f, transcribed, "passive")
                            if(self.passive_listen):
                                # Take the same block of audio and put it
                                # through the active listener
                                f.seek(0)
                                try:
                                    sr_output = self.sr_engine.recognize_speaker(f, self.active_stt_engine)
                                except Exception:
                                    sr_output = {
                                        'speaker': None,
                                        'confidence': 0,
                                        'utterance': []
                                    }
                                    dbg = (self._logger.getEffectiveLevel() == logging.DEBUG)
                                    self._logger.error("Active transcription failed!", exc_info=dbg)
                                else:
                                    if(" ".join(sr_output['utterance']).strip() == ""):
                                        if(self._print_transcript):
                                            visualizations.run_visualization("output", "<< <noise>")
                                        self._log_audio(f, sr_output, "noise")
                                    else:
                                        if(self._print_transcript):
                                            visualizations.run_visualization(
                                                "output",
                                                "<< {} ({})".format(
                                                    sr_output['utterance'],
                                                    sr_output['speaker']
                                                )
                                            )
                                        self._log_audio(f, sr_output['utterance'], "active")
                                if(profile.get_profile_flag(['passive_stt', 'verify_wakeword'], False)):
                                    # Check if any of the wakewords identified by
                                    # the passive stt engine appear in the active
                                    # transcript
                                    if self.check_for_keyword(sr_output['utterance'], keyword):
                                        return sr_output
                                    else:
                                        self._logger.info('Wakeword not matched in active transcription')
                                else:
                                    return sr_output
                            else:
                                if(profile.get_profile_flag(['passive_stt', 'verify_wakeword'], False)):
                                    sr_output = self.sr_engine.recognize_speaker(f, self.active_stt_engine)
                                    transcribed = [word.upper() for word in sr_output['utterance']]
                                    if self.check_for_keyword(sr_output['utterance'], keyword):
                                        return sr_output
                                    else:
                                        self._logger.info('Wakeword not matched in active transcription')
                                else:
                                    return sr_output
                        else:
                            self._log_audio(f, transcribed, "noise")
                    else:
                        if(self._print_transcript):
                            visualizations.run_visualization("output", "<  <noise>")
                            self._log_audio(f, "", "noise")
        return False

    def active_listen(self, play_prompts=True):
        if(play_prompts):
            # let the user know we are listening
            if self._active_stt_reply:
                self.say(self._active_stt_reply)
            else:
                self._logger.debug("No text to respond with using beep")
                if(self._print_transcript):
                    visualizations.run_visualization("output", ">> <beep>")
                self.play_file(paths.data('audio', 'beep_hi.wav'))
        with self._write_frames_to_file(
            self._vad_plugin.get_audio(),
            self.active_stt_engine._samplerate,
            self.active_stt_engine._volume_normalization
        ) as f:
            if(play_prompts):
                if self._active_stt_response:
                    self.say(self._active_stt_response)
                else:
                    self._logger.debug("No text to respond with using beep")
                    if(self._print_transcript):
                        visualizations.run_visualization("output", ">> <boop>")
                    self.play_file(paths.data('audio', 'beep_lo.wav'))
            try:
                sr_output = self.sr_engine.recognize_speaker(f, self.active_stt_engine)
            except Exception:
                sr_output = {
                    'speaker': None,
                    'confidence': 0,
                    'utterance': []
                }
                dbg = (self._logger.getEffectiveLevel() == logging.DEBUG)
                self._logger.error("Active transcription failed!", exc_info=dbg)
            else:
                if(" ".join(sr_output['utterance']).strip() == ""):
                    if(self._print_transcript):
                        visualizations.run_visualization("output", "<< <noise>")
                    self._log_audio(f, sr_output, "noise")
                else:
                    if(self._print_transcript):
                        visualizations.run_visualization(
                            "output",
                            "<< {} ({})".format(
                                sr_output['utterance'],
                                sr_output['speaker']
                            )
                        )
                    self._log_audio(f, sr_output, "active")
        return sr_output

    def listen(self):
        if(self.passive_listen):
            return self.wait_for_keyword(self._keyword)
        else:
            kw = self.wait_for_keyword(self._keyword)
            # wait_for_keyword normally returns either a list of key
            if isinstance(kw, bool):
                if(not kw):
                    return {
                        'speaker': None,
                        'confidence': 0,
                        'utterance': []
                    }
            # if not in passive_listen mode, then the user has tried to
            # interrupt, go ahead and stop talking
            self.stop(wait=True)
            return self.active_listen()

    # If we are using the asynchronous say, so we can hear the "stop"
    # command, what we want to do is put the prompt on the queue, then
    # yield control back to the main conversation loop. When the prompt
    # is spoken in the thread, then we want to return to this point in
    # the main thread and use the blocking listen to listen until we get
    # an actual transcription. That should then be used to determine
    # whether the user responded with one of the expected phrases or not.
    def expect(self, prompt, phrases, name='expect', instructions=None):
        expected_phrases = phrases.copy()
        phrases.extend(
            profile.get_arg("application").brain.get_plugin_phrases(True)
        )
        # set up the special mode so it is pre-generated later
        with self.special_mode(name, phrases):
            pass
        # If "listen_while_talking" is set to true, then we want to create the
        # special mode after saying the prompt. If not, then we want to create
        # the special mode first, so we are ready to listen. Also, there is no
        # need to add anything to the queue if we are not listening while
        # talking.
        if(profile.get_arg('listen_while_talking', False)):
            self.say(prompt)
            self.add_queue(lambda: profile.set_arg('resetmic', True))
            # Now wait for any sounds in the queue to be processed
            while not profile.get_arg('resetmic'):
                sr_output = self.listen()
                handled = False
                if isinstance(sr_output['utterance'], bool):
                    handled = True
                else:
                    while(" ".join(sr_output['utterance']) != "" and not handled):
                        sr_output, handled = profile.get_arg('application').conversation.handleRequest(sr_output)
            # Now that we are past the mic reset
            profile.set_arg('resetmic', False)
        else:
            self.say(prompt)
        # Now start listening for a response
        with self.special_mode(name, phrases):
            while True:
                sr_output = self.active_listen()
                if(len(' '.join(sr_output['utterance']))):
                    # Now that we have a transcription, check if it matches one of the phrases
                    phrase, score = profile.get_arg("application").brain._intentparser.match_phrase(sr_output['utterance'], expected_phrases)
                    # If it does, then return the phrase
                    self._logger.info("Expecting: {} Got: {}".format(expected_phrases, sr_output['utterance']))
                    self._logger.info("Score: {}".format(score))
                    if(score > .1):
                        return phrase
                    # Otherwise, raise an exception with the active transcription.
                    # This will break us back into the main conversation loop
                    else:
                        # If the user is not responding to the prompt, then assume that
                        # they are starting a new command. This should mean that the wake
                        # word would be included.
                        if(self.check_for_keyword(sr_output['utterance'])):
                            raise Unexpected(sr_output['utterance'])
                        else:
                            # The user just said something unexpected. Remind them of their choices
                            if instructions is None:
                                profile.get_arg("application").conversation.list_choices(expected_phrases)
                            else:
                                self.say(instructions)

    # confirm is a special case of expect which expects "yes" or "no"
    def confirm(self, prompt):
        # default to english
        language = profile.get(['language'], 'en-US')[:2]
        POSITIVE = ['YES', 'SURE', 'YES PLEASE']
        NEGATIVE = ['NO', 'NOPE', 'NO THANK YOU']
        if(language == "fr"):
            POSITIVE = ['OUI']
            NEGATIVE = ['NON']
        elif(language == "de"):
            POSITIVE = ['JA']
            NEGATIVE = ['NEIN']
        phrase = self.expect(
            prompt,
            POSITIVE + NEGATIVE,
            name='confirm',
            instructions=profile.get_arg("application").conversation.gettext(
                "Please respond with Yes or No"
            )
        )
        if phrase in POSITIVE:
            return True
        else:
            return False

    # Output methods
    def play_file(self, filename):
        if(profile.get_arg('listen_while_talking', False)):
            self.play_file_async(filename)
        else:
            self.play_file_sync(filename)

    def play_file_async(self, filename):
        global queue
        queue.append(lambda: self.play_file_sync(filename))
        if(hasattr(self.current_thread, "is_alive")):
            if self.current_thread.is_alive():
                # if Naomi is currently talking, then we are done
                return
        # otherwise, start talking
        self.current_thread = threading.Thread(
            target=self.process_queue
        )
        self.current_thread.start()

    def play_file_sync(self, filename):
        with open(filename, 'rb') as f:
            self._output_device.play_fp(f)

    # Stop talking and delete the queue
    def stop(self, wait=False):
        global queue
        visualizations.run_visualization("output", "Stopping...")
        if(hasattr(self, "current_thread")):
            try:
                queue = []
                if(hasattr(self.current_thread, "is_alive")):
                    # Threads can't be terminated
                    # but we can set a "stop" attribute on self._output_device
                    self._output_device._stop = True
                    if(wait):
                        while not self._output_device._stop:
                            time.sleep(.1)
            except AttributeError:
                # current_thread can't be terminated
                self._logger.info("Can't terminate thread")
        self._logger.info("Stopped")

    def process_queue(self, *args, **kwargs):
        while(True):
            try:
                queue.pop(0)()
            except IndexError:
                sys.exit()

    def add_queue(self, action):
        global queue
        queue.append(action)
        if(hasattr(self.current_thread, "is_alive")):
            if self.current_thread.is_alive():
                # if Naomi is currently talking, then we are done
                return
        # otherwise, start talking
        self.current_thread = threading.Thread(
            target=self.process_queue
        )
        self.current_thread.start()

    def say(self, phrase):
        altered_phrase = alteration.clean(phrase)
        if(profile.get_arg('listen_while_talking', False)):
            self.say_async(altered_phrase)
        else:
            self.say_sync(altered_phrase)

    def say_async(self, phrase):
        self.add_queue(lambda: self.say_sync(phrase))
        if(hasattr(self.current_thread, "is_alive")):
            if self.current_thread.is_alive():
                # if Naomi is currently talking, then we are done
                return
        # otherwise, start talking
        self.current_thread = threading.Thread(
            target=self.process_queue
        )
        self.current_thread.daemon = True
        self.current_thread.start()

    def say_sync(self, phrase):
        if(profile.get_arg('print_transcript')):
            visualizations.run_visualization("output", ">> {}\n".format(phrase))
        with tempfile.SpooledTemporaryFile() as f:
            f.write(self.tts_engine.say(phrase))
            f.seek(0)
            self._output_device.play_fp(f)
            time.sleep(.2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("stt").setLevel(logging.WARNING)
    audio = Mic.get_instance()
    while True:
        text = audio.listen()[0]
        if text:
            audio.say(text)
