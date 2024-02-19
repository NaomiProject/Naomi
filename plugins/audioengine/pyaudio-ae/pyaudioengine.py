# -*- coding: utf-8 -*-
import contextlib
import logging
import os
import pyaudio
import re
import slugify
import time
import wave
from naomi import plugin
from naomi import profile


PYAUDIO_BIT_MAPPING = {8: pyaudio.paInt8,
                       16: pyaudio.paInt16,
                       24: pyaudio.paInt24,
                       32: pyaudio.paInt32}


def bits_to_samplefmt(bits):
    if bits in PYAUDIO_BIT_MAPPING.keys():
        return PYAUDIO_BIT_MAPPING[bits]


# Context enabled open so we don't forget to close the file handle
# when hiding system stderr messages.
class hide_stderr:
    def __enter__(self):
        self.fd = os.open('/dev/null', os.O_WRONLY)
        self.std_err = os.dup(2)
        os.dup2(self.fd, 2)
        return self.fd

    def __exit__(self, *args, **kwargs):
        os.dup2(self.std_err, 2)
        os.close(self.fd)
        return True


class PyAudioEnginePlugin(plugin.AudioEnginePlugin):

    def __init__(self, *args, **kwargs):

        super(PyAudioEnginePlugin, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing PyAudio. ALSA/Jack error messages " +
                          "that pop up during this process are normal and " +
                          "can usually be safely ignored.")

        with hide_stderr():
            self._pyaudio = pyaudio.PyAudio()

        self._logger.info("Initialization of PyAudio engine finished")

    def __del__(self):
        self._pyaudio.terminate()

    def get_devices(self, device_type=plugin.audioengine.DEVICE_TYPE_ALL):
        num_devices = self._pyaudio.get_device_count()
        self._logger.debug('Found %d PyAudio devices', num_devices)
        devs = [PyAudioDevice(self, self._pyaudio.get_device_info_by_index(i))
                for i in range(num_devices)]
        if device_type == plugin.audioengine.DEVICE_TYPE_ALL:
            return devs
        else:
            return [device for device in devs if device_type in device.types]

    def get_default_device(self, output=True):
        try:
            if output:
                info = self._pyaudio.get_default_output_device_info()
            else:
                info = self._pyaudio.get_default_input_device_info()
        except IOError:
            direction = 'output' if output else 'input'
            devices = self.get_devices(device_type=(
                plugin.audioengine.DEVICE_TYPE_OUTPUT if output
                else plugin.audioengine.DEVICE_TYPE_INPUT))
            if len(devices) == 0:
                msg = 'No %s devices available!' % direction
                self._logger.warning(msg)
                raise plugin.audioengine.DeviceNotFound(msg)
            try:
                device = [d for d in devices if d.slug == 'default'][0]
            except IndexError:
                device = devices[0]
            return device
        else:
            return PyAudioDevice(self, info)

    def get_device_by_slug(self, slug):
        for device in self. get_devices():
            if device.slug == slug:
                return device
        raise plugin.audioengine.DeviceNotFound(
            "Audio device with slug '%s' not found" % slug)


class PyAudioDevice(plugin.audioengine.AudioDevice):
    RE_PRESLUG = re.compile(r'\(hw:\d,\d\)')
    _output_stream = None
    _output_format = pyaudio.paInt16
    _output_rate = 16000
    _output_channels = 2

    def __init__(self, engine, info):
        super(PyAudioDevice, self).__init__(info['name'])
        self._logger = logging.getLogger(__name__)
        self._engine = engine
        self._index = info['index']
        self._max_output_channels = info['maxOutputChannels']
        self._max_input_channels = info['maxInputChannels']
        # slugify the name
        preslug_name = self.RE_PRESLUG.sub('', self.name)
        if preslug_name.endswith(': - '):
            preslug_name = self.name
        self._pyaudio_slug = slugify.slugify(preslug_name)

    @property
    def slug(self):
        return self._pyaudio_slug

    @property
    def index(self):
        return self._index

    @property
    def types(self):
        types = []
        if self._max_input_channels > 0:
            types.append(plugin.audioengine.DEVICE_TYPE_INPUT)
        if self._max_output_channels > 0:
            types.append(plugin.audioengine.DEVICE_TYPE_OUTPUT)
        return tuple(types)

    def supports_format(self, bits, channels, rate, output=True):
        req_dev_type = (plugin.audioengine.DEVICE_TYPE_OUTPUT if output
                        else plugin.audioengine.DEVICE_TYPE_INPUT)
        if req_dev_type not in self.types:
            return False
        sample_fmt = bits_to_samplefmt(bits)
        if not sample_fmt:
            return False
        direction = 'output' if output else 'input'
        fmt_info = {
            ('%s_device' % direction): self.index,
            ('%s_format' % direction): sample_fmt,
            ('%s_channels' % direction): channels,
            'rate': rate
        }
        try:
            supported = self._engine._pyaudio.is_format_supported(**fmt_info)
        except ValueError as e:
            if e.args in (('Sample format not supported', -9994),
                          ('Invalid sample rate', -9997),
                          ('Invalid number of channels', -9998),
                          ('Device unavailable', -9985)):
                return False
            else:
                raise
        else:
            return supported

    @contextlib.contextmanager
    def open_stream(self, bits, channels, rate, chunksize=1024, output=True):
        # Check if format is supported
        is_supported_fmt = self.supports_format(bits, channels, rate,
                                                output=output)
        if not is_supported_fmt:
            msg_fmt = ("PyAudioDevice {index} ({name}) doesn't support " +
                       "%s format (Int{bits}, {channels}-channel at" +
                       " {rate} Hz)") % ('output' if output else 'input')
            msg = msg_fmt.format(index=self.index,
                                 name=self.name,
                                 bits=bits,
                                 channels=channels,
                                 rate=rate)
            self._logger.critical(msg)
            raise plugin.audioengine.UnsupportedFormat(msg)
        # Everything looks fine, open the stream
        direction = ('output' if output else 'input')
        stream_kwargs = {
            'format': bits_to_samplefmt(bits),
            'channels': channels,
            'rate': rate,
            'output': output,
            'input': not output,
            ('%s_device_index' % direction): self.index,
            'frames_per_buffer': chunksize if output else chunksize * 8  # Hacky
        }
        stream = self._engine._pyaudio.open(**stream_kwargs)

        self._logger.debug("%s stream opened on device '%s' (%d Hz, %d " +
                           "channel, %d bit)", "output" if output else "input",
                           self.slug, rate, channels, bits)
        try:
            yield stream
        finally:
            stream.close()
            self._logger.debug("%s stream closed on device '%s'",
                               "output" if output else "input", self.slug)

    def record(self, chunksize, *args):
        # AJC 2018-08-02 Add a second while loop so if the pyaudio stream
        # gets closed, we immediately reopen it rather than continue
        # to try to read from a closed stream
        while True:
            with self.open_stream(*args, chunksize=chunksize,
                                output=False) as stream:
                while True:
                    try:
                        frame = stream.read(chunksize)
                    except IOError as e:
                        if type(e.errno) is not int:
                            # Simple hack to work around the fact that the
                            # errno/strerror arguments were swapped in older
                            # PyAudio versions. This was fixed in upstream
                            # commit 1783aaf9bcc6f8bffc478cb5120ccb6f5091b3fb.
                            strerror, errno = e.errno, e.strerror
                        else:
                            strerror, errno = e.strerror, e.errno
                        self._logger.warning(
                            "IO error while reading from device" +
                            " '%s': '%s' (Errno: %d)" % (
                                self.slug,
                                strerror,
                                errno
                            )
                        )
                        break
                    else:
                        yield frame

    def play_fp(self, fp, *args, **kwargs):
        self._stop = False
        if ('chunksize' in kwargs):
            chunksize = kwargs['chunksize']
        else:
            chunksize = int(profile.get(['audio', 'output_chunksize'], 1024))
        if ('add_padding' in kwargs):
            add_padding = kwargs['add_padding']
        else:
            add_padding = profile.get(['audio', 'output_padding'], False)
        pause = float(profile.get(['audio', 'output_pause'], 0))
        with wave.open(fp, 'rb') as w:
            channels = w.getnchannels()
            samplewidth = w.getsampwidth()
            bits = w.getsampwidth() * 8
            rate = w.getframerate()
            data = w.readframes(chunksize)
            datalen = len(data)
            fmt = bits_to_samplefmt(bits)
            if (self._output_stream is None):
                self._output_stream = self._engine._pyaudio.open(
                    format=fmt,
                    channels=channels,
                    rate=rate,
                    output=True,
                    input=False,
                    output_device_index=self.index,
                    frames_per_buffer=chunksize
                )
                # Set the initial values for self._output_format,
                # self._output_rate and self._output_channels
                self._output_format = fmt
                self._output_rate = rate
                self._output_channels = channels
            # Check to make sure that format, rate and channels match
            # the current stream. If not, close and reopen.
            # Note: This causes an error if the previous stream is not
            # finished playing. The mostly causes problems when playing
            # the "beep" noises which are recorded at a higher bitrate.
            if (
                (fmt != self._output_format)
                or (rate != self._output_rate)
                or (channels != self._output_channels)
            ):
                self._output_stream.stop_stream()
                self._output_stream.close()
                self._output_stream = self._engine._pyaudio.open(
                    format=fmt,
                    channels=channels,
                    rate=rate,
                    output=True,
                    input=False,
                    output_device_index=self.index,
                    frames_per_buffer=chunksize
                )
                self._output_format = fmt
                self._output_rate = rate
                self._output_channels = channels
            if (
                (add_padding)
                and (datalen > 0)
                and (datalen < (chunksize * samplewidth))
            ):
                data += b'\00' * (chunksize * samplewidth - datalen)
                datalen = len(data)
            while (datalen > 0):
                # Check to see if we need to stop
                if (self._stop):
                    self._stop = False
                    break
                # Generates "ALSA lib pcm.c:8545:(snd_pcm_recover) underrun
                # occurred" errors
                try:
                    self._output_stream.write(data)
                except OSError:
                    self._output_stream = self._engine._pyaudio.open(
                        format=bits_to_samplefmt(bits),
                        channels=channels,
                        rate=rate,
                        output=True,
                        input=False,
                        output_device_index=self.index,
                        frames_per_buffer=chunksize
                    )
                    self._output_stream.write(data)
                data = w.readframes(chunksize)
                datalen = len(data)
                if (
                    (add_padding)
                    and (datalen > 0)
                    and (datalen < (chunksize * samplewidth))
                ):
                    data += b'\00' * (chunksize * samplewidth - datalen)
                    datalen = len(data)
            # pause before closing the stream (reduce clipping)
            if (pause > 0):
                time.sleep(pause)
            self._stop = False
