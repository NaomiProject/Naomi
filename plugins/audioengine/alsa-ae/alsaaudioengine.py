# -*- coding: utf-8 -*-
import logging
import contextlib
import alsaaudio
from naomi import plugin

ALSAAUDIO_BIT_MAPPING = {8: alsaaudio.PCM_FORMAT_S8,
                         16: alsaaudio.PCM_FORMAT_S16_LE,
                         24: alsaaudio.PCM_FORMAT_S24_LE,
                         32: alsaaudio.PCM_FORMAT_S32_LE}


def bits_to_samplefmt(bits):
    if bits in ALSAAUDIO_BIT_MAPPING.keys():
        return ALSAAUDIO_BIT_MAPPING[bits]


class AlsaAudioEnginePlugin(plugin.AudioEnginePlugin):
    def __init__(self, *args, **kwargs):
        super(AlsaAudioEnginePlugin, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)

    def get_devices(self, device_type=plugin.audioengine.DEVICE_TYPE_ALL):
        devices = set()
        if device_type in (plugin.audioengine.DEVICE_TYPE_ALL,
                           plugin.audioengine.DEVICE_TYPE_OUTPUT):
            devices.update(set(alsaaudio.pcms(alsaaudio.PCM_PLAYBACK)))
        if device_type in (plugin.audioengine.DEVICE_TYPE_ALL,
                           plugin.audioengine.DEVICE_TYPE_INPUT):
            devices.update(set(alsaaudio.pcms(alsaaudio.PCM_CAPTURE)))
        device_names = sorted(list(devices))
        num_devices = len(device_names)
        self._logger.debug('Found %d ALSA devices', num_devices)
        return [AlsaAudioDevice(name) for name in device_names]

    def get_default_device(self, output=True):
        device_name = 'default'
        req_type = (plugin.audioengine.DEVICE_TYPE_OUTPUT if output
                    else plugin.audioengine.DEVICE_TYPE_INPUT)
        try:
            device = self.get_device_by_slug(device_name)
        except plugin.audioengine.DeviceNotFound:
            pass
        else:
            if req_type in device.types:
                return device
        devices = self.get_devices(device_type=req_type)
        if len(devices) == 0:
            direction = 'output' if output else 'input'
            msg = 'No %s devices available!' % direction
            self._logger.warning(msg)
            raise plugin.audioengine.DeviceNotFound(msg)
        return devices[0]

    def get_device_by_slug(self, slug):
        for device in self.get_devices():
            if device.slug == slug:
                return device
        raise plugin.audioengine.DeviceNotFound(
            "Audio device with slug '%s' not found" % slug)


class AlsaAudioDevice(plugin.audioengine.AudioDevice):
    def __init__(self, name):
        super(AlsaAudioDevice, self).__init__(name)
        self._logger = logging.getLogger(__name__)

    @property
    def types(self):
        types = []
        if self.name in alsaaudio.pcms(alsaaudio.PCM_CAPTURE):
            types.append(plugin.audioengine.DEVICE_TYPE_INPUT)
        if self.name in alsaaudio.pcms(alsaaudio.PCM_PLAYBACK):
            types.append(plugin.audioengine.DEVICE_TYPE_OUTPUT)
        return tuple(types)

    def supports_format(self, bits, channels, rate, output=True):
        req_type = (plugin.audioengine.DEVICE_TYPE_OUTPUT if output
                    else plugin.audioengine.DEVICE_TYPE_INPUT)
        if req_type not in self.types:
            return False
        elif bits_to_samplefmt(bits) is None:
            return False
        return True

    @contextlib.contextmanager
    def open_stream(self, *args, **kwargs):
        bits = self._input_bits
        if 'bits' in kwargs:
            bits = kwargs['bits']
        channels = self._input_channels
        if 'channels' in kwargs:
            channels = kwargs['channels']
        rate = self._input_rate
        if 'rate' in kwargs:
            rate = kwargs['rate']
        output = True
        if 'output' in kwargs:
            output = kwargs['output']
        chunksize = self._input_chunksize
        if 'chunksize' in kwargs:
            chunksize = kwargs['chunksize']

        # Check if format is supported
        is_supported_fmt = self.supports_format(bits, channels, rate,
                                                output=output)
        if not is_supported_fmt:
            msg_fmt = ("ALSAAudioDevice ({name}) doesn't support " +
                       "%s format (Int{bits}, {channels}-channel at" +
                       " {rate} Hz)") % ('output' if output else 'input')
            msg = msg_fmt.format(name=self.name,
                                 bits=bits,
                                 channels=channels,
                                 rate=rate)
            self._logger.critical(msg)
            raise Exception(msg)
        # Everything looks fine, open the PCM stream
        pcm_type = alsaaudio.PCM_PLAYBACK if output else alsaaudio.PCM_CAPTURE
        stream = alsaaudio.PCM(type=pcm_type,
                               mode=alsaaudio.PCM_NORMAL,
                               device=self.name)
        stream.setchannels(channels)
        stream.setrate(rate)
        stream.setformat(bits_to_samplefmt(bits))
        stream.setperiodsize(chunksize)
        self._logger.debug("%s stream opened on device '%s' (%d Hz, %d " +
                           "channel, %d bit)", "output" if output else "input",
                           self.slug, rate, channels, bits)
        try:
            yield stream
        finally:
            stream.close()
            self._logger.debug("%s stream closed on device '%s'",
                               "output" if output else "input", self.slug)

    def record(self, *args, **kwargs):
        # AJC 2018-08-02 Add a second while loop so if the stream
        # gets closed, we immediately reopen it rather than continue
        # to try to read from a closed stream
        stream = None
        if 'stream' in kwargs:
            stream = kwargs['stream']
        while True:
            if stream:
                try:
                    frame = stream.read()
                except IOError as e:
                    self._logger.warning(e)
                    break
                else:
                    yield frame[1]
            else:
                with self.open_stream(
                    bits=self._input_bits,
                    channels=self._input_channels,
                    rate=self._input_rate,
                    chunksize=self._input_chunksize,
                    output=False
                ) as stream:
                    while True:
                        try:
                            frame = stream.read()
                        except IOError as e:
                            self._logger.warning(e)
                            break
                        else:
                            yield frame[1]
