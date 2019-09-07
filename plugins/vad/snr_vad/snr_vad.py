# -*- coding: utf-8 -*-
from blessings import Terminal
from naomi.commandline import println
from naomi import plugin
from naomi import profile
import audioop
import math


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
class SNRPlugin(plugin.VADPlugin):
    _maxsnr = None
    _minsnr = None
    
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
            displaywidth = Terminal().width - 6
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
            snrrange = self._maxsnr - self._minsnr
            if snrrange == 0:
                snrrange = 1 # to avoid divide by zero below
            feedback = ["+"] if recording else ["-"]
            feedback.extend(
                list("".join([
                    "||",
                    ("=" * int(displaywidth * ((snr - self._minsnr) / snrrange))),
                    ("-" * int(displaywidth * ((self._maxsnr - snr) / snrrange))),
                    "||"
                ]))
            )
            # insert markers for mean and threshold
            if(self._minsnr < mean < self._maxsnr):
                feedback[int(displaywidth * ((mean - self._minsnr) / snrrange))] = 'm'
            if(self._threshold < maxsnr):
                feedback[int(displaywidth * ((self._threshold - self._minsnr) / snrrange))] = 't'
            println("".join(feedback))
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
