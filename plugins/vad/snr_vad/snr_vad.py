# -*- coding: utf-8 -*-
import audioop
import math
import unittest
from naomi import plugin
from naomi import profile
from naomi import visualizations


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
class SNRPlugin(plugin.VADPlugin, unittest.TestCase):
    _maxsnr = None
    _minsnr = None
    _visualizations = []

    def __init__(self, *args, **kwargs):
        input_device = args[0]
        timeout = profile.get_profile_var(["snr_vad", "timeout"], 1)
        minimum_capture = profile.get_profile_var(
            ["snr_vad", "minimum_capture"],
            0.5
        )
        threshold = profile.get_profile_var(["snr_vad", "threshold"], 30)
        super(SNRPlugin, self).__init__(input_device, timeout, minimum_capture)
        # if the audio decibel is greater than threshold, then consider this
        # having detected a voice.
        self._threshold = threshold
        # Keep track of the number of audio levels
        self.distribution = {}

    def _voice_detected(self, *args, **kwargs):
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
            # Every 100 samples, rescale, allowing changes in
            # the environment to be recognized more quickly.
            self.distribution = {
                key: (
                    (value + 1) / 2
                ) for key, value in self.distribution.items()
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
            self._logger.info("Voice Detected: {}/{}".format(snr, threshold))
            response = True
        return response
