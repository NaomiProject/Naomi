# Changelog

## v3.0 (Work in progress)

### Core updates

#### Python3

Converted Naomi to Python3

#### Print Transcript

Naomi has the ability to print a transcript of what it says and hears (useful for debugging). Either run naomi with the "--print-transcript" flag or set "print_transcript: True" in profile.yml.

#### VAD Plugin

Created a new plugin type: VADPlugin, which is used to detect voice activity specifically to allow Naomi to use webrtc_vad. Re-wrote the current Sound Noise Ratio method as a pure Python plugin that can be used as a default (snr_vad).

#### Profile API

Added an API for accessing profile variables. Instead of using:

```py
try:
    input_channels=profile['audio']['input_channels']
except NameException:
    input_channels=1
```

You can now just use

```py
from naomi import profile
...
input_channels=profile.get(['audio','input_channels'], 1)
```

This API includes the following commands:

* set_arg(name, value)
* get_arg(name, default=None)
* set_profile(custom_profile)
* get_profile(command="")
* save_profile()
* get(path, default=None) - alias for get_profile_var
* get_profile_var(path, default=None)
* set_profile_var(path, value)
* remove_profile_var(path)
* get_password(path, default=None) - alias for get_profile_password
* get_profile_password(path, default=None)
* set_profile_password(path, value)
* get_profile_flag(path, default=None) - retrieves boolean
* exists(path) - alias for get_profile_var_exists
* get_profile_var_exists(path)
* validate(definition, response)

This also means that it is no longer necessary to pass a variable containing a copy of the profile to each module. The profile is stored in a static variable and available to any module that imports the profile module.

#### Naomi user directory moved

Naomi's user configuration files have moved from ~/.naomi to ~/.config/naomi to better follow the current Linux protocol. Naomi's profile.yml file has moved from ~/.naomi/profile.yml to ~/.config/naomi/configs/profile.yml

#### Plugin settings

The populate.py script has been replaced with settings that exist within the individual plugins. This way, a plugin author needs information from the user to get the plugin working, this information can be encoded within the plugin and not have to be added to a file in the Naomi core.
Settings have the following structure:

```py
(
    ("path", "to", "setting",), {
        'type': type, # textbox, listbox, combobox, boolean, password, encrypted
        'title': title,
        'description': description,
        'options': [option1, option2], # required for listbox, used by listbox and combobox
        'validation': validationfunction,
        'active': activefunction
    }
)
```

#### Ability to disable plugins from within profile.yml

Plugins are listed within profile.yml and can be enabled or disabled by setting the associated value.

#### Passive Listen

Naomi can be set to collect audio, and if audio contains the wakeword, use the active listener to scan the captured audio, allowing a more natural conversation style. Requires setting the "passive_listen: true" value in profile.yml or running Naomi with the --passive-listen flag.

#### Asynchronous Say

Talking can happen in a separate thread so Naomi can listen while talking, allowing the user to stop Naomi in the middle of a response by saying "Naomi Stop". Unfortunately, with most audio setups, this causes Naomi to react to its own voice, so this is disabled by default while working out how to filter out the sound of Naomi speaking. Currently best used with either headphones or a USB conference phone with hardware level feedback filtering. Activated by either passing the "--listen-while-talking" flag or setting "listen_while_talking: true" in profile.yml.

#### Syncronous Mic

In the original jasper-dev project, the wake word scanner was using three asynchronous listeners, all constantly checking the audio stream for the wake word. After detecting the wake word, the audio stream would start recording. Changing this This freed up a lot of resources used in wake word scanning, allowed the wake word to appear anywhere in a command, and made it easier to save audio for training VAD noise detection and passive listeners.

#### audiolog

Ability to save audio captured by Naomi for STT training purposes.

#### NaomiSTTTrainer.py

Plugin based system for training Naomi STT engines from audio captured by Naomi during use.

#### Switched from pygettext to xgettext

In the update_translations.py script, switched from pygettext to xgettext because it is on the path and the location does not change when Python updates. Also cleaned duplicate lines out of the resulting .po file headers.

#### Naomi Plugin Exchange - Core Based

Developed a method for 3rd party plugin authors to list their plugins in Naomi, so plugins can be easily searched and installed from within Naomi.
Current command line flags include

* --install \<plugin>
* --update [\<plugin>]
* --remove \<plugin>
* --disable \<plugin>
* --enable \<plugin>
* --list-active-plugins
* --list-available-plugins

#### Naomi Plugin Exchange - Web Based

Developed a web based [NPE](https://projectnaomi.com/plugins/) for exploring plugins written by or endorsed by the Naomi Project. Plugins are labeled as "included" if they come pre-installed with Naomi, or instructions on how to install will be shown if it's an endorsed plugin.

#### Naomi Plugin Exchange Editor (NPEeditor) - Web Based

Developed a web based [plugin editor](https://npeeditor.projectnaomi.com/) to give developers a framework and kickstart on plugin development based on the information provided in the form. This generates a zip file that contains a properly structured and setup plugin that is compatible with the Core & Web based NPE systems.

#### Visualizations Plugin

This is a way of designing plugins to provide feedback for Naomi core processes. It requires creating a run_visualization call that references one or more visualization plugins that may or may not be loaded.

#### TTI Plugin

Created a Text to Intent plugin type and created a word frequency/edit distance replacement for the current intent parsing system. Wrote plugins allowing the user to use Naomi with the Adapt or Padatious intent parsers in addition to our in house intent parser. Stabilized the methods for designing an intent within a SpeechHandler plugin.

#### Multiple wakewords

Naomi now supports multiple wake words. Naomi accepts the first wake word as the primary wake word, but will respond to other wake words as well.

#### naomi-setup.sh script

This script went through a lot of permutations this year. Right now it will create a working Naomi setup on any Debian derivative.

#### Oneline Installer

Along with the new setup script, there is now a one line command you can execute in any Linux based terminal that will setup and install Naomi based on OS & version.

#### Email access routines moved to app_utils

There should no longer be any reason for plugin developers to need direct access to the user's email username or password. Routines for sending and checking emails are now embedded in app_utils. This include:

* check_imap_config()
* check_smtp_config()
* send_email(SUBJECT, BODY, TO)
* email_user(SUBJECT="", BODY="")
* fetch_emails(since=None, email_filter="", markRead=False, limit=None)
* get_sender(msg)
* get_sender_email(msg)
* get_message_text(msg)
* mark_read(msg)
* get_most_recent_date(emails)

### Plugin updates

#### Updated to MPD2

Fixed a few issues with the MPDClient plugin, including updating to the mpd2 module, getting playlists to start playing when they are loaded, and getting Naomi to pause music before speaking when in music mode.

#### Fixed Google Cloud STT and TTS

Thanks to Ole who got these working

#### Replacement weather plugin

Replaced the default Yahoo weather plugin with WWIS weather.

#### Pocketsphinx self setup

Pocketsphinx will now automatically download the standard language model for English, French, or German from the [CMUSphinx standard language models](https://github.com/NaomiProject/CMUSphinx_standard_language_models.git) repository when first loaded.

#### v2.2 (31/12/2018)

*No changelog for this release.*

#### v2.1 (13/09/2018)

*No changelog for this release.*
