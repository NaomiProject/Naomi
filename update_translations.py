#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Update .po files to receive updated translation strings
# Create one .po file for the files in the main naomi directory,
# then run through all the plugins and create .po files for each of them.
import argparse
import itertools
import logging
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime

import pdb
PROGRAM = "Naomi"
VERSION = "3.0"
LICENSE = "MIT"


def update_translation_files(
    logger,
    pygettext_path,
    base_dir,
    locale_dir,
    languages,
    plugin,
    name,
    email
):
    now = datetime.now()
    tdiff=round(100 * (now - datetime.utcnow()).seconds / 3600)
    zone = str(tdiff) if tdiff<0 else "+{}".format(tdiff)
    year = str(now.year)
    month = str(now.month).zfill(2)
    day = str(now.day).zfill(2)
    hour = str(now.hour).zfill(2)
    minute = str(now.minute).zfill(2)
    second = str(now.second).zfill(2)

    if(os.path.isdir(locale_dir)):
        # temp file working directory
        locale_temp_dir = tempfile.gettempdir()
        # walk through the directory structure and
        # make a list of all the .py files
        new_phrases_file = os.path.join(locale_temp_dir, "temp.pot")
        cmd = [
            pygettext_path,
            "-L", "Python",
            "-kgettext",
            "-o", "temp.pot",
            "-p", locale_temp_dir
        ]
        for dirName, subdirList, fileList in os.walk(base_dir):
            for file in [
                x for x in fileList if x.endswith(".py") and x != "i18n.py"
            ]:
                cmd.append(os.path.join(dirName, file))

        # create the new phrases file
        print(" ".join(cmd))
        subprocess.check_call(cmd)

        for language in languages:
            # make a copy of the .po file containing the current
            # translations
            language_file = os.path.join(locale_dir, "%s.po" % language)
            language_temp_file = os.path.join(
                locale_temp_dir, "%s.po" % language
            )
            plural_forms = '"Plural-Forms: nplurals=2; plural=(n != 1);\\n"'
            if(language == "fr-FR"):
                plural_forms = '"Plural-Forms: nplurals=2; plural=(n>1);\\n"'
            if(os.path.isfile(language_file)):
                print("cp {} {}".format(language_file, language_temp_file))
                shutil.copyfile(language_file, language_temp_file)
            else:
                # create a language file
                print("touch {}".format(language_temp_file))
                open(language_temp_file, "w").close()
            # combine the generated pot file with the temporary po file
            # and write them back to the working po file location
            with open(language_file, "w") as fp:
                try:
                    print("msgcat {} {}".format(language_temp_file, new_phrases_file))
                    header = False
                    prev_line = ""
                    skip1 = False
                    skip2 = False
                    for line in subprocess.check_output(
                        ["msgcat", language_temp_file, new_phrases_file]
                    ).decode('utf-8').split("\n"):
                        if(line == "# #-#-#-#-#  temp.pot (PACKAGE VERSION)  #-#-#-#-#"):
                            skip1 = True
                        if(skip1):
                            if(line == "#, fuzzy"):
                                skip1 = False
                            else:
                                continue
                        if(line == '"#-#-#-#-#  temp.pot (PACKAGE VERSION)  #-#-#-#-#\\n"'):
                            skip2 = True
                        if(skip2):
                            if(line == ""):
                                skip2 = False
                            else:
                                continue
                        # Eliminate duplicate lines
                        if(line == prev_line):
                            continue
                        prev_line = line
                        if(line == "# SOME DESCRIPTIVE TITLE."):
                            line = "# {} {} {}".format(PROGRAM, VERSION, plugin)
                        if(line == "# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER"):
                            line = "# Copyright (C) {} {}".format(year, "Naomi Project")
                        if(line == "# This file is distributed under the same license as the PACKAGE package."):
                            line = "# This file is distributed under the same {} license as the {} package.".format(LICENSE, PROGRAM)
                        if(line == "# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR."):
                            line = "# {} <{}>, {}".format(name, email, year)
                        if(line == '"Project-Id-Version: PACKAGE VERSION\\n"'):
                            line = '"Project-Id-Version: {}\\n"'.format('Naomi 3.0')
                        if(line == '"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"'):
                            line = '"Last-Translator: {} <{}>\\n"'.format(name, email)
                        if(line == '"Language: \\n"'):
                            line = '"Language: {}\\n"'.format(language)
                        if(line == '"Report-Msgid-Bugs-To: \\n"'):
                            line = '"Report-Msgid-Bugs-To: {}\\n"'.format(email)
                        if(line[:19] == '"PO-Revision-Date: '):
                            line = '"PO-Revision-Date: {}-{}-{} {}:{}{}\\n"'.format(year, month, day, hour, minute, zone)
                        if(line == '"Language-Team: LANGUAGE <LL@li.org>\\n"'):
                            line = '"Language-Team: {} <{}@projectnaomi.com>\\n"'.format(language, language)
                        if(line == '"Content-Type: text/plain; charset=CHARSET\\n"'):
                            line = '"Content-Type: text/plain; charset=UTF-8\\n"'
                        if(line == '"Content-Transfer-Encoding: 8bit\n"'):
                            line = "\n".join([
                                '"Content-Transfer-Encoding: 8bit\\n"',
                                plural_forms
                            ])
                        if(line[:15] == '"Plural-Forms: '):
                            continue
                        if(line == '"# #-#-#-#-#  temp.pot (PACKAGE VERSION)  #-#-#-#-#\\n"'):
                            skip2 = True
                        fp.write("{}\n".format(line))
                except subprocess.CalledProcessError as e:
                    logger.error(e.output)
                fp.close()
            print("Updated %s" % language_file)
            # clean up the copied .po file
            print("rm {}".format(language_temp_file))
            os.remove(language_temp_file)
        if(os.path.isfile(new_phrases_file)):
            print("rm {}".format(new_phrases_file))
            os.remove(new_phrases_file)
    else:
        logger.warn(
            "Skipping %s, %s directory does not exist" % (
                base_dir, locale_dir
            )
        )

def check_executable(executable):
    try:
        devnull = open(os.devnull)
        subprocess.Popen(
            [
                executable,
                '--help'
            ],
            stdout=devnull,
            stdin=devnull,
            stderr=devnull
        ).communicate()
        return True
    except OSError:
        return False

def main():
    logger = logging.getLogger("update_translations")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    locale_dir = os.path.join(
        base_dir,
        "naomi",
        "data",
        "locale"
    )
    # Get a list of existing translations from
    # the language files located in locale_dir
    existing_languages = []
    for file in os.listdir(locale_dir):
        match = re.search(r'\.po$', file)
        if(match):
            existing_languages.append(file[:match.start()])

    # Get the current language(s) from the parameters
    parser = argparse.ArgumentParser(
        description=" ".join([
            'Update .pot files to receive updated translation strings.',
            'Translation files exist for the following languages:',
            '%s' % existing_languages
        ])
    )
    parser.add_argument(
        "-l", "--language",
        action="append",
        nargs='+')
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Show debugging info"
    )
    parser.add_argument(
        "-a", "--author",
        action="store",
        help="Author's name (defaults to 'Naomi Project')",
        default="Naomi Project"
    )
    parser.add_argument(
        "-e", "--email",
        action="store",
        help="Author's email (defaults to 'naomi@projectnaomi.com'",
        default="naomi@projectnaomi.com"
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.ERROR
    )
    if(args.language is None):
        languages = existing_languages
    else:
        # each -l argument adds a list which can contain multiple items.
        # for example, -l en-US fr-FR results in [['en-US', 'fr-FR']]
        # while -l en-US -l fr-FR results in [['en-US'], ['fr-FR']]
        # Use itertools to flatten the list of languages.
        languages = []
        for language in itertools.chain.from_iterable(args.language):
            if(language in existing_languages):
                languages.append(language)
            else:
                print(
                    " ".join([
                        "%s" % language,
                        "is not in the current list of translations: ",
                        "%s." % existing_languages
                    ])
                )
                response = "X"
                while response not in ['Y', 'N']:
                    response = input(
                        " ".join([
                            "Are you sure you want to add it",
                            "as a new language (Y/n)? "
                        ])
                    ).strip().upper()
                    if(len(response) == 0):
                        response = 'Y'
                print()
                if(response != 'N'):
                    languages.append(language)

    if(len(languages) > 0):
        pygettext_path = "xgettext"
        if(check_executable("xgettext")):
            if(check_executable("msgcat")):
                # Update the translations for the "naomi" folder and subfolders
                update_translation_files(
                    logger,
                    pygettext_path,
                    os.path.join(base_dir, "naomi"),
                    locale_dir,
                    languages,
                    "Core",
                    args.author,
                    args.email
                )

                # now walk through all the directories in the plugins/*/
                # directories
                for pluginType in next(
                    os.walk(
                        os.path.join(
                            base_dir, "plugins"
                        )
                    )
                )[1]:
                    for plugin in next(
                        os.walk(
                            os.path.join(
                                base_dir, "plugins", pluginType
                            )
                        )
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
                            print("Processing plugin %s type %s" % (
                                plugin, pluginType
                            ))
                            update_translation_files(
                                logger,
                                pygettext_path,
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
                                languages,
                                plugin,
                                args.author,
                                args.email
                            )
                print("Finished.")
                print(
                    " ".join([
                        "Unfortunately, this program has probably introduced",
                        "duplicate lines into the .po file headers.",
                        "Please clean them up while updating the translations.",
                        "Thank you."
                    ])
                )
            else:
                logger.error(
                    '\n'.join([
                        "The msgcat command does not exist.",
                        "Please install the gettext package:",
                        "",
                        "sudo apt install gettext"
                    ])
                )
        else:
            logger.error(
                '\n'.join([
                    "File %s does not exist." % pygettext_path,
                    "Please install the gettext package:",
                    "",
                    "sudo apt install gettext"
                ])
            )
    else:
        print("No languages listed for updating. Exiting.")


if __name__ == "__main__":
    main()
