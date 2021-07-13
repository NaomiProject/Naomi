# -*- coding: utf-8 -*-
# This allows you to use the webrtcvad plugin.
# You should be able to install it with a simple
# pip install webrtcvad
import audioop
import logging
import math
import unittest
import webrtcvad
from naomi import plugin
from naomi import profile
from naomi import visualizations


class WebRTCPlugin(plugin.VADPlugin, unittest.TestCase):
    _maxsnr = None
    _minsnr = None
    _visualizations = []

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
            3
        )

        threshold = profile.get_profile_var(["webrtc_vad", "threshold"], 30)
        super(WebRTCPlugin, self).__init__(input_device, timeout, minimum_capture)
        # if the audio decibel is greater than threshold, then consider this
        # having detected a voice.
        self._threshold = threshold
        # Keep track of the number of audio levels
        self.distribution = {}

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
                    "in your ~/.config/naomi/configs/profile.yml file."
                ]).format(
                    input_device._input_rate,
                    input_device._input_rate * 0.01,
                    input_device._input_rate * 0.02,
                    input_device._input_rate * 0.03
                )
            )

    def _voice_detected(self, *args, **kwargs):
        frame = args[0]
        self._logger.info("Frame length: {} bytes".format(len(frame)))
        # The frame length must be either .01, .02 or .02 ms.
        # Sometimes the audio card will refuse to obey the chunksize
        # directive. In this case, we have to cut down the sample to
        # fit the next smaller unit
        sample_rate = self._input_device._input_rate
        input_bytes = self._input_device._input_bits / 8
        sample_length = len(frame) / input_bytes / sample_rate
        if not((
            sample_length == 0.01
        )or(
            sample_length == 0.02
        )or(
            sample_length == 0.03
        )):
            if(sample_length > 0.03):
                self._logger.info(
                    "Reducing buf length from {} to {} (0.03 seconds)".format(
                        len(frame),
                        int(sample_rate * input_bytes * 0.03)
                    )
                )
                frame = frame[:int(sample_rate * input_bytes * 0.03)]
            elif(sample_length > 0.02):
                self._logger.info(
                    "Reducing buf length from {} to {} (0.02 seconds)".format(
                        len(frame),
                        int(sample_rate * input_bytes * 0.02)
                    )
                )
                frame = frame[:int(sample_rate * input_bytes * 0.02)]
            elif(sample_length > 0.01):
                self._logger.info(
                    "Reducing buf length from {} to {} (0.01 seconds)".format(
                        len(frame),
                        int(sample_rate * input_bytes * 0.01)
                    )
                )
                frame = frame[:int(sample_rate * input_bytes * 0.01)]
            else:
                raise Exception(
                    "Buffer length {} less than minimum of {}".format(
                        len(frame),
                        int(sample_rate * input_bytes * 0.01)
                    )
                )
        frame = args[0]
        recording = False
        if "recording" in kwargs:
            recording = kwargs["recording"]
        rms = audioop.rms(frame, int(self._input_device._input_bits / 8))
        if rms > 0 and self._threshold > 0:
            snr = round(20.0 * math.log(rms / self._threshold, 10))
        else:
            snr = 0
        if snr in self.distribution:
            self.distribution[snr] += 1
        else:
            self.distribution[snr] = 1
        # calculate the mean and standard deviation
        sum1 = sum([
            value * (key ** 2) for key, value in self.distribution.items()
        ])
        items = sum([value for value in self.distribution.values()])
        if items > 1:
            # mean = sum( value * freq )/items
            mean = sum(
                [key * value for key, value in self.distribution.items()]
            ) / items
            stddev = math.sqrt((sum1 - (items * (mean ** 2))) / (items - 1))
            self._threshold = mean + (
                stddev * profile.get(
                    ['snr_vad', 'tolerance'],
                    1
                )
            )
            # We'll say that the max possible value for SNR is mean+3*stddev
            if self._minsnr is None:
                self._minsnr = snr
            if self._maxsnr is None:
                self._maxsnr = snr
            maxsnr = mean + 3 * stddev
            if snr > maxsnr:
                maxsnr = snr
            if maxsnr > self._maxsnr:
                self._maxsnr = maxsnr
            minsnr = mean - 3 * stddev
            if snr < minsnr:
                minsnr = snr
            if minsnr < self._minsnr:
                self._minsnr = minsnr
            # Loop through visualization plugins
            visualizations.run_visualization(
                "mic_volume",
                recording=recording,
                snr=snr,
                minsnr=self._minsnr,
                maxsnr=self._maxsnr,
                mean=mean,
                threshold=self._threshold
            )
        if(items > 100):
            # Every 50 samples (about 1-3 seconds), rescale,
            # allowing changes in the environment to be
            # recognized more quickly.
            self.distribution = {
                key: (
                    (value + 1) / 2
                ) for key, value in self.distribution.items() if value > 1
            }
        threshold = self._threshold
        # If we are already recording, reduce the threshold so as
        # the user's voice trails off, we continue to record.
        # Here I am setting it to the halfway point between threshold
        # and mean.
        if(recording):
            threshold = (mean + threshold) / 2
        if(snr < threshold):
            response = False
        else:
            if(self._vad.is_speech(frame, self._input_device._input_rate)):
                response = True
                self._logger.info("Voice detected")
            else:
                response = False
        return response
