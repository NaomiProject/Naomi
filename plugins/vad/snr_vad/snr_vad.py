# -*- coding: utf-8 -*-
# This is a really simple voice activity detector
# based on what Naomi currently uses. When you create it,
# you can pass in a decibel level which defaults to 30dB.
# The optimal value for decibel level appears to be
# affected not only by noise levels where you are, but
# also the specific sound card or even microphone you
# are using.
# Once the audio level goes above this level, recording
# starts. Once the level goes below this for timeout
# seconds (floating point, can be fractional), then
# recording stops. If the total length of the recording is
# over twice the length of timeout, then the recorded audio
# is returned for processing.
from naomi import plugin
import audioop
import logging
import math


class SNRPlugin(plugin.VADPlugin):
    def __init__(
        self,
        input_device,
        timeout=1,
        minimum_capture=0.5,
        threshold=30
    ):
        super(SNRPlugin, self).__init__(input_device, timeout, minimum_capture)
        # if the audio decibel is greater than threshold, then consider this
        # having detected a voice.
        self._threshold = threshold
        # Keep track of the number of audio levels
        self.distribution = {}

    def _voice_detected(self, frame):
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
            self._threshold = mean + (stddev * 1.5)
            if(self._logger.getEffectiveLevel() < logging.ERROR):
                print(
                    "\t".join([
                        "snr: {}",
                        "threshold: {}",
                        "mean: {}",
                        "deviation: {}"
                    ]).format(
                        snr,
                        round(self._threshold),
                        round(mean),
                        round(stddev)
                    )
                )
        if(items > 100):
            # Every 100 samples, rescale, allowing changes in
            # the environment to be recognized more quickly.
            self.distribution = {
                key: (
                    (value + 1) / 2
                ) for key, value in self.distribution.items()
            }
        if(snr < self._threshold):
            response = False
        else:
            self._logger.info("Voice Detected: {}".format(snr))
            response = True
        return response
