# -*- coding: utf-8 -*-
from blessings import Terminal
from datetime import datetime
from naomi.commandline import println
from naomi import plugin


class TerminalVisualizationsPlugin(plugin.VisualizationsPlugin):
    @classmethod
    def mic_volume(self, *args, **kwargs):
        try:
            recording = kwargs['recording']
            snr = kwargs['snr']
            minsnr = kwargs['minsnr']
            maxsnr = kwargs['maxsnr']
            mean = kwargs['mean']
            threshold = kwargs['threshold']
        except KeyError:
            return
        try:
            displaywidth = Terminal().width - 6
        except TypeError:
            displaywidth = 20
        snrrange = maxsnr - minsnr
        if snrrange == 0:
            snrrange = 1  # to avoid divide by zero below

        feedback = ["+"] if recording else ["-"]
        feedback.extend(
            list("".join([
                "||",
                ("=" * int(displaywidth * ((snr - minsnr) / snrrange))),
                ("-" * int(displaywidth * ((maxsnr - snr) / snrrange))),
                "||"
            ]))
        )
        # insert markers for mean and threshold
        if (minsnr < mean < maxsnr):
            feedback[int(displaywidth * ((mean - minsnr) / snrrange))] = 'm'
        if (minsnr < threshold < maxsnr):
            feedback[int(displaywidth * ((threshold - minsnr) / snrrange))] = 't'
        println("".join(feedback))

    @staticmethod
    def output(message, timestamp=True):
        if (timestamp):
            now = datetime.now()
            println(f"{now:%I}:{now:%M} {now:%p} - {message}\n")
        else:
            println(f"{message}\n")
