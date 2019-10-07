# -*- coding: utf-8 -*-
import csv
import io
import logging
import os
import re
import shutil
import urllib
from . import audioengine
from . import brain
from . import commandline as interface
from . import i18n
from . import paths
from . import pluginstore
from . import populate
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
        if repopulate:
            populate.run()
        if(profile.get_arg("Profile_missing", False)):
            print("Your config file does not exist.")
            text_input = input(
                " ".join([
                    "Would you like to answer a few ",
                    "questions to create a new one? (y/N): "
                ])
            )
            if(text_input.strip()[:1].upper() == "Y"):
                populate.run()
            else:
                print("Cannot continue. Exiting.")
                quit()
        # FIXME We still need this next line because a lot of
        # plugins still use self.config
        self.config = profile.get_profile()
        translations = i18n.parse_translations(paths.data('locale'))
        translator = i18n.GettextMixin(translations)
        _ = translator.gettext

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

        keyword = profile.get_profile_var(['keyword'], 'NAOMI')
        self._logger.info("Using keyword '{}'".format(keyword))

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
        # Load plugins
        self.plugins = pluginstore.PluginStore()
        self.plugins.detect_plugins()

        # load visualizations
        visualizations.load_visualizations(self)

        # Initialize AudioEngine
        ae_info = self.plugins.get_plugin(
            audio_engine_slug,
            category='audioengine'
        )
        self.audio = ae_info.plugin_class(ae_info, self.config)
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
        try:
            device_slug = self.config['audio']['output_device']
        except KeyError:
            device_slug = self.audio.get_default_device(output=True).slug
            self._logger.warning(
                " ".join([
                    "output_device not specified in profile,",
                    "defaulting to '{0:s}' (Possible values: {1:s})"
                ]).format(device_slug, ', '.join(devices))
            )
        try:
            output_device = self.audio.get_device_by_slug(device_slug)
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
                plugin = info.plugin_class(info, self.config)
            except Exception as e:
                self._logger.warning(
                    "Plugin '%s' skipped! (Reason: %s)", info.name,
                    e.message if hasattr(e, 'message') else 'Unknown',
                    exc_info=(
                        self._logger.getEffectiveLevel() == logging.DEBUG
                    )
                )
            else:
                self.brain.add_plugin(plugin)
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
            active_stt_plugin_info,
            self.config
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
            self.brain.get_standard_phrases() + [keyword],
            passive_stt_plugin_info,
            self.config
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

        active_stt_reply = profile.get_profile_var(['active_stt', 'reply'])
        active_stt_response = profile.get_profile_var(
            ['active_stt', 'response']
        )
        # pdb.set_trace()
        tts_plugin_info = self.plugins.get_plugin(tts_slug, category='tts')
        tts_plugin = tts_plugin_info.plugin_class(tts_plugin_info, self.config)

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
                self.config,
                keyword=keyword,
                print_transcript=print_transcript,
                passive_listen=passive_listen,
                save_audio=save_audio,
                save_passive_audio=save_passive_audio,
                save_active_audio=save_active_audio,
                save_noise=save_noise
            )

        self.conversation = conversation.Conversation(
            self.mic, self.brain, self.config)

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
            print("{} {} - {}".format(
                info.name.ljust(len_name),
                (
                    "(v%s)" % info.version).ljust(len_version),
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
