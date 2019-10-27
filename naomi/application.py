# -*- coding: utf-8 -*-
import audioop
import collections
import csv
import io
import logging
import math
import os
import platform
import re
import shutil
import tempfile
import urllib
import wave
from . import audioengine
from . import brain
from . import commandline as interface
from . import i18n
from . import paths
from . import pluginstore
# from . import populate
from . import conversation
from . import mic
from . import profile
from .run_command import run_command
from . import local_mic
from . import batch_mic
from . import visualizations
from .strcmpci import strcmpci

USE_STANDARD_MIC = 0
USE_TEXT_MIC = 1
USE_BATCH_MIC = 2
DEFAULT_PLUGIN_URL = "/".join([
    "https://raw.githubusercontent.com",
    "NaomiProject",
    "naomi-plugins",
    "master",
    "plugins.csv"
])
_ = None
audioengine_plugins = None


# AaronC = for detecting audio. Switch to using VAD engine.
def _snr(input_bits, threshold, frames):
    rms = audioop.rms(b''.join(frames), int(input_bits / 8))
    if ((threshold > 0) and (rms > threshold)):
        return 20.0 * math.log(rms / threshold, 10)
    else:
        return 0


class Naomi(object):
    def __init__(
        self,
        use_mic=USE_STANDARD_MIC,
        batch_file=None,
        repopulate=False,
        print_transcript=False,
        passive_listen=False,
        save_audio=False,
        save_passive_audio=False,
        save_active_audio=False,
        save_noise=False
    ):
        global _
        self._logger = logging.getLogger(__name__)
        self._interface = interface.commandline()
        # check that the values we need in order to run Naomi
        # exist
        language = profile.get_profile_var(['language'])
        if(not language):
            language = 'en-US'
            self._logger.warn(
                ' '.join([
                    'language not specified in profile,',
                    'using default ({})'.format(language)
                ])
            )
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations)
        self.gettext = translator.gettext
        _ = translator.gettext
        # Load plugins
        self.plugins = pluginstore.PluginStore()
        self.plugins.detect_plugins()
        self._logger.info("Using Language '{}'".format(language))
        if hasattr(self, "settings"):
            # set a variable here to tell us if all settings are
            # completed or not
            # If all settings do not currently exist, go ahead and
            # re-query all settings for this plugin
            settings_complete = True
            # Step through the settings and check for
            # any missing settings
            for setting in self.settings():
                if not profile.check_profile_var_exists(setting):
                    self._logger.info(
                        "{} setting does not exist".format(setting)
                    )
                    # Go ahead and pull the setting
                    settings_complete = False
        # Disabling populate until I figure out what can't be
        # handled through settings.
        # if(profile.get_arg("Profile_missing", False)):
        #     print("Your config file does not exist.")
        #     text_input = input(
        #         " ".join([
        #             "Would you like to answer a few ",
        #             "questions to create a new one? (y/N): "
        #         ])
        #     )
        #     if(text_input.strip()[:1].upper() == "Y"):
        #         populate.run()
        #     else:
        #         print("Cannot continue. Exiting.")
        #         quit()
        if(profile.get_arg("repopulate") or profile.get_arg("profile_missing") or not settings_complete):
            populate.run()
            print(self._interface.status_text(_(
                "Configuring {}"
            ).format(
                profile.get_profile_var(['keyword'], ['Naomi'])[0]
            )))
            for setting in self.settings():
                self._interface.get_setting(
                    setting, self.settings()[setting]
                )
            # Save the profile with the new settings
            profile.save_profile()

        language = profile.get_profile_var(['language'])
        if(not language):
            language = 'en-US'
            self._logger.warn(
                ' '.join([
                    'language not specified in profile,',
                    'using default ({})'.format(language)
                ])
            )
        self._logger.info("Using Language '{}'".format(language))

        audio_engine_slug = profile.get_profile_var(['audio_engine'])
        if(not audio_engine_slug):
            audio_engine_slug = 'pyaudio'
            self._logger.warn(
                ' '.join([
                    "audio_engine not specified in profile, using",
                    "defaults ({}).".format(audio_engine_slug)
                ])
            )
        self._logger.info("Using Audio engine '{}'".format(audio_engine_slug))

        active_stt_slug = profile.get_profile_var(
            ['active_stt', 'engine']
        )
        if(not active_stt_slug):
            active_stt_slug = 'sphinx'
            self._logger.warning(
                " ".join([
                    "stt_engine not specified in profile,",
                    "using default ({}).".format(active_stt_slug)
                ])
            )
        self._logger.info(
            "Using STT (speech to text) engine '{}'".format(active_stt_slug)
        )

        active_stt_reply = profile.get_profile_var(
            ['active_stt', 'reply']
        )
        if(active_stt_reply):
            self._logger.info(
                "Using active STT voice reply '{}'".format(active_stt_reply)
            )

        active_stt_response = profile.get_profile_var(
            ['active_stt', 'response']
        )
        if(active_stt_response):
            self._logger.info(
                "Using active STT voice response '{}'".format(
                    active_stt_response
                )
            )

        passive_stt_slug = profile.get_profile_var(
            ['passive_stt', 'engine'],
            active_stt_slug
        )
        self._logger.info(
            "Using passive STT engine '{}'".format(passive_stt_slug)
        )

        special_stt_slug = profile.get_profile_var(
            ['special_stt', 'engine'],
            active_stt_slug
        )
        self._logger.info(
            "Using special STT engine '{}'".format(special_stt_slug)
        )

        tts_slug = profile.get_profile_var(['tts_engine'])
        if(not tts_slug):
            tts_slug = 'espeak-tts'
            self._logger.warning(
                " ".join([
                    "tts_engine not specified in profile, using",
                    "defaults."
                ])
            )
        self._logger.info("Using TTS engine '{}'".format(tts_slug))

        keyword = profile.get_profile_var(['keyword'], ['NAOMI'])
        if isinstance(keyword, str):
            keyword = [keyword]
            profile.set_profile_var(['keyword'], keyword)
            profile.save_profile()
        self._logger.info("Using keywords '{}'".format(', '.join(keyword)))

        if(not print_transcript):
            print_transcript = profile.get_profile_flag(
                ['print_transcript'],
                False
            )

        # passive_listen
        if(not passive_listen):
            passive_listen = profile.get_profile_flag(["passive_listen"])

        # Audiolog settings
        if(save_audio):
            save_passive_audio = True
            save_active_audio = True
            save_noise = True
        elif(not(save_passive_audio or save_active_audio or save_noise)):
            # get the settings from the profile
            if(profile.get_profile_flag(['audiolog', 'save_audio'], False)):
                save_passive_audio = True
                save_active_audio = True
                save_noise = True
            else:
                save_passive_audio = profile.get_profile_flag(
                    ['audiolog', 'save_passive_audio']
                )
                save_active_audio = profile.get_profile_flag(
                    ['audiolog', 'save_active_audio']
                )
                save_noise = profile.get_profile_flag(
                    ['audiolog', 'save_noise']
                )

        # load visualizations
        visualizations.load_visualizations(self)

        # Initialize AudioEngine
        ae_info = self.plugins.get_plugin(
            audio_engine_slug,
            category='audioengine'
        )
        self.audio = ae_info.plugin_class(ae_info)
        # self.check_settings(self.audio, repopulate)

        # Initialize audio input device
        devices = [device.slug for device in self.audio.get_devices(
            device_type=audioengine.DEVICE_TYPE_INPUT)]
        try:
            device_slug = profile.get_profile_var(['audio', 'input_device'])
        except KeyError:
            device_slug = self.audio.get_default_device(output=False).slug
            self._logger.warning(
                " ".join([
                    "input_device not specified in profile, ",
                    "defaulting to '{:s}' (Possible values: {:s})"
                ]).format(
                    device_slug,
                    ', '.join(devices)
                )
            )
        try:
            input_device = self.audio.get_device_by_slug(device_slug)
            if audioengine.DEVICE_TYPE_INPUT not in input_device.types:
                raise audioengine.UnsupportedFormat(
                    "Audio device with slug '%s' is not an input device"
                    % input_device.slug)
        except (audioengine.DeviceException) as e:
            self._logger.critical(e.args[0])
            self._logger.warning('Valid input devices: %s',
                                 ', '.join(devices))
            raise
        input_device._input_rate = profile.get_profile_var(
            ['audio', 'input_samplerate'],
            16000
        )
        input_device._input_bits = profile.get_profile_var(
            ['audio', 'input_samplewidth'],
            16
        )
        input_device._input_channels = profile.get_profile_var(
            ['audio', 'input_channels'],
            1
        )
        input_device._input_chunksize = profile.get_profile_var(
            ['audio', 'input_chunksize'],
            1024
        )
        self._logger.debug(
            'Input sample rate: {:d} Hz'.format(
                input_device._input_rate
            )
        )
        self._logger.debug(
            'Input sample width: {:d} bit'.format(
                input_device._input_bits
            )
        )
        self._logger.debug(
            'Input channels: {:d}'.format(
                input_device._input_channels
            )
        )
        self._logger.debug(
            'Input chunksize: {:d} frames'.format(
                input_device._input_chunksize
            )
        )

        # Initialize audio output device
        devices = [device.slug for device in self.audio.get_devices(
            device_type=audioengine.DEVICE_TYPE_OUTPUT)]
        device_slug = profile.get(['audio', 'output_device'])
        if not device_slug:
            device_slug = self.audio.get_default_device(output=True).slug
            self._logger.warning(
                " ".join([
                    "output_device not specified in profile,",
                    "defaulting to '{0:s}' (Possible values: {1:s})"
                ]).format(device_slug, ', '.join(devices))
            )
        output_device = self.audio.get_device_by_slug(device_slug)
        try:
            if audioengine.DEVICE_TYPE_OUTPUT not in output_device.types:
                raise audioengine.UnsupportedFormat(
                    " ".join([
                        "Audio device with slug '{:s}'",
                        "is not an output device"
                    ]).format(output_device.slug)
                )
        except (audioengine.DeviceException) as e:
            self._logger.critical(e.args[0])
            self._logger.warning(
                'Valid output devices: {:s}'.format(', '.join(devices))
            )
            raise
        output_device._output_chunksize = profile.get_profile_var(
            ['audio', 'output_chunksize'],
            1024
        )
        output_device._output_padding = profile.get_profile_flag(
            ['audio', 'output_padding'],
            False
        )
        self._logger.debug(
            'Output chunksize: {:d} frames'.format(
                output_device._output_chunksize
            )
        )
        self._logger.debug(
            'Output padding: {:s}'.format(
                'yes' if output_device._output_padding else 'no'
            )
        )

        # Initialize Voice activity detection
        vad_slug = profile.get_profile_var(['vad_engine'], 'snr_vad')
        vad_info = self.plugins.get_plugin(
            vad_slug,
            category='vad'
        )
        vad_plugin = vad_info.plugin_class(input_device)

        # Initialize Brain
        tti_slug = profile.get_profile_var(['tti_engine'], 'Naomi TTI')
        tti_info = self.plugins.get_plugin(
            tti_slug,
            category='tti'
        )
        intent_parser = tti_info.plugin_class(tti_info)

        self.brain = brain.Brain(intent_parser)
        for info in self.plugins.get_plugins_by_category('speechhandler'):
            try:
                plugin = info.plugin_class(info)
                self.brain.add_plugin(plugin)
            except Exception as e:
                self._logger.warning(
                    "Plugin '%s' skipped! (Reason: %s)", info.name,
                    e.message if hasattr(e, 'message') else 'Unknown',
                    exc_info=(
                        self._logger.getEffectiveLevel() == logging.DEBUG
                    )
                )

        # print(self.brain._intentparser.intent_map)
        self.brain.train()

        if len(self.brain.get_plugins()) == 0:
            msg = 'No plugins for handling speech found!'
            self._logger.error(msg)
            raise RuntimeError(msg)
        elif len(self.brain.get_all_phrases()) == 0:
            msg = 'No command phrases found!'
            self._logger.error(msg)
            raise RuntimeError(msg)

        active_stt_plugin_info = self.plugins.get_plugin(
            active_stt_slug,
            category='stt'
        )
        active_phrases = self.brain.get_plugin_phrases(passive_listen)
        active_stt_plugin = active_stt_plugin_info.plugin_class(
            'default',
            active_phrases,
            active_stt_plugin_info
        )
        if(profile.check_profile_var_exists(['active_stt', 'samplerate'])):
            active_stt_plugin._samplerate = int(
                profile.get_profile_var(['active_stt', 'samplerate'])
            )
        if(profile.check_profile_var_exists(
            ['active_stt', 'volume_normalization']
        )):
            active_stt_plugin._volume_normalization = float(
                profile.get_profile_var(['active_stt', 'volume_normalization'])
            )
        active_stt_reply = profile.get_profile_var(['active_stt', 'reply'])
        active_stt_response = profile.get_profile_var(
            ['active_stt', 'response']
        )

        # passive speech to text engine
        # Here we are checking to see if passive and
        # active modes are both using the same plugin.
        # If they are, then we create the passive plugin
        # from the active plugin for some reason, which
        # I assume means that the volume normalization
        # and samplerate settings come over as well.
        # I would think that if you have defined these
        # settings for active_stt, then simply requested
        # the same engine for passive_stt, it might be
        # confusing why these other settings are being
        # overridden as well.
        if passive_stt_slug != active_stt_slug:
            passive_stt_plugin_info = self.plugins.get_plugin(
                passive_stt_slug, category='stt'
            )
        else:
            passive_stt_plugin_info = active_stt_plugin_info

        passive_stt_plugin = passive_stt_plugin_info.plugin_class(
            'keyword',
            self.brain.get_standard_phrases(),
            passive_stt_plugin_info
        )

        if(profile.check_profile_var_exists(['passive_stt', 'samplerate'])):
            passive_stt_plugin._samplerate = int(
                profile.get_profile_var(['passive_stt', 'samplerate'])
            )
        if(profile.check_profile_var_exists(
            ['passive_stt', 'volume_normalization']
        )):
            passive_stt_plugin._volume_normalization = float(
                profile.get_profile_var(['passive_stt', 'volume_normalization'])
            )

        # We need to engage the special stt engine here, otherwise if we are
        # in "populate" mode, it will ask for information the first time it
        # is initialized. Luckily, we need a YES/NO special mode anyway.
        if special_stt_slug != active_stt_slug:
            special_stt_plugin_info = self.plugins.get_plugin(
                special_stt_slug, category='stt'
            )
        else:
            special_stt_plugin_info = active_stt_plugin_info

        yesno_stt_plugin = special_stt_plugin_info.plugin_class(
            'yes/no',
            [
                _("YES"),
                _("NO")
            ],
            special_stt_plugin_info
        )

        if(profile.check_profile_var_exists(['special_stt', 'samplerate'])):
            yesno_stt_plugin._samplerate = int(
                profile.get_profile_var(['special_stt', 'samplerate'])
            )
        if(profile.check_profile_var_exists(
            ['special_stt', 'volume_normalization']
        )):
            yesno_stt_plugin._volume_normalization = float(
                profile.get_profile_var(['special_stt', 'volume_normalization'])
            )

        # Initialize Text to speech engine
        tts_plugin_info = self.plugins.get_plugin(tts_slug, category='tts')
        tts_plugin = tts_plugin_info.plugin_class(tts_plugin_info)

        # Initialize Mic
        if use_mic == USE_TEXT_MIC:
            self.mic = local_mic.Mic()
            self._logger.info('Using local text input and output')
        elif use_mic == USE_BATCH_MIC:
            self.mic = batch_mic.Mic(
                passive_stt_plugin,
                active_stt_plugin,
                special_stt_slug,
                self.plugins,
                batch_file,
                keyword=keyword
            )
            self._logger.info('Using batched mode')
        else:
            self.mic = mic.Mic(
                input_device,
                output_device,
                active_stt_reply,
                active_stt_response,
                passive_stt_plugin,
                active_stt_plugin,
                special_stt_slug,
                self.plugins,
                tts_plugin,
                vad_plugin,
                keyword=keyword,
                print_transcript=print_transcript,
                passive_listen=passive_listen,
                save_audio=save_audio,
                save_passive_audio=save_passive_audio,
                save_active_audio=save_active_audio,
                save_noise=save_noise
            )

        self.conversation = conversation.Conversation(
            self.mic, self.brain
        )

    def settings(self):
        _ = self.gettext
        return collections.OrderedDict(
            [
                (
                    ("keyword",), {
                        "title": _("By what name would you like to call me?"),
                        "description": _("A good choice for a name would have multiple syllables and not sound like any common words."),
                        "default": "Naomi"
                    }
                ),
                (
                    ("audio_engine",), {
                        "type": "listbox",
                        "title": _("Please select an audio engine"),
                        "options": self.get_audio_engines,
                        "default": "alsa" if re.match(r'linux', platform.system().lower()) else "pyaudio"
                    }
                ),
                (
                    ("audio", "output_device"), {
                        "type": "listbox",
                        "title": _("please select an output device"),
                        "options": self.get_output_devices,
                        "validation": self.validate_output_device,
                        "default": "default"
                    }
                ),
                (
                    ("audio", "input_device"), {
                        "type": "listbox",
                        "title": _("Please select an input device"),
                        "options": self.get_input_devices,
                        "validation": self.validate_input_device,
                        "default": "default"
                    }
                ),
                (
                    ("passive_stt", "engine"), {
                        "type": "listbox",
                        "title": _("Please select a passive speech to text engine"),
                        "description": _("The passive STT engine processes everything you say near me. It is highly recommended to use an offline engine like sphinx."),
                        "options": [info.name for info in self.plugins.get_plugins_by_category("stt")],
                        "default": "sphinx"
                    }
                ),
                (
                    ("active_stt", "engine"), {
                        "type": "listbox",
                        "title": _("Please select an active speech to text engine"),
                        "description": _("After I hear my wake word, this engine processes everything you say. I recommend an offline option, but you could also use an online option like Google Voice."),
                        "options": [info.name for info in self.plugins.get_plugins_by_category("stt")],
                        "default": "sphinx"
                    }
                ),
                (
                    ("special_stt", "engine"), {
                        "type": "listbox",
                        "title": _("Please select a special speech to text engine"),
                        "description": _("Special mode is used when I am listening for a specific set of requests while in a specific plugin. An offline option should work fine here, but an online option should also work."),
                        "options": [info.name for info in self.plugins.get_plugins_by_category("stt")],
                        "default": "sphinx"
                    }
                ),
                (
                    ("tts_engine"), {
                        "type": "listbox",
                        "title": _("Please select a text to speech engine"),
                        "description": _("This provides my voice."),
                        "options": [info.name for info in self.plugins.get_plugins_by_category("tts")],
                        "default": "flite-tts"
                    }
                ),
                (
                    ("passive_listen"), {
                        "type": "boolean",
                        "title": _("Would you like to turn on passive listening?"),
                        "description": _("In normal mode, when I hear my wake word I will beep and wait for a command. In passive listening mode, I will process whatever you say with the wake word. So in normal mode, you would say 'Naomi' and I would beep and you would say 'what time is it' and I would tell you, but in passive mode you could just say 'Naomi what time is it' and I would tell you."),
                        "default": True
                    }
                ),
                (
                    ("print_transcript"), {
                        "type": "boolean",
                        "title": _("Would you like to turn on print transcript?"),
                        "description": _("In 'print transcript' mode, I will print everything I say and everything I think I hear you say to the command line. This is mostly useful for debugging."),
                        "default": True
                    }
                ),
                (
                    ("email", "address"), {
                        "type": "encrypted",
                        "title": _("Please enter your email address"),
                        "description": _("I can use your email address to check your mail and send you notifications"),
                        "validation": "email"
                    }
                ),
                (
                    ("email", "imap", "server"), {
                        "title": _("Please enter your IMAP email server url"),
                        "description": _(
                            "I need to know the url of your email server if you want me to check your emails for you"),
                        "active": lambda: True if len(
                            profile.get_profile_var(["email", "address"]).strip()) > 0 else False
                    }
                ),
                (
                    ("email", "imap", "port"), {
                        "title": _("Please enter your IMAP email server port"),
                        "description": _("I need to know I have the correct port to access your email"),
                        "default": "993",
                        "validation": "int",
                        "active": lambda: True if (
                            len(profile.get_profile_var(["email", "address"]).strip()) > 0
                        ) and (
                            len(profile.get_profile_var(["email", "imap"])) > 0
                        ) else False
                    }
                ),
                (
                    ("email", "smtp", "server"), {
                        "title": _("Please enter an SMTP email server url I can use"),
                        "description": _(
                            "I need to know the url for an SMTP email server to send emails to or for you."),
                        "active": lambda: True if len(
                            profile.get_profile_var(["email", "address"]).strip()) > 0 else False
                    }
                ),
                (
                    ("email", "smtp", "port"), {
                        "title": _("Please enter an SMTP email server port I can use"),
                        "description": _("I need to know I have the correct port to send email"),
                        "default": "587",
                        "validation": "int",
                        "active": lambda: True if (
                            len(profile.get_profile_var(["email", "address"]).strip()) > 0
                        ) and (
                            len(profile.get_profile_var(["email", "imap"])) > 0
                        ) else False
                    }
                ),
                (
                    ("email", "username"), {
                        "type": "encrypted",
                        "title": _("Please enter your email username"),
                        "description": _(
                            "Your username is normally either your full email address or just the part before the '@' symbol."),
                        "active": lambda: True if len(
                            profile.get_profile_var(["email", "address"]).strip()) > 0 else False
                    }
                ),
                (
                    ("email", "password"), {
                        "type": "password",
                        "title": _("Please enter your email password"),
                        "description": _("I need your email address in order to check your emails."),
                        "active": lambda: True if(
                            len(profile.get_profile_password(["email", "address"]).strip()) > 0
                        ) and (
                            len(profile.get_profile_var(["email", "imap"])) > 0
                        ) else False
                    }
                ),
                (
                    ("phone_number",), {
                        "type": "encrypted",
                        "title": _("Please enter your phone number"),
                        "description": _("I can use your phone number to send text messages to you")
                    }
                ),
                (
                    ("carrier",), {
                        "title": _("Please enter your carrier"),
                        "description": _("I need to know your phone carrier in order to send text messages to you from the SMTP account I'm using. If you don't know it, try sending a text message to your email account. When it arrives, it will be in the form <phone number>@<carrier> i.e. 2125551212@vtext.com"),
                        "active": lambda: True if (len(profile.get_profile_password(["phone_number"]).strip()) > 0) else False
                    }
                ),
                (
                    ("allows_email",), {
                        "type": "boolean",
                        "title": _("Would you like to let me send you emails?"),
                        "description": _("If you select 'Yes' I will send emails to you at your request, or to let you know when important things are happening."),
                        "active": lambda: True if(
                            len(profile.get_profile_password(["email", "address"]).strip())
                        ) else False,
                        "default": True
                    }
                )
            ]
        )

    # Return a list of currently installed audio engines.
    @staticmethod
    def get_audio_engines():
        global audioengine_plugins
        audioengine_plugins = pluginstore.PluginStore()
        audioengine_plugins.detect_plugins("audioengine")
        audioengines = [
            ae_info.name
            for ae_info
            in audioengine_plugins.get_plugins_by_category(
                category='audioengine'
            )
        ]
        return audioengines

    def get_output_devices(self):
        return self.get_audio_devices(audioengine.DEVICE_TYPE_OUTPUT)

    def get_input_devices(self):
        return self.get_audio_devices(audioengine.DEVICE_TYPE_INPUT)

    def validate_output_device(self, output_device_slug):
        response = True
        print(self._interface.instruction_text(
            _("Testing device by playing a sound")
        ))
        ae_info = audioengine_plugins.get_plugin(
            profile.get_profile_var(['audio_engine']),
            category='audioengine'
        )
        # AaronC 2018-09-14 Get a list of available output devices
        audio_engine = ae_info.plugin_class(ae_info, profile.get_profile())
        output_device = audio_engine.get_device_by_slug(output_device_slug)
        output_chunksize = profile.get(
            ['audio', 'output_chunksize'],
            1024
        )
        output_add_padding = profile.get(
            ['audio', 'output_padding'],
            False
        )
        filename = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "data",
            "audio",
            "beep_lo.wav"
        )
        try:
            output_device.play_file(
                filename,
                chunksize=output_chunksize,
                add_padding=output_add_padding
            )
        except Exception as e:
            print(e)
        heard = self._interface.simple_yes_no(
            _("Were you able to hear the beep?")
        )
        try:
            if not (heard):
                print(
                    self._interface.instruction_text(" ".join([
                        _("The volume on your device may be too low."),
                        _("You should be able to use 'alsamixer'"),
                        _("to set the volume level.")
                    ]))
                )
                heard = self._interface.simple_yes_no(
                    self._interface.instruction_text(
                        " ".join([
                            _("Do you want to continue now"),
                            _("and fix the volume later?")
                        ])
                    )
                )
                if not (heard):
                    response = False
        except audioengine.UnsupportedFormat as e:
            print(self._interface.alert_text(str(e)))
            print(
                self._interface.instruction_text(
                    _("Output format not supported on this device.")
                )
            )
            print(
                self._interface.instruction_text(
                    _("Please choose a different device.")
                )
            )
            print("")
            response = False
        return response

    def validate_input_device(self, input_device_slug):
        # AaronC 2018-09-14 Initialize AudioEngine
        ae_info = audioengine_plugins.get_plugin(
            profile.get_profile_var(['audio_engine']),
            category='audioengine'
        )
        # AaronC 2018-09-14 Get a list of available output devices
        audio_engine = ae_info.plugin_class(ae_info, profile.get_profile())
        # AaronC 2018-09-14 Get the input device
        input_device_slug = profile.get_profile_var(["audio", "input_device"])
        if not input_device_slug:
            input_device_slug = audio_engine.get_default_device(output=False).slug
        response = True
        # try recording a sample
        test = self._interface.simple_yes_no(" ".join([
            _("Would you like me to test your selection"),
            _("by recording your voice and playing it back to you?")
        ]))
        while test:
            test = False
            # FIXME AaronC Sept 16 2018
            # The following are defaults. They should be read
            # from the proper locations in the profile file if
            # they have been set.
            threshold = 10  # 10 dB
            input_chunks = profile.get_profile_var(
                ['audio', 'input_chunksize'],
                1024
            )
            input_bits = profile.get_profile_var(
                ['audio', 'input_samplewidth'],
                16
            )
            input_channels = profile.get_profile_var(
                ['audio', 'input_channels'],
                1
            )
            input_rate = profile.get_profile_var(
                ['audio', 'input_samplerate'],
                16000
            )

            output_chunksize = profile.get_profile_var(
                ['audio', 'output_chunksize'],
                1024
            )
            output_add_padding = profile.get_profile_var(
                ['audio', 'output_padding'],
                False
            )
            input_device = audio_engine.get_device_by_slug(
                profile.get_profile_var(['audio', 'input_device'])
            )
            output_device = audio_engine.get_device_by_slug(
                profile.get_profile_var(["audio", "output_device"])
            )
            frames = collections.deque([], 30)
            recording = False
            recording_frames = []
            filename = os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ),
                "data",
                "audio",
                "beep_hi.wav"
            )
            if(os.path.isfile(filename)):
                output_device.play_file(
                    filename,
                    chunksize=output_chunksize,
                    add_padding=output_add_padding
                )
            started = False
            for frame in input_device.record(
                input_chunks,
                input_bits,
                input_channels,
                input_rate
            ):
                frames.append(frame)
                # Moved this down here because sometimes it takes a second
                # for the sound card to actually start recording
                if not started:
                    started = True
                    print(
                        self._interface.instruction_text(
                            _("Please speak into the mic now")
                        )
                    )

                if not recording:
                    snr = _snr(input_bits, threshold, [frame])
                    if snr >= threshold:
                        print(
                            self._interface.alert_text(
                                _("Sound detected - recording")
                            )
                        )
                        recording = True
                        if len(frames) > 30:
                            recording_frames = list(frames)[-30:]
                        else:
                            recording_frames = list(frames)
                    elif len(frames) >= frames.maxlen:
                        # Threshold not reached. Update.
                        soundlevel = float(audioop.rms(b"".join(frames), 2))
                        if (soundlevel < threshold):
                            print(self._interface.alert_text(" ".join([
                                _("No sound detected."),
                                _("Setting threshold from {t} to {s}").format(
                                    t=threshold,
                                    s=soundlevel
                                )
                            ])))
                            threshold = soundlevel
                else:
                    recording_frames.append(frame)
                    if len(recording_frames) > 20:
                        # Check if we are below threshold again
                        last_snr = _snr(
                            input_bits,
                            threshold,
                            recording_frames[-10:]
                        )
                        if((
                            last_snr <= threshold
                        )or(
                            len(recording_frames) > 60
                        )):
                            # stop recording
                            recording = False
                            print(
                                self._interface.success_text(
                                    _("Recorded %d frames")
                                    % len(recording_frames)
                                )
                            )
                            break
            if len(recording_frames) > 20:
                response = False
                replay = True
                while (replay):
                    response = True
                    with tempfile.NamedTemporaryFile(mode='w+b') as f:
                        wav_fp = wave.open(f, 'wb')
                        wav_fp.setnchannels(input_channels)
                        wav_fp.setsampwidth(int(input_bits / 8))
                        wav_fp.setframerate(input_rate)
                        fragment = b"".join(frames)
                        wav_fp.writeframes(fragment)
                        wav_fp.close()
                        output_device.play_file(
                            f.name,
                            chunksize=output_chunksize,
                            add_padding=output_add_padding
                        )
                    heard = self._interface.simple_yes_no(
                        _("Did you hear yourself?")
                    )
                    if (heard):
                        replay = False
                        response = True
                    else:
                        replay = self._interface.simple_yes_no(
                            _("Replay?")
                        )
                        if (not replay):
                            skip = self._interface.simple_yes_no(
                                _("Do you want to skip this test and continue?")
                            )
                            if (skip):
                                replay = False
                                heard = True
                                response = True
                                test = False
                            else:
                                replay = False
                                heard = True
                                response = False
                                test = False
        return response

    @staticmethod
    def get_audio_devices(device_type):
        ae_info = audioengine_plugins.get_plugin(
            profile.get_profile_var(['audio_engine']),
            category='audioengine'
        )
        # AaronC 2018-09-14 Get a list of available output devices
        audio_engine = ae_info.plugin_class(ae_info, profile.get_profile())
        # AaronC 2018-09-14 Get a list of available input devices
        input_devices = [device.slug for device in audio_engine.get_devices(
            device_type=device_type
        )]
        return input_devices

    def list_audio_devices(self):
        for device in self.audio.get_devices():
            device.print_device_info(
                verbose=(self._logger.getEffectiveLevel() == logging.DEBUG))

    # This is a standardized function for getting all the plugins available
    # from all the repositories the user has enabled in their profile
    def get_remote_plugin_repositories(self, plugins=None):
        csvfile = []
        repositories = profile.get(
            ['plugin_repositories'],
            {DEFAULT_PLUGIN_URL: "Enabled"}
        )
        for url in repositories:
            if repositories[url] == 'Enabled':
                self._logger.info("Reading {}".format(url))
                # It would be good if we could actually read the csv file line
                # by line rather than reading it all into memory, but that
                # might require some custom code. For right now, we'll use the
                # python tools.
                # I should set up a context manager for this anyway, since I
                # am processing multiple urls.
                # The nosec comment on the next line has to be there to say
                # "Yes, I know I'm doing something unsecure" or codacy has a
                # fit
                with urllib.request.urlopen(urllib.request.Request(url)) as f:  #nosec
                    file_contents = f.read().decode('utf-8')
                for line in csv.DictReader(
                    io.StringIO(file_contents),
                    delimiter=',',
                    quotechar='"'
                ):
                    if line not in csvfile:
                        csvfile.append(line)
        # Because the plugin information can be coming from multiple sources,
        # we are now in a situation where different versions of a plugin can
        # be listed in multiple repositories, and there is definitely the
        # possibility of two different repositories having different plugins
        # with the same name, or different versions of the same plugin.
        return csvfile

    # Functions for plugin management
    def list_active_plugins(self):
        plugins = self.plugins.get_plugins()
        len_name = max(len(info.name) for info in plugins)
        len_version = max(len(info.version) for info in plugins)
        # Sort these alphabetically by name
        plugins_sorted = {}
        for info in plugins:
            plugins_sorted[info.name.lower()] = info
        for name in sorted(plugins_sorted):
            info = plugins_sorted[name]
            print(
                "{} {} - {}".format(
                    info.name.ljust(len_name),
                    ("(v%s)" % info.version).ljust(len_version),
                    info.description
                )
            )

    def list_available_plugins(self, categories):
        installed_plugins = {}
        for category in self.plugins._categories_map:
            # Get a list of installed plugins in each category
            superclass = self.plugins._categories_map[category]
            for info in self.plugins._plugins.values():
                if issubclass(info.plugin_class, superclass):
                    if(category not in installed_plugins):
                        installed_plugins[category] = {}
                    installed_plugins[category][info.name] = info.version
        print(_("Available Plugins:"))
        # Get the list of available plugins:
        # NaomiProject: https://raw.githubusercontent.com/NaomiProject/naomi-plugins/master/plugins.csv
        # aaronchantrill: https://raw.githubusercontent.com/aaronchantrill/naomi-plugins/master/plugins.csv
        csvfile = self.get_remote_plugin_repositories()
        print_plugins = {}
        flat_cat = [y for x in categories for y in x]
        for row in csvfile:
            if len(flat_cat):
                if(row["Category"] in [y for x in categories for y in x]):
                    print_plugins[row["Name"].lower()] = row
            else:
                print_plugins[row["Name"].lower()] = row
        if(len(print_plugins) == 0):
            print(_("Sorry, no plugins matched"))
        else:
            for name in sorted(print_plugins):
                pluginstore.printplugin(print_plugins[name], installed_plugins)

    # Right now what install_plugins does is git clone the plugin into the
    # user's plugin dir (~/.naomi/plugins) and then run install.py if there
    # is one, or python_requirements.txt if there is one.
    def install_plugins(self, plugins):
        flat_plugins = [y for x in plugins for y in x]
        csvfile = self.get_remote_plugin_repositories(flat_plugins)
        for row in csvfile:
            # Keeps track of any failure inside the naming while loop
            fail = False
            if(row['Name'] in flat_plugins):
                print(_('Installing {}...').format(row['Name']))
                # install it to the user's plugin directory
                install_dir = paths.sub(
                    os.path.join(
                        'plugins',
                        row['Category']
                    )
                )
                # Make sure the install dir exists
                if not os.path.isdir(install_dir):
                    os.makedirs(install_dir)
                # We aren't capturing the actual name of the directory.
                # The name of the directory does not matter, so we should just
                # create one. Replace any spaces in the plugin name with
                # underscores.
                install_name = re.sub('\W', '', re.sub('\s', '_', row['Name']))
                install_to_base = os.path.join(install_dir, install_name)
                install_to = install_to_base
                rev = 0
                installed_url = ""
                while(os.path.isdir(install_to)):
                    # Check if the git fetch url is the same. If so, then
                    # this is the same plugin and just needs to be updated.
                    # If not, then this is a different plugin, so rename the
                    # install_to directory.
                    installed_url = ""
                    cmd = [
                        "git",
                        '-C', install_to,
                        "remote", "-v"
                    ]
                    completed_process = run_command(cmd, 1)
                    # # This is how you can get the URL from the info file
                    # # instead of git:
                    # installed_url = self.plugins.parse_plugin(install_to)

                    # This could easily fail, if this directory is not
                    # actually a git directory
                    if(completed_process.returncode == 0):
                        installed_url = completed_process.stdout.decode(
                            "UTF-8"
                        ).split("\n")[0].split("\t")[1].split()[0]
                    if(strcmpci(
                        installed_url,
                        row['Repository']
                    )):
                        # It's the same plugin
                        # Just go ahead and reset the head and do
                        # a git pull origin.
                        # The following assumes there is a master branch:
                        cmd = [
                            'git',
                            '-C', install_to,
                            'checkout',
                            'master'
                        ]
                        completed_process = run_command(cmd, 2)
                        if(completed_process.returncode == 0):
                            # break out of the loop
                            break
                        else:
                            print(_('Unable to reset plugin "{}": {}').format(
                                row['Name'],
                                completed_process.stderr.decode("UTF-8")
                            ))
                            fail = True  # next line from csv
                            break
                        cmd = [
                            'git',
                            '-C', install_to,
                            'pull',
                            'origin'
                        ]
                        completed_process = run_command(cmd, 2)
                        if(completed_process.returncode == 0):
                            # break out of the while loop
                            break
                        else:
                            print(_('Unable to update plugin "{}": {}').format(
                                row['Name'],
                                completed_process.stderr.decode("UTF-8")
                            ))
                            fail = True  # next line from csv
                            break
                    else:
                        rev += 1
                        install_to = "_".join([install_to_base, str(rev)])
                if(fail):
                    continue
                if(not os.path.isdir(install_to)):
                    cmd = [
                        'git',
                        'clone',
                        row['Repository'],
                        install_to
                    ]
                    completed_process = run_command(cmd, 2)
                    if(completed_process.returncode != 0):
                        print(completed_process.stderr.decode("UTF-8"))
                if(os.path.isdir(install_to)):
                    # checkout the specific commit
                    cmd = [
                        'git',
                        '--git-dir={}/.git'.format(install_to),
                        '--work-tree={}'.format(install_to),
                        'checkout',
                        row['Commit']
                    ]
                    completed_process = run_command(cmd, 2)
                    if(completed_process.returncode != 0):
                        print(completed_process.stderr.decode("UTF-8"))
                        # At this point, we have a potentially rogue
                        # copy of the plugin, with code that has not
                        # been vetted.
                        # A developer could easily force this condition
                        # by simply deleting the vetted commit from their
                        # repository. At that point, anyone who installed
                        # the plugin would get whatever the current state
                        # is.
                        print(_("Failed to set head to the vetted commit"))
                        print(_("Deleting {}".format(install_to)))
                        shutil.rmtree(install_to)
                    else:
                        # check and see if there is an install.py file
                        install_file = os.path.join(install_to, "install.py")
                        if os.path.isfile(install_file):
                            # run that
                            run_command(install_file)
                        else:
                            required_file = os.path.join(
                                install_dir,
                                "python_required.txt"
                            )
                            if os.path.isfile(required_file):
                                # Install any python packages required
                                cmd = [
                                    'pip3',
                                    'install',
                                    '--user',
                                    '--requirement',
                                    required_file
                                ]
                                run_command(cmd)
                        # Since the plugin will request its own settings each
                        # time it is run with settings missing, no need to set
                        # that up now.
                        self.plugins.detect_plugins()
                        self.enable_plugins([[row['Name']]])
                        print(_('Plugin "{}" installed to {}').format(
                            row['Name'],
                            install_to
                        ))

    def update_plugins(self, plugins):
        flat_plugins = [y for x in plugins for y in x]
        csvfile = self.get_remote_plugin_repositories()
        for row in csvfile:
            if(row['Name'] in flat_plugins):
                # Find the plugin
                found_plugin = False
                for info in self.plugins._plugins.values():
                    if(info.name == row["Name"]):
                        found_plugin = True
                        plugin_dir = info._path
                        # FIXME check if the urls are the same, if not, then
                        # this is probably a different plugin with the same
                        # name.
                        # It probably makes the most sense to check the
                        # git remote -v origin url, since that is the one
                        # actually used, and the url in info may be unreliable
                        print(_("Updating {}").format(row["Name"]))
                        if(info.version == row['Version']):
                            print(
                                _("{} versions identical ({}), updating anyway").format(
                                    row['Name'],
                                    info.version
                                )
                            )
                        else:
                            print(_("Updating {} from {} to {}").format(
                                row["Name"],
                                info.version,
                                row["Version"]
                            ))
                        # checkout the specific commit
                        cmd = [
                            'git',
                            '--git-dir={}/.git'.format(plugin_dir),
                            '--work-tree={}'.format(plugin_dir),
                            'checkout',
                            row['Commit']
                        ]
                        completed_process = run_command(cmd, 2)
                        if(completed_process.returncode != 0):
                            print(completed_process.stderr.decode("UTF-8"))
                            print(_("Failed to set head to the vetted commit"))
                        else:
                            # check and see if there is an install.py file
                            install_file = os.path.join(
                                plugin_dir,
                                "install.py"
                            )
                            if os.path.isfile(install_file):
                                # run that
                                run_command(install_file)
                            else:
                                required_file = os.path.join(
                                    plugin_dir,
                                    "python_required.txt"
                                )
                                if os.path.isfile(required_file):
                                    # Install any python packages required
                                    cmd = [
                                        'pip3',
                                        'install',
                                        '--user',
                                        '--requirement',
                                        required_file
                                    ]
                                    run_command(cmd)
                            # Since the plugin will request its own settings
                            # each time it is run with settings missing, no
                            # need to set that up now.
                            self.plugins.detect_plugins()
                            self.enable_plugins([[row['Name']]])
                            print(_('Plugin "{}" Updated').format(row['Name']))
                if not found_plugin:
                    print(_("Plugin {} was not found.").format(row["Name"]))
                    print(_("Are you sure it is installed?"))

    # I don't know what we want this to do. If this is a plugin in the user's
    # directory, then delete it. If it is a directory in the main naomi dir,
    # then disable it.
    # If silent is set to True, then do not prompt the user. This allows
    # this function to be used from a script.
    def remove_plugins(self, plugins, silent=False):
        flat_plugins = [y for x in plugins for y in x]
        for plugin in flat_plugins:
            plugin_found = False
            for info in self.plugins._plugins.values():
                if(info.name == plugin):
                    plugin_found = True
                    if(paths.sub() == info._path[:len(paths.sub())]):
                        print('Removing plugin "{}"'.format(info.name))
                        if(silent or self._interface.simple_yes_no("Are you sure?")):
                            # FIXME Remove the plugin line from profile.yml
                            # This would require using del or pop to remove
                            # the key, but would have to traverse the tree
                            # until we reach the key first.
                            print(_("Removing directory: {}").format(info._path))
                            shutil.rmtree(info._path)
                            plugin_category = info._path.split(os.path.sep)[
                                len(info._path.split(os.path.sep)) - 2
                            ]
                            profile.remove_profile_var([
                                'plugins',
                                plugin_category,
                                info.name
                            ])
                            profile.save_profile()
                    else:
                        self.disable_plugins([[info.name]])
            if(not plugin_found):
                print(_('Could not locate plugin "{}" ({})').format(
                    plugin,
                    _("has it been disabled?")
                ))

    @staticmethod
    def enable_plugins(plugins):
        flat_plugins = [y for x in plugins for y in x]
        plugins_enabled = 0
        for plugin in flat_plugins:
            plugin_enabled = False
            # Being disabled, the plugin won't be in self.plugins
            # We need to search every plugin category in profile.plugins
            for category in profile.get_profile_var(['plugins']):
                if(plugin in profile.get_profile_var(['plugins', category])):
                    if(profile.get_profile_var([
                        'plugins',
                        category,
                        plugin
                    ]) == 'Enabled'):
                        print(_('Plugin "{}" is enabled').format(plugin))
                        plugin_enabled = True
                    else:
                        profile.set_profile_var(
                            [
                                'plugins',
                                category,
                                plugin
                            ],
                            'Enabled'
                        )
                        print(_('Enabled plugin "{}"').format(plugin))
                        plugin_enabled = True
                        plugins_enabled += 1
            if(not plugin_enabled):
                print(_('Unable to enable plugin "{}"').format(plugin))
        if(plugins_enabled > 0):
            profile.save_profile()

    def disable_plugins(self, plugins):
        flat_plugins = [y for x in plugins for y in x]
        plugins_disabled = 0
        # We don't know what category the plugin is in from just the name
        # so the first thing we have to do is figure out the category
        plugin_category = None
        # Being enabled, the plugin should appear in self.plugins
        for plugin in flat_plugins:
            plugin_disabled = False
            for info in self.plugins._plugins.values():
                if(info.name == plugin):
                    plugin_category = info._path.split(os.path.sep)[
                        len(info._path.split(os.path.sep)) - 2
                    ]
            if(not plugin_category):
                # If we were not able to find the plugin in self.plugins
                # check the profile directly. The plugin may have been skipped
                # due to a syntax error or missing depenency.
                for category in profile.get_profile_var(['plugins']):
                    if(plugin in profile.get_profile_var([
                        'plugins',
                        category
                    ])):
                        plugin_category = category
            if(plugin_category):
                if(profile.get_profile_var([
                    'plugins',
                    plugin_category,
                    plugin
                ]) == 'Disabled'):
                    print(_('Plugin "{}" is disabled').format(plugin))
                    plugin_disabled = True
                else:
                    profile.set_profile_var(
                        [
                            'plugins',
                            plugin_category,
                            plugin
                        ],
                        'Disabled'
                    )
                    print(_('Disabled plugin "{}"').format(plugin))
                    plugin_disabled = True
                    plugins_disabled += 1
            if(not plugin_disabled):
                print(_('Unable to disable plugin "{}"').format(plugin))
        if(plugins_disabled > 0):
            profile.save_profile()

    def run(self):
        self.conversation.askName()
        self.conversation.greet()
        self.conversation.handleForever()
