#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Update .po files to receive updated translation strings
# Create one .po file for the files in the main naomi directory,
# then run through all the plugins and create .po files for each of them.
import argparse
import logging
import os
import re
import shutil
import subprocess
import tempfile


def update_translation_files(base_dir, locale_dir, languages):
    logger = logging.getLogger("update_translations")
    if(os.path.isdir(locale_dir)):
        # temp file working directory
        locale_temp_dir = tempfile.gettempdir()
        # walk through the directory structure and
        # make a list of all the .py files
        new_phrases_file = os.path.join(locale_temp_dir, "temp.pot")
        cmd = [
            "/usr/share/doc/python2.7/examples/Tools/i18n/pygettext.py",
            "-k", "gettext",
            "-d", "temp",
            "-p", locale_temp_dir
        ]
        for dirName, subdirList, fileList in os.walk(base_dir):
            for file in [
                x for x in fileList if x.endswith(".py") and x != "i18n.py"
            ]:
                cmd.append(os.path.join(dirName, file))

        # create the new phrases file
        subprocess.check_call(cmd)

        for language in languages:
            # make a copy of the .po file containing the current translations
            language_file = os.path.join(locale_dir, "%s.po" % language)
            language_temp_file = os.path.join(
                locale_temp_dir, "%s_temp.po" % language
            )
            if(os.path.isfile(language_file)):
                shutil.copyfile(language_file, language_temp_file)
            else:
                # create a language file
                open(language_temp_file, "w").close()
            # combine the generated pot file with the temporary po file
            # and write them back to the working po file location
            with open(language_file, "w") as fp:
                try:
                    for line in (subprocess.check_output(
                        ["msgcat", language_temp_file, new_phrases_file]
                    )):
                        fp.write(line)
                except subprocess.CalledProcessError as e:
                    logger.error(e.output)
                fp.close()
            print("Updated %s" % language_file)
            # clean up the copied .po file
            os.remove(language_temp_file)
        os.remove(new_phrases_file)
    else:
        logger.warn(
            "Skipping %s, %s directory does not exist" % (base_dir, locale_dir)
        )


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    locale_dir = os.path.join(
        base_dir,
        "naomi",
        "data",
        "locale"
    )

    # Get the current language(s) from the parameters
    parser = argparse.ArgumentParser(
        description='Update .pot files to receive updated translation strings'
    )
    parser.add_argument(
        "--language", "-l",
        action="append",
        nargs='+')
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Show debugging info"
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.ERROR
    )
    if(args.language is None):
        args.language = []
        # Get a list of languages from the language files located in locale_dir
        for file in os.listdir(locale_dir):
            match = re.search(r'\.po$', file)
            if(match):
                args.language.append(file[:match.start()])

    # Update the translations for the "naomi" folder and subfolders
    update_translation_files(
        os.path.join(base_dir, "naomi"),
        locale_dir,
        args.language
    )

    # now walk through all the directories in the plugins/*/ directories
    for pluginType in next(os.walk(os.path.join(base_dir, "plugins")))[1]:
        for plugin in next(
            os.walk(os.path.join(base_dir, "plugins", pluginType))
        )[1]:
            if(
                os.path.isfile(
                    os.path.join(
                        base_dir,
                        "plugins",
                        pluginType,
                        plugin,
                        "plugin.info"
                    )
                )
            ):
                print("Processing plugin %s type %s" % (plugin, pluginType))
                update_translation_files(
                    os.path.join(
                        base_dir,
                        "plugins",
                        pluginType,
                        plugin
                    ),
                    os.path.join(
                        base_dir,
                        "plugins",
                        pluginType,
                        plugin,
                        "locale"
                    ),
                    args.language
                )


if __name__ == "__main__":
    main()
