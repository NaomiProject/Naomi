# -*- coding: utf-8 -*-
import sys
import logging
import argparse
from . import application
from . import profile


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
        '--repopulate',
        action='store_true',
        help='Rebuild configuration profile'
    )
    parser.add_argument(
        '--passive-listen',
        action='store_true',
        help='Check for keyword and command in same input'
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
    list_info = parser.add_mutually_exclusive_group(required=False)
    list_info.add_argument(
        '--list-plugins',
        action='store_true',
        help='List plugins and exit'
    )
    list_info.add_argument(
        '--list-audio-devices',
        action='store_true',
        help='List audio devices and exit'
    )
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

    print("************************************************************")
    print("*                    Naomi Assistant                       *")
    print("* Made by the Naomi Community, based on the Jasper Project *")
    print("* Source code available from                               *")
    print("*    https://github.com/NaomiProject/Naomi                 *")
    print("************************************************************")

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

    # AaronC 2019-05-29
    # This keeps an argument in a static location
    # so we don't have to keep passing it from library
    # to library. We need to know if the user wants to
    # re-run populate.py when we examine the settings
    # variable while instantiating plugin objects
    # in plugin.GenericPlugin.__init__()
    profile.set_arg("repopulate",p_args.repopulate)

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
    if p_args.list_plugins:
        app.list_plugins()
        sys.exit(1)
    elif p_args.list_audio_devices:
        app.list_audio_devices()
        sys.exit(0)
    app.run()


if __name__ == '__main__':
    main()
