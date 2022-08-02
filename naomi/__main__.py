# -*- coding: utf-8 -*-
import os
import sys
import logging
import logging.handlers
import argparse
from . import application
from . import app_utils
from . import coloredformatting as cf
from . import i18n
from . import paths
from . import profile


logo = cf.naomidefaults.logo
sto = cf.naomidefaults.sto
USE_STANDARD_MIC = application.USE_STANDARD_MIC
USE_TEXT_MIC = application.USE_TEXT_MIC
USE_BATCH_MIC = application.USE_BATCH_MIC


def main(args=None):
    parser = argparse.ArgumentParser(description='Naomi Voice Control Center')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show debug messages'
    )
    parser.add_argument(
        '--passive-listen',
        action='store_true',
        help='Check for keyword and command in same input'
    )
    parser.add_argument(
        '--repopulate',
        action='store_true',
        help='Rebuild configuration profile'
    )
    parser.add_argument(
        '--save-passive-audio',
        action='store_true',
        help='Save passive recordings and transcripts for training'
    )
    parser.add_argument(
        '--save-active-audio',
        action='store_true',
        help='Save active recordings and transcripts for training'
    )
    parser.add_argument(
        '--save-noise',
        action='store_true',
        help='Save noise recordings for training'
    )
    parser.add_argument(
        '--save-audio',
        action='store_true',
        help=' '.join([
            'Save passive, active and noise audio recordings',
            'and transcripts for training'
        ])
    )
    parser.add_argument(
        '--listen-while-talking',
        action='store_true',
        help=' '.join([
            'Continue to listen while talking. This allows you to interrupt',
            'Naomi, but may also lead to Naomi attempting to respond to its',
            'own voice.'
        ])
    )

    # Plugin Repository Management
    pr_man = parser.add_mutually_exclusive_group(required=False)
    pr_man.add_argument(
        '--list-available-plugins',
        nargs='*',
        dest='list_available',
        action='append',
        help='List available plugins (by category) and exit'
    )
    pr_man.add_argument(
        '--install',
        nargs=1,
        dest='plugins_to_install',
        action='append',
        help='Install plugin and exit'
    )
    pr_man.add_argument(
        '--update',
        nargs="?",
        dest='plugins_to_update',
        action='append',
        help='Update specific plugin or all plugins and exit'
    )
    pr_man.add_argument(
        '--remove',
        nargs=1,
        dest='plugins_to_remove',
        action='append',
        help='Remove (uninstall) plugins and exit'
    )
    pr_man.add_argument(
        '--disable',
        nargs=1,
        dest='plugins_to_disable',
        action='append',
        help='Disable plugins and exit'
    )
    pr_man.add_argument(
        '--enable',
        nargs=1,
        dest='plugins_to_enable',
        action='append',
        help='Enable plugins and exit'
    )
    list_info = parser.add_mutually_exclusive_group(required=False)
    list_info.add_argument(
        '--list-active-plugins',
        action='store_true',
        help='List active plugins and exit'
    )
    list_info.add_argument(
        '--list-audio-devices',
        action='store_true',
        help='List audio devices and exit'
    )
    # input options
    mic_mode = parser.add_mutually_exclusive_group(required=False)
    mic_mode.add_argument(
        '--local',
        action='store_true',
        help='Use text input/output instead of verbal interface'
    )
    mic_mode.add_argument(
        '--batch',
        dest='batch_file',
        metavar="FILE",
        type=argparse.FileType('r'),
        help=' '.join([
            'Batch mode using a text file with references to audio files'
        ])
    )
    mic_mode.add_argument(
        '--print-transcript',
        action='store_true',
        help='Prints a transcription of things Naomi says and thinks it hears'
    )
    p_args = parser.parse_args(args)
    loglevel = logging.ERROR
    if(p_args.debug):
        loglevel = logging.DEBUG
    else:
        if profile.get(['logging', 'level'], 'error') == "debug":
            loglevel = logging.DEBUG
    logfile = profile.get(['logging', 'logfile'], paths.sub('Naomi.log'))
    handler = logging.handlers.TimedRotatingFileHandler(
        logfile,
        interval=24,
        when="h",
        backupCount=5
    )
    if(os.path.isfile(logfile)):
        handler.doRollover()
    logging.basicConfig(
        level=loglevel,
        filename=logfile
    )
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    language = profile.get_profile_var(['language'])
    if(not language):
        language = 'en-US'
        logger.warn(
            ' '.join([
                'language not specified in profile,',
                'using default ({})'.format(language)
            ])
        )
    translations = i18n.parse_translations(paths.data('locale'))
    translator = i18n.GettextMixin(translations)
    _ = translator.gettext
    print(_("Logging to {}").format(logfile))

    print(logo)
    print("      ___           ___           ___           ___                  ")
    print("     /\__\         /\  \         /\  \         /\__\          ___    ")
    print("    /::|  |       /::\  \       /::\  \       /::|  |        /\  \   ")
    print("   /:|:|  |      /:/\:\  \     /:/\:\  \     /:|:|  |        \:\  \  ")
    print("  /:/|:|  |__   /::\~\:\  \   /:/  \:\  \   /:/|:|__|__      /::\__\ ")
    print(" /:/ |:| /\__\ /:/\:\ \:\__\ /:/__/ \:\__\ /:/ |::::\__\    /:/\/__/ ")
    print(" \/__|:|/:/  / \/__\:\/:/  / \:\  \ /:/  / \/__/~~/:/  / __/:/  /    ")
    print("     |:/:/  /       \::/  /   \:\  /:/  /        /:/  / /\/:/  /     ")
    print("     |::/  /        /:/  /     \:\/:/  /        /:/  /  \::/__/      ")
    print("     /:/  /        /:/  /       \::/  /        /:/  /    \:\__\      ")
    print("     \/__/         \/__/         \/__/         \/__/      \/__/      ")
    print(sto)

    # Select Mic
    used_mic = USE_STANDARD_MIC
    if p_args.local:
        # Use Local text mic
        used_mic = USE_TEXT_MIC
    elif p_args.batch_file is not None:
        # Use batched mode mic, pass a file too
        used_mic = USE_BATCH_MIC

    # listen
    # AaronC 2019-05-29
    # This keeps an argument in a static location
    # so we don't have to keep passing it from library
    # to library. We need to know if the user wants to
    # re-run populate.py when we examine the settings
    # variable while instantiating plugin objects
    # in plugin.GenericPlugin.__init__()
    profile.set_arg("repopulate", p_args.repopulate)

    if(p_args.listen_while_talking):
        profile.set_arg("listen_while_talking", 'Yes')
    else:
        profile.set_arg(
            "listen_while_talking",
            app_utils.is_positive(
                profile.get(
                    ["listen_while_talking"],
                    'false'
                )
            )
        )

    # Run Naomi
    app = application.Naomi(
        use_mic=used_mic,
        batch_file=p_args.batch_file,
        repopulate=p_args.repopulate,
        print_transcript=p_args.print_transcript,
        passive_listen=p_args.passive_listen,
        save_audio=p_args.save_audio,
        save_passive_audio=p_args.save_passive_audio,
        save_active_audio=p_args.save_active_audio,
        save_noise=p_args.save_noise
    )
    if p_args.list_audio_devices:
        app.list_audio_devices()
        sys.exit(0)
    if p_args.list_active_plugins:
        print(_("Active Plugins:"))
        active_plugins = app.npe.list_active_plugins()
        len_name = max(len(active_plugins[info].name) for info in active_plugins)
        len_version = max(len(active_plugins[info].version) for info in active_plugins)
        for name in sorted(active_plugins):
            info = active_plugins[name]
            print(
                "{} {} - {}".format(
                    info.name.ljust(len_name),
                    ("(v%s)" % info.version).ljust(len_version),
                    info.description
                )
            )
        sys.exit(0)
    if p_args.list_available:
        print(_("Available Plugins:"))
        print_plugins = app.npe.list_available_plugins(p_args.list_available)
        if(len(print_plugins) == 0):
            print(_("Sorry, no plugins matched"))
        else:
            for name in sorted(print_plugins):
                print(print_plugins[name])
        sys.exit(0)
    if p_args.plugins_to_install:
        print(app.npe.install_plugins(p_args.plugins_to_install))
        sys.exit(0)
    if p_args.plugins_to_update:
        print(app.npe.update_plugins(p_args.plugins_to_update))
        sys.exit(0)
    if p_args.plugins_to_remove:
        print(app.npe.remove_plugins(p_args.plugins_to_remove))
        sys.exit(0)
    if p_args.plugins_to_enable:
        print(app.npe.enable_plugins(p_args.plugins_to_enable))
        sys.exit(0)
    if p_args.plugins_to_disable:
        print(app.npe.disable_plugins(p_args.plugins_to_disable))
        sys.exit(0)
    app.run()


if __name__ == '__main__':
    main()
