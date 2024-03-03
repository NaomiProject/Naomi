# -*- coding: utf-8 -*-
import logging
from naomi import paths
from naomi import mic
from naomi import visualizations


# global action queue
queue = []


class MicSynchronous(mic.Mic):
    """
    The Mic class handles all interactions with the microphone and speaker.
    """
    def active_listen(self, play_prompts=True):
        """
        Active listen does not check for a wakeword.
    `   It should only be used in cases where Naomi has just asked a question.
        """
        transcribed = []
        if play_prompts:
            # let the user know we are listening
            if self._active_stt_reply:
                self.say(self._active_stt_reply)
            else:
                self._logger.debug("No text to respond with using beep")
                visualizations.run_visualization("output", ">> <beep>")
                self.play_file(paths.data('audio', 'beep_hi.wav'))
        audio = self.vad_plugin.get_audio()
        with self._write_frames_to_file(
            audio
        ) as f:
            if play_prompts:
                if self._active_stt_response:
                    self.say(self._active_stt_response)
                else:
                    self._logger.debug("No text to respond with using beep")
                    visualizations.run_visualization("output", ">> <boop>")
                    self.play_file(paths.data('audio', 'beep_lo.wav'))
            try:
                transcribed = [word.upper() for word in self.active_stt_plugin.transcribe(f)]
            except Exception:
                transcribed = []
                dbg = (self._logger.getEffectiveLevel() == logging.DEBUG)
                self._logger.error("Active transcription failed!", exc_info=dbg)
            else:
                if transcribed:
                    visualizations.run_visualization(
                        "output",
                        "<< {}".format(transcribed)
                    )
                    self._log_audio(f, transcribed, "active")
                else:
                    visualizations.run_visualization("output", "<< <noise>")
                    self._log_audio(f, transcribed, "noise")
        return transcribed, audio

    def listen(self):
        """
        Listen for a request
        """
        transcription = []
        audio = self.vad_plugin.get_audio()
        with self._write_frames_to_file(
            audio
        ) as f:
            passive_transcription = [word.upper() for word in self.passive_stt_plugin.transcribe(f)]
            if len(passive_transcription):
                visualizations.run_visualization(
                    "output",
                    f"<  {passive_transcription}"
                )
                keywords_detected = self.check_for_keyword(passive_transcription, self.keywords)
                if len(keywords_detected):
                    if self.passive_listen:
                        # If passive listen, then just use the same audio with the active stt engine
                        active_transcription = self.active_stt_plugin.transcribe(f)
                        if self.verify_wakeword:
                            # Check if any of the same wakewords are heard by the active stt engine
                            if self.check_for_keyword(active_transcription, keywords_detected):
                                transcription = active_transcription
                        else:
                            transcription = active_transcription
                        if transcription:
                            visualizations.run_visualization(
                                "output",
                                f"<< {transcription}"
                            )
                            self._log_audio(f, transcription, "active")
                        else:
                            visualizations.run_visualization(
                                "output",
                                "<< <noise>"
                            )
                            self._log_audio(f, transcription, "noise")
                    else:
                        transcription, audio = self.active_listen()
                else:
                    visualizations.run_visualization(
                        "output",
                        "<< <noise>"
                    )
                    self._log_audio(f, transcription, "noise")
            else:
                visualizations.run_visualization(
                    "output",
                    "<  <noise>"
                )
        return transcription, audio


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("stt").setLevel(logging.WARNING)
    audio = MicSynchronous.get_instance()
    while True:
        text = audio.listen()[0]
        if text:
            audio.say(text)
