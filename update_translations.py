#!/usr/bin/env python2
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


def update_translation_files(
    logger,
    pygettext_path,
    base_dir,
    locale_dir,
    languages
):
    if(os.path.isdir(locale_dir)):
        # temp file working directory
        locale_temp_dir = tempfile.gettempdir()
        # walk through the directory structure and
        # make a list of all the .py files
        new_phrases_file = os.path.join(locale_temp_dir, "temp.pot")
        cmd = [
            pygettext_path,
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
            # make a copy of the .po file containing the current
            # translations
            language_file = os.path.join(locale_dir, "%s.po" % language)
            language_temp_file = os.path.join(
                locale_temp_dir, "%s.po" % language
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
                response = ""
                while response not in ['Y', 'N']:
                    response = raw_input(
                        " ".join([
                            "Are you sure you want to add it",
                            "as a new language (Y/N)? "
                        ])
                    ).strip().upper()
                if(response=='Y'):
                    languages.append(language)

    if(len(languages) > 0):
        pygettext_path = "/".join([
            "",
            "usr",
            "share",
            "doc",
            "python2.7",
            "examples",
            "Tools",
            "i18n",
            "pygettext.py"
        ])
        if(check_executable(pygettext_path)):
            if(check_executable("msgcat")):
                # Update the translations for the "naomi" folder and subfolders
                update_translation_files(
                    logger,
                    pygettext_path,
                    os.path.join(base_dir, "naomi"),
                    locale_dir,
                    languages
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
                                languages
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
                    "Please install the examples package for python 2.7:",
                    "",
                    "sudo apt install python2.7-examples"
                ])
            )
    else:
        print("No languages listed for updating. Exiting.")


if __name__ == "__main__":
    main()
