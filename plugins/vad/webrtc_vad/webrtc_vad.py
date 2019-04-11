# -*- coding: utf-8 -*-
# This allows you to use the webrtcvad plugin.
# You should be able to install it with a simple
# pip install webrtcvad
import logging
from naomi import plugin
from naomi import profile
import webrtcvad


class WebRTCPlugin(plugin.VADPlugin):
    # Timeout in seconds
    def __init__(self, *args):
        self._logger = logging.getLogger(__name__)
        input_device = args[0]
        timeout = profile.get_profile_var(["webrtc_vad", "timeout"], 1)
        minimum_capture = profile.get_profile_var(
            ["webrtc_vad", "minimum_capture"],
            0.25
        )
        aggressiveness = profile.get_profile_var(
            ["webrtc_vad", "aggressiveness"],
            1
        )
        self._logger.info("timeout: {}".format(timeout))
        self._logger.info("minimum_capture: {}".format(minimum_capture))
        self._logger.info("aggressiveness: {}".format(aggressiveness))
        super(WebRTCPlugin, self).__init__(
            input_device,
            timeout,
            minimum_capture
        )
        if aggressiveness not in [0, 2, 3]:
            aggressiveness = 1
        self._vad = webrtcvad.Vad(aggressiveness)
        if(self._chunktime not in [0.01, 0.02, 0.03]):
            # From the website:
            #
            # https://github.com/wiseman/py-webrtcvad
            #
            # The WebRTC VAD only accepts 16-bit mono PCM audio, sampled at
            # 8000, 16000, 32000 or 48000 Hz. A frame must be either 10, 20,
            # or 30 ms in duration:
            raise ValueError(
                "\n".join([
                    "When using WebRTCVAD, chunks are limited to 10, 20,",
                    "or 30 millisends in length.",
                    "At current input rate of {}, the allowed chunk sizes are",
                    "{} (10ms), {} (20ms) or {} (30 ms).",
                    "Please adjust the value of",
                    "audio: ",
                    "  input_chunksize:",
                    "in your ~/.naomi/profile.yml file."
                ]).format(
                    input_device._input_rate,
                    input_device._input_rate * 0.01,
                    input_device._input_rate * 0.02,
                    input_device._input_rate * 0.03
                )
            )

    def _voice_detected(self, frame):
        if(self._vad.is_speech(frame, self._input_device._input_rate)):
            response = True
        else:
            response = False
        return response
