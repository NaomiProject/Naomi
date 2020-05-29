# -*- coding: utf-8 -*-
import sys
import logging
import argparse
from . import application
from . import app_utils
from . import profile
from . import coloredformatting as cf
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
        help='Use text input instead of a real microphone'
    )
    mic_mode.add_argument(
        '--batch',
        dest='batch_file',
        metavar="FILE",
        type=argparse.FileType('r'),
        help=' '.join([
            'Batch mode using a text file with text',
            'commands audio filenames at each line.'
        ])
    )
    mic_mode.add_argument(
        '--print-transcript',
        action='store_true',
        help='Prints a transcription of things Naomi says and thinks it hears'
    )
    p_args = parser.parse_args(args)

    print(logo)
    print("      ___           ___           ___           ___                  ")
    print("     /\__\         /\  \         /\  \         /\__\          ___    ")
    print("    /::|  |       /::\  \       /::\  \       /::|  |        /\  \   ")
    print("   /:|:|  |      /:/\:\  \     /:/\:\  \     /:|:|  |        \:\  \  ")
    print("  /:/|:|  |__   /::\~\:\  \   /:/  \:\  \   /:/|:|__|__      /::\__\ ")
    print(" /:/ |:| /\__\ /:/\:\ \:\__\ /:/__/ \:\__\ /:/ |::::\__\  __/:/\/__/ ")
    print(" \/__|:|/:/  / \/__\:\/:/  / \:\  \ /:/  / \/__/~~/:/  / /\/:/  /    ")
    print("     |:/:/  /       \::/  /   \:\  /:/  /        /:/  /  \::/__/     ")
    print("     |::/  /        /:/  /     \:\/:/  /        /:/  /    \:\__\     ")
    print("     /:/  /        /:/  /       \::/  /        /:/  /      \/__/     ")
    print("     \/__/         \/__/         \/__/         \/__/                 ")
    print(sto)

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if p_args.debug else logging.ERROR
    )

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
    if p_args.list_active_plugins:
        app.list_active_plugins()
        sys.exit(0)
    elif p_args.list_audio_devices:
        app.list_audio_devices()
        sys.exit(0)
    if p_args.list_available:
        app.list_available_plugins(p_args.list_available)
        sys.exit(0)
    if p_args.plugins_to_install:
        app.install_plugins(p_args.plugins_to_install)
        sys.exit(0)
    if p_args.plugins_to_update:
        app.update_plugins(p_args.plugins_to_update)
        sys.exit(0)
    if p_args.plugins_to_remove:
        app.remove_plugins(p_args.plugins_to_remove)
        sys.exit(0)
    if p_args.plugins_to_enable:
        app.enable_plugins(p_args.plugins_to_enable)
        sys.exit(0)
    if p_args.plugins_to_disable:
        app.disable_plugins(p_args.plugins_to_disable)
        sys.exit(0)
    app.run()


if __name__ == '__main__':
    main()
