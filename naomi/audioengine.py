# -*- coding: utf-8 -*-
import abc
import contextlib
import slugify
import time
import wave
from naomi import profile


STANDARD_SAMPLE_RATES = (
    8000, 9600, 11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000, 88200,
    96000, 192000
)


DEVICE_TYPE_ALL = 'all'
DEVICE_TYPE_INPUT = 'input'
DEVICE_TYPE_OUTPUT = 'output'


class DeviceException(Exception):
    pass


class UnsupportedFormat(DeviceException):
    pass


class DeviceNotFound(DeviceException):
    pass


class AudioEngine(object):
    @abc.abstractmethod
    def get_devices(self, device_type=DEVICE_TYPE_ALL):
        pass

    @abc.abstractmethod
    def get_default_device(self, output=True):
        pass

    @abc.abstractmethod
    def get_device_by_slug(self, slug):
        pass


class AudioDevice(object):
    def __init__(self, name):
        self._name = name
        self._slug = slugify.slugify(name)
        self._input_rate = profile.get_profile_var(
            ['audio', 'input_samplerate'],
            16000
        )
        self._input_bits = profile.get_profile_var(
            ['audio', 'input_samplewidth'],
            16
        )
        self._input_channels = profile.get_profile_var(
            ['audio', 'input_channels'],
            1
        )
        self._input_chunksize = profile.get_profile_var(
            ['audio', 'input_chunksize'],
            1024
        )

    @property
    def name(self):
        return self._name

    @property
    def slug(self):
        return self._slug

    @abc.abstractproperty
    def types(self):
        pass

    @abc.abstractmethod
    def supports_format(self, bits, channels, rate, output=True):
        pass

    @abc.abstractmethod
    @contextlib.contextmanager
    def open_stream(self, bits, channels, rate, chunksize=1024, output=True):
        pass

    @abc.abstractmethod
    def record(self, chunksize, *args):
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
                        ' '.join([
                            "IO error while reading from device",
                            "'{}': '{}' (Errno: {})"
                        ]).format(
                            self.slug,
                            strerror,
                            errno
                        )
                    )
                else:
                    yield frame

    def play_fp(self, fp, *args, **kwargs):
        if('chunksize' in kwargs):
            chunksize = kwargs['chunksize']
        else:
            chunksize = int(profile.get(['audio', 'output_chunksize'], 1024))
        if('add_padding' in kwargs):
            add_padding = kwargs['add_padding']
        else:
            add_padding = profile.get(['audio', 'output_padding'], False)
        pause = float(profile.get(['audio', 'output_pause'], 0))
        w = wave.open(fp, 'rb')
        channels = w.getnchannels()
        samplewidth = w.getsampwidth()
        bits = w.getsampwidth() * 8
        rate = w.getframerate()
        with self.open_stream(
            bits,
            channels,
            rate,
            chunksize=chunksize
        ) as stream:
            data = w.readframes(chunksize)
            datalen = len(data)
            if add_padding and datalen > 0 and datalen < (chunksize * samplewidth):
                data += b'\00' * (chunksize * samplewidth - datalen)
                datalen = len(data)
            while data:
                # Check to see if we need to stop
                if(hasattr(self, "stop")):
                    del self.stop
                    break
                stream.write(data)
                data = w.readframes(chunksize)
                datalen = len(data)
                if add_padding and datalen > 0 and datalen < (chunksize * samplewidth):
                    data += b'\00' * (chunksize * samplewidth - datalen)
                    datalen = len(data)
            # pause before closing the stream (reduce clipping)
            if(pause > 0):
                time.sleep(pause)
        w.close()

    def play_file(self, filename, *args, **kwargs):
        with open(filename, 'rb') as f:
            self.play_fp(f, *args, **kwargs)

    def print_device_info(self, verbose=False):
        print('[Audio device \'%s\']' % self.slug)
        print('  Name: %s' % self.name)
        print('  Input device: %s' % ('Yes'
                                      if DEVICE_TYPE_INPUT in self.types
                                      else 'No'))
        print('  Output device: %s' % ('Yes'
                                       if DEVICE_TYPE_OUTPUT in self.types
                                       else 'No'))
        if verbose:
            for io_type in self.types:
                direction = 'output' if DEVICE_TYPE_OUTPUT else 'input'
                print('  Supported %s formats:' % direction)
                formats = []
                for bits in (8, 16, 24, 32):
                    for channels in (1, 2):
                        for rate in STANDARD_SAMPLE_RATES:
                            args = (bits, channels, rate)
                            if self.supports_format(
                                    *args, output=(direction == 'output')):
                                formats.append(args)
                if len(formats) == 0:
                    print('    None')
                else:
                    n = 4
                    for chunk in (formats[i:i + n]
                                  for i in range(0, len(formats), n)):
                        print('    %s' % ', '.join(
                            "(%d Bit %d CH @ %d Hz)" % fmt
                            for fmt in chunk))
