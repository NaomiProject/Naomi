import collections
import random
import tempfile
import threading
import time
from naomi import alteration
from naomi import mic
from naomi import paths
from naomi import profile
from naomi import visualizations


recordings_available_event = threading.Event()


class MicAsynchronous(mic.Mic):
    actions_thread = None
    Continue = True

    def __init__(self, *args, **kwargs):
        mic.Mic.__init__(self, *args, **kwargs)
        self.recordings_queue = collections.deque([], maxlen=10)
        self.actions_queue = collections.deque([], maxlen=10)

    def queue_recording(self, audio):
        self.recordings_queue.appendleft(audio)
        recordings_available_event.set()

    def queue_action(self, action):
        self.actions_queue.appendleft(action)

    def listen(self):
        """Grab the next block of audio out of the queue and convert to text"""
        transcription = []
        audio = b''
        recordings_available_event.wait()
        try:
            audio = self.recordings_queue.pop()
            if len(audio) > 0:
                with self._write_frames_to_file(audio) as f:
                    passive_transcription = self.passive_stt_plugin.transcribe(f)

                    if len(passive_transcription) > 0:
                        visualizations.run_visualization(
                            "output",
                            f"<  {passive_transcription}"
                        )
                        if self.passive_listen:
                            if self.check_for_keyword(passive_transcription):
                                active_transcription = [" ".join(self.active_stt_plugin.transcribe(f))]
                                if len(active_transcription) > 0:
                                    if self.verify_keyword:
                                        if self.check_for_keyword(active_transcription):
                                            transcription = active_transcription
                                            if len(transcription) > 0:
                                                visualizations.run_visualization(
                                                    "output",
                                                    f"<< {transcription}"
                                                )
                                            else:
                                                visualizations.run_visualization(
                                                    "output",
                                                    "<< <noise>"
                                                )
                                        else:
                                            visualizations.run_visualization(
                                                "output",
                                                "<< <noise>"
                                            )
                                    else:
                                        # Don't verify keyword
                                        transcription = active_transcription
                                        if len(transcription) > 0:
                                            visualizations.run_visualization(
                                                "output",
                                                f"<< {transcription}"
                                            )
                                        else:
                                            visualizations.run_visualization(
                                                "output",
                                                "<< <noise>"
                                            )
                                else:
                                    visualizations.run_visualization(
                                        "output",
                                        "<< <noise>"
                                    )
                        else:
                            # New transcription
                            transcription = []
                            # Clear the queue and event
                            self.recordings_queue.clear()
                            recordings_available_event.clear()
                            while not transcription:
                                utterance = self.active_listen()
                                transcription = utterance.transcription
                                audio = utterance.audio
                    else:
                        visualizations.run_visualization(
                            "output",
                            "<  <noise>"
                        )
        except IndexError:
            recordings_available_event.clear()
        return mic.Utterance(transcription=transcription, audio=audio)

    def active_listen(self, play_prompts=True):
        """
        Active listen does not check for a wakeword.
    `   It should only be used in cases where Naomi has just asked a question.
        """
        if play_prompts:
            # let the user know we are listening
            if self._active_stt_reply:
                self.say(self._active_stt_reply)
            else:
                self._logger.debug("No text to respond with using beep")
                visualizations.run_visualization("output", ">> <beep>")
                self.play_file(paths.data('audio', 'beep_hi.wav'))

        transcription = ""
        audio = b''
        recordings_available_event.wait()
        try:
            audio = self.recordings_queue.pop()
            if len(audio) > 0:
                with self._write_frames_to_file(audio, None) as f:
                    transcription = [
                        " ".join(
                            self.active_stt_plugin.transcribe(f)
                        )
                    ]
        except IndexError:
            recordings_available_event.clear()
        if len(transcription) > 0:
            visualizations.run_visualization(
                "output",
                f"<< {transcription}"
            )
        else:
            visualizations.run_visualization(
                "output",
                "<< <noise>"
            )
        if play_prompts:
            if self._active_stt_response:
                self.say(self._active_stt_response)
            else:
                self._logger.debug("No text to respond with using beep")
                visualizations.run_visualization("output", ">> <boop>")
                self.play_file(paths.data('audio', 'beep_lo.wav'))
        return mic.Utterance(transcription=transcription, audio=audio)

    def handle_vad_output(self):
        """
        This is a thread that converts the audio captured by VAD
        sequentially into a transcript of the words spoken until it runs
        out of audio to process
        """
        while self.Continue:
            try:
                utterance = self.listen()
                if len(utterance.transcription):
                    self.handleRequest(utterance)
            except IndexError:
                break

    def say(self, phrase):
        self.actions_queue.appendleft(lambda: self.tts(phrase))
        if not (
            self.actions_thread
            and hasattr(self.actions_thread, "is_alive")
            and self.actions_thread.is_alive()
        ):
            # start the thread
            self.actions_thread = threading.Thread(
                target=self.process_actions
            )
            self.actions_thread.start()

    def play_file(self, filename):
        self.actions_queue.appendleft(lambda: self._play_file(filename))
        if not (
            self.actions_thread
            and hasattr(self.actions_thread, "is_alive")
            and self.actions_thread.is_alive()
        ):
            # start the thread
            self.actions_thread = threading.Thread(
                target=self.process_actions
            )
            self.actions_thread.start()

    def _play_file(self, filename):
        """
        Internal version of play_file used above
        """
        with open(filename, 'rb') as f:
            self._output_device.play_fp(f)
            time.sleep(.5)

    def process_actions(self):
        while self.Continue:
            try:
                action = self.actions_queue.pop()
                action()
            except IndexError:
                break

    def tts(self, phrase):
        altered_phrase = alteration.clean(phrase)
        visualizations.run_visualization("output", f">> {phrase}")
        with tempfile.SpooledTemporaryFile() as f:
            f.write(self.tts_engine.say(altered_phrase))
            f.seek(0)
            self._output_device.play_fp(f)
            time.sleep(.2)

    def main_loop(self):
        """This is an asynchronous main loop"""
        stt_thread = None
        try:
            with self._input_device.open_stream(
                output=False
            ) as stream:
                while self.Continue:
                    # put the audio in a queue and call the stt engine
                    self.queue_recording(
                        self.vad_plugin.get_audio(
                            stream=stream
                        )
                    )
                    if not (
                        stt_thread
                        and hasattr(stt_thread, "is_alive")
                        and stt_thread.is_alive()
                    ):
                        # start the thread
                        stt_thread = threading.Thread(
                            target=self.handle_vad_output
                        )
                        stt_thread.start()
        except KeyboardInterrupt:
            self.Continue = False
        visualizations.run_visualization(
            "output",
            "Exiting..."
        )

    def say_i_do_not_understand(self):
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
            self.brain.get_plugin_phrases(True)
        )
        # set up the special mode so it is pre-generated later
        with self.special_mode(name, phrases):
            pass
        self.queue_action(lambda: profile.set_arg('resetmic', True))
        self.say(prompt)
        # Now wait for any sounds in the queue to be processed
        while not profile.get_arg('resetmic'):
            utterance = self.listen()
            handled = False
            while (utterance.transcription and not handled):
                utterance, handled = self.handleRequest(
                    utterance
                )
        # Now that we are past the mic reset
        profile.set_arg('resetmic', False)
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
                        "Expecting: {expected_phrases} Got: {utterance.transcription}"
                    )
                    self._logger.info("Score: {}".format(score))
                    if (score > .1):
                        return phrase
                    # Otherwise, raise an exception with the active
                    # transcription.
                    # This will break us back into the main conversation loop
                    else:
                        # If the user is not responding to the prompt, then
                        # assume that they are starting a new command. This
                        # should mean that the wake word would be included.
                        if self.check_for_keyword(utterance.transcription):
                            raise mic.Unexpected(utterance)
                        else:
                            # The user just said something unexpected.
                            # Remind them of their choices
                            if instructions is None:
                                self.list_choices(expected_phrases)
                            else:
                                self.say(instructions)
