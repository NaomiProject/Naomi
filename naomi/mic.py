# -*- coding: utf-8 -*-
import logging
import tempfile
import wave
import audioop
import contextlib

from . import alteration
from . import paths
from . import profile


class Mic(object):
    """
    The Mic class handles all interactions with the microphone and speaker.
    """

    def __init__(
        self,
        input_device,
        output_device,
        active_stt_reply,
        active_stt_response,
        passive_stt_engine,
        active_stt_engine,
        tts_engine,
        vad_plugin,
        config,
        keyword='NAOMI',
        print_transcript=False
    ):
        self._logger = logging.getLogger(__name__)
        self._keyword = keyword
        self.tts_engine = tts_engine
        self.passive_stt_engine = passive_stt_engine
        self.active_stt_engine = active_stt_engine
        self._input_device = input_device
        self._output_device = output_device
        self._vad_plugin = vad_plugin
        self._active_stt_reply = active_stt_reply
        self._active_stt_response = active_stt_response
        self._print_transcript = print_transcript

    @contextlib.contextmanager
    def special_mode(self, name, phrases):
        plugin_info = self.active_stt_engine.info
        plugin_config = self.active_stt_engine.profile

        original_stt_engine = self.active_stt_engine

        try:
            mode_stt_engine = plugin_info.plugin_class(
                name, phrases, plugin_info, plugin_config)
            self.active_stt_engine = mode_stt_engine
            yield
        finally:
            self.active_stt_engine = original_stt_engine

    @contextlib.contextmanager
    def _write_frames_to_file(self, frames, framerate, volume):
        with tempfile.NamedTemporaryFile(mode='w+b') as f:
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
                            print("<  {}".format(transcribed))
                        if any([
                            keyword.lower() in t.lower()
                            for t in transcribed if t
                        ]):
                            self._logger.debug("Passive listen: {}".format(profile.get_profile_flag(["passive_listen"])))
                            if(profile.get_profile_flag(["passive_listen"])):
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
                                        print("<< {}".format(transcribed))
                                return transcribed
                            else:
                                return False
                    else:
                        if(self._print_transcript):
                            print("<  <noise>")

    def active_listen(self, timeout=3):
        transcribed = []
        # let the user know we are listening
        if self._active_stt_reply:
            self.say(self._active_stt_reply)
        else:
            self._logger.debug("No text to respond with using beep")
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
                self.play_file(paths.data('audio', 'beep_lo.wav'))
            try:
                transcribed = self.active_stt_engine.transcribe(f)
            except Exception:
                dbg = (self._logger.getEffectiveLevel() == logging.DEBUG)
                self._logger.error("Active transcription failed!", exc_info=dbg)
            else:
                if(self._print_transcript):
                    print("<< {}".format(transcribed))
        return transcribed

    def listen(self):
        if(profile.get_profile_flag(["passive_listen"])):
            self._logger.info("[passive_listen]")
            return self.wait_for_keyword(self._keyword)
        else:
            self.wait_for_keyword(self._keyword)
            return self.active_listen()

    # Output methods
    def play_file(self, filename):
        self._output_device.play_file(
            filename,
            chunksize=self._output_device._output_chunksize,
            add_padding=self._output_device._output_padding
        )

    def say(self, phrase):
        if(self._print_transcript):
            print(">> {}".format(phrase))
        altered_phrase = alteration.clean(phrase)
        with tempfile.SpooledTemporaryFile() as f:
            f.write(self.tts_engine.say(altered_phrase))
            f.seek(0)
            self._output_device.play_fp(f)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("stt").setLevel(logging.WARNING)
    audio = Mic.get_instance()
    while True:
        text = audio.listen()[0]
        if text:
            audio.say(text)
