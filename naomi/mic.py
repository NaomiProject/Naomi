# -*- coding: utf-8 -*-
from datetime import datetime
from naomi.commandline import println
from naomi import alteration
from naomi import app_utils
from naomi import paths
from naomi import profile
import audioop
import contextlib
import logging
import os
import sqlite3
import tempfile
import threading
import time
import wave


# global queue
queue = []


class Mic(object):
    """
    The Mic class handles all interactions with the microphone and speaker.
    """
    current_thread = None

    def __init__(
        self,
        input_device,
        output_device,
        active_stt_reply,
        active_stt_response,
        passive_stt_engine,
        active_stt_engine,
        special_stt_slug,
        plugins,
        tts_engine,
        vad_plugin,
        keyword=['NAOMI'],
        print_transcript=False,
        passive_listen=False,
        save_audio=False,
        save_passive_audio=False,
        save_active_audio=False,
        save_noise=False
    ):
        self._logger = logging.getLogger(__name__)
        self._keyword = keyword
        self.tts_engine = tts_engine
        self.passive_stt_engine = passive_stt_engine
        self.active_stt_engine = active_stt_engine
        self.special_stt_slug = special_stt_slug
        self.plugins = plugins
        self._input_device = input_device
        self._output_device = output_device
        self._vad_plugin = vad_plugin
        self._active_stt_reply = active_stt_reply
        self._active_stt_response = active_stt_response
        self.passive_listen = passive_listen
        # transcript for monitoring
        self._print_transcript = print_transcript
        # audiolog for training
        if(save_audio):
            self._save_passive_audio = True
            self._save_active_audio = True
            self._save_noise = True
        else:
            self._save_passive_audio = save_passive_audio
            self._save_active_audio = save_active_audio
            self._save_noise = save_noise
        if(
            (
                self._save_active_audio
            )or(
                self._save_passive_audio
            )or(
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
        if(
            (
                sample_type.lower() == "noise" and self._save_noise
            )or(
                sample_type.lower() == "passive" and self._save_passive_audio
            )or(
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
            except:
                self._logger.info("intent column exists")
            try:
                c.execute("alter table audiolog add column score")
                self._conn.commit()
            except:
                self._logger.info("score column exists")
            try:
                c.execute("alter table audiolog add column verified_intent")
                self._conn.commit()
            except:
                self._logger.info("verified_intent column exists")
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
                        "datetime,",
                        "engine,",
                        "filename,",
                        "type,",
                        "transcription,",
                        "verified_transcription,",
                        "speaker,",
                        "reviewed,",
                        "wer",
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

    def wait_for_keyword(self, keyword=None):
        if not keyword:
            keyword = self._keyword
        while True:
            with self._write_frames_to_file(
                self._vad_plugin.get_audio(),
                self.passive_stt_engine._samplerate,
                self.passive_stt_engine._volume_normalization
            ) as f:
                try:
                    transcribed = self.passive_stt_engine.transcribe(f)
                except Exception:
                    dbg = (self._logger.getEffectiveLevel() == logging.DEBUG)
                    self._logger.error(
                        "Passive transcription failed!",
                        exc_info=dbg
                    )
                else:
                    if(len(transcribed)):
                        if(self._print_transcript):
                            println("<  {}\n".format(transcribed))
                            self._log_audio(f, transcribed, "passive")
                        if any([
                            word.lower() in t.lower()
                            for word in keyword
                            for t in transcribed if t
                        ]):
                            if(self.passive_listen):
                                # Take the same block of audio and put it
                                # through the active listener
                                f.seek(0)
                                try:
                                    transcribed = self.active_stt_engine.transcribe(f)
                                except Exception:
                                    dbg = (self._logger.getEffectiveLevel() == logging.DEBUG)
                                    self._logger.error("Active transcription failed!", exc_info=dbg)
                                else:
                                    if(self._print_transcript):
                                        println("<< {}\n".format(transcribed))
                                    if(self._save_active_audio):
                                        self._log_audio(f, transcribed, "active")
                                return transcribed
                            else:
                                return False
                    else:
                        if(self._print_transcript):
                            println("<  <noise>\n")
                            self._log_audio(f, "", "noise")

    def active_listen(self, timeout=3):
        transcribed = []
        # let the user know we are listening
        if self._active_stt_reply:
            self.say(self._active_stt_reply)
        else:
            self._logger.debug("No text to respond with using beep")
            if(self._print_transcript):
                println(">> <beep>\n")
            self.play_file(paths.data('audio', 'beep_hi.wav'))
        with self._write_frames_to_file(
            self._vad_plugin.get_audio(),
            self.active_stt_engine._samplerate,
            self.active_stt_engine._volume_normalization
        ) as f:
            if self._active_stt_response:
                self.say(self._active_stt_response)
            else:
                self._logger.debug("No text to respond with using beep")
                if(self._print_transcript):
                    println(">> <boop>\n")
                self.play_file(paths.data('audio', 'beep_lo.wav'))
            try:
                transcribed = self.active_stt_engine.transcribe(f)
            except Exception:
                dbg = (self._logger.getEffectiveLevel() == logging.DEBUG)
                self._logger.error("Active transcription failed!", exc_info=dbg)
            else:
                if(self._print_transcript):
                    println("<< {}\n".format(transcribed))
                if(profile.get_arg("save_active_audio", False)):
                    self._log_audio(f, transcribed, "active")
        return transcribed

    def listen(self):
        if(self.passive_listen):
            self._logger.info("[passive_listen]")
            return self.wait_for_keyword(self._keyword)
        else:
            self.wait_for_keyword(self._keyword)
            return self.active_listen()

    # Output methods
    def play_file(self, filename):
        global queue
        with open(filename, 'rb') as f:
            queue.append(f.read())
        if(hasattr(self.current_thread, "is_alive")):
            if self.current_thread.is_alive():
                # if Naomi is currently talking, then we are done
                return
        # otherwise, start talking
        self.current_thread = threading.Thread(
            target=self.say_thread
        )
        self.current_thread.start()

    # Stop talking and delete the queue
    def stop(self):
        global queue
        print("stopping...")
        if(hasattr(self, "current_thread")):
            try:
                queue = []
                # Threads can't be terminated
                # but we can set a "stop" attribute on self._output_device
                self._output_device.stop = 1
            except AttributeError:
                # current_thread can't be terminated
                self._logger.info("Can't terminate thread")
        self._logger.info("Stopped")

    def say(self, phrase):
        if(self._print_transcript):
            println(">> {}\n".format(phrase))
        if(profile.get_arg('listen_while_talking', False)):
            self.say_async(phrase)
        else:
            self.say_sync(phrase)

    def say_async(self, phrase):
        global queue
        altered_phrase = alteration.clean(phrase)
        queue.append(self.tts_engine.say(altered_phrase))
        if(hasattr(self.current_thread, "is_alive")):
            if self.current_thread.is_alive():
                # if Naomi is currently talking, then we are done
                return
        # otherwise, start talking
        self.current_thread = threading.Thread(
            target=self.say_thread
        )
        self.current_thread.start()

    def say_sync(self, phrase):
        altered_phrase = alteration.clean(phrase)
        with tempfile.SpooledTemporaryFile() as f:
            f.write(self.tts_engine.say(altered_phrase))
            f.seek(0)
            self._output_device.play_fp(f)

    def say_thread(self, *args, **kwargs):
        while(True):
            try:
                audio = queue.pop(0)
            except IndexError:
                return
            with tempfile.SpooledTemporaryFile() as f:
                f.write(audio)
                f.seek(0)
                self._output_device.play_fp(f)
                # Pause for 2/10 second before continuing
                time.sleep(.2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("stt").setLevel(logging.WARNING)
    audio = Mic.get_instance()
    while True:
        text = audio.listen()[0]
        if text:
            audio.say(text)
