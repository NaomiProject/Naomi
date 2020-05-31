# -*- coding: utf-8 -*-
# workflow adapted from
# https://cmusphinx.github.io/wiki/tutorialadapt
import glob
import logging
import os
import pandas as pd
import re
import shutil
import sqlite3
from datetime import datetime
from naomi import paths
from naomi import plugin
from naomi import pluginstore
from naomi import profile
from naomi.run_command import run_command
from naomi.run_command import process_completedprocess


# This checks a directory to make sure the pocketsphinx model files
# we need are in there.
def check_pocketsphinx_model(directory):
    # Start by assuming the files exist. If any file is found to not
    # exist, then set this to False
    FilesExist = True
    if(not os.path.isfile(os.path.join(directory, "mdef.txt"))):
        if(os.path.isfile(os.path.join(directory, "mdef"))):
            command = [
                "pocketsphinx_mdef_convert",
                "-text",
                os.path.join(directory, "mdef"),
                os.path.join(directory, "mdef.txt")
            ]
            completedprocess = run_command(command)
            print("Command {} returned {}".format(
                " ".join(completedprocess.args),
                completedprocess.returncode
            ))
        if(not os.path.isfile(os.path.join(directory, "mdef.txt"))):
            FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "means"))):
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "mixture_weights"))):
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "sendump"))):
        FilesExist = False
    if(not os.path.isfile(os.path.join(directory, "variances"))):
        FilesExist = False
    return FilesExist


class PocketsphinxAdaptPlugin(plugin.STTTrainerPlugin):
    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger(__name__)
        self.language = profile.get_profile_var(['language'])
        self.base_working_dir = paths.sub("pocketsphinx")
        if not os.path.isdir(self.base_working_dir):
            os.mkdir(self.base_working_dir)
        self.standard_dir = os.path.join(self.base_working_dir, "standard")
        if not os.path.isdir(self.standard_dir):
            os.mkdir(self.standard_dir)
        self.standard_dir = os.path.join(self.standard_dir, self.language)
        if not os.path.isdir(self.standard_dir):
            os.mkdir(self.standard_dir)
        self.working_dir = os.path.join(self.base_working_dir, "working")
        self.model_dir = os.path.join(self.working_dir, self.language)
        self.adapt_dir = os.path.join(
            self.base_working_dir,
            "adapt",
            self.language
        )
        self.formatteddict_path = os.path.join(
            self.adapt_dir,
            "cmudict.formatted.dict"
        )
        self.audiolog_dir = paths.sub("audiolog")
        self.audiolog_db = os.path.join(self.audiolog_dir, "audiolog.db")
        super(PocketsphinxAdaptPlugin, self).__init__(*args, **kwargs)

    def HandleCommand(self, command, description):
        try:
            conn = sqlite3.connect(self.audiolog_db)
            c = conn.cursor()
            response = []
            continue_next = True
            nextcommand = ""
            if(command == ""):
                response.append(
                    "<h2>Preparing to adapt Pocketsphinx model</h2>"
                )
                description.append(
                    "Adapting standard {} pocketsphinx model".format(
                        self.language
                    )
                )
                nextcommand = "checkenviron"
            if(command == "checkenviron"):
                # Now run through the steps to adapt the standard model
                # Start by checking to see if we have a copy of the standard
                # model for this user's chosen language and download it if not.
                # Check for the files we need
                if(not check_pocketsphinx_model(self.standard_dir)):
                    # Check and see if we already have a copy of the standard
                    # language model
                    cmd = [
                        'git',
                        'clone',
                        '-b',
                        self.language,
                        'https://github.com/NaomiProject/CMUSphinx_standard_language_models.git',
                        self.standard_dir
                    ]
                    completedprocess = run_command(cmd)
                    response.append(
                        process_completedprocess(
                            completedprocess,
                            output='html'
                        )
                    )
                    if(completedprocess.returncode != 0):
                        continue_next = False
                response.append("Environment configured")
                nextcommand = "prepareworkingdir"
            if(command == "prepareworkingdir"):
                # At this point, we should have the standard model we need
                if(check_pocketsphinx_model(self.standard_dir)):
                    # FIXME It might be safest to remove the working dir at this
                    # point if it already exists
                    if not os.path.isdir(self.model_dir):
                        # Copy the sphinx model into model_dir
                        shutil.copytree(self.standard_dir, self.model_dir)
                    if(check_pocketsphinx_model(self.model_dir)):
                        query = " ".join([
                            "select",
                            " rowid,",
                            " case",
                            "  when length(trim(verified_transcription))>0",
                            "   then (length(trim(verified_transcription))-length(replace(trim(verified_transcription),' ','')))+1",
                            "  else 0",
                            " end as WordCount,",
                            " filename,",
                            " upper(trim(replace(replace(verified_transcription,'?',''),',',''))) as transcription",
                            "from audiolog",
                            "where type in('active','passive') and reviewed!=''"
                        ])
                        df = pd.read_sql_query(query, conn)
                        # Take the above and create naomi.fileids and naomi.transcription
                        # fileids:
                        description.append("on {} wav files".format(str(df.shape[0])))
                        response.append("Adapting on {} wav files".format(df.shape[0]))
                        with open(os.path.join(self.working_dir, "naomi.fileids"), "w+") as f:
                            for filename in df['filename']:
                                # No need to copy file, just leave it in audiolog
                                f.write("{}\n".format(filename.rsplit(".", 1)[0]))
                        with open(os.path.join(self.working_dir, "naomi.transcription"), "w+") as f:
                            for t in df['transcription']:
                                f.write("<s> {} </s>\n".format(t.lower()))
                        nextcommand = "featureextraction"
                    else:
                        response.append("Error: failed to populate working model")
            if(command == "featureextraction"):
                cmd = [
                    'sphinx_fe',
                    '-argfile', os.path.join(self.model_dir, 'feat.params'),
                    '-samprate', '16000',
                    '-c', os.path.join(self.working_dir, 'naomi.fileids'),
                    '-di', self.audiolog_dir,
                    '-do', self.working_dir,
                    '-ei', 'wav',
                    '-eo', 'mfc',
                    '-mswav', 'yes'
                ]
                completedprocess = run_command(cmd)
                response.append(
                    process_completedprocess(
                        completedprocess,
                        output='html'
                    )
                )
                if(completedprocess.returncode != 0):
                    continue_next = False
                nextcommand = "buildweights"
            if(command == "buildweights"):
                bw = '/usr/lib/sphinxtrain/bw'
                if os.path.isfile('/usr/local/libexec/sphinxtrain/bw'):
                    bw = '/usr/local/libexec/sphinxtrain/bw'
                cmd = [
                    bw,
                    '-hmmdir', self.model_dir,
                    '-moddeffn', os.path.join(self.model_dir, 'mdef.txt'),
                    '-ts2cbfn', '.ptm.',
                    '-feat', '1s_c_d_dd',
                    '-svspec', '0-12/13-25/26-38',
                    '-cmn', 'current',
                    '-agc', 'none',
                    '-dictfn', os.path.join(self.model_dir, 'cmudict.dict'),
                    '-ctlfn', os.path.join(self.working_dir, 'naomi.fileids'),
                    '-lsnfn', os.path.join(self.working_dir, 'naomi.transcription'),
                    '-cepdir', self.working_dir,
                    '-accumdir', self.working_dir
                ]
                completedprocess = run_command(cmd)
                response.append(
                    process_completedprocess(
                        completedprocess,
                        output='html'
                    )
                )
                if(completedprocess.returncode != 0):
                    continue_next = False
                nextcommand = "mllr"
            if(command == "mllr"):
                # MLLR is a cheap adaptation method that is suitable when the amount of data is limited. It's good for online adaptation.
                # MLLR works best for a continuous model. It's effect for semi-continuous models is limited.
                mllr = '/usr/lib/sphinxtrain/mllr_solve'
                if os.path.isfile('/usr/local/libexec/sphinxtrain/mllr_solve'):
                    mllr = '/usr/local/libexec/sphinxtrain/mllr_solve'
                cmd = [
                    mllr,
                    '-meanfn', os.path.join(self.model_dir, 'means'),
                    '-varfn', os.path.join(self.model_dir, 'variances'),
                    '-outmllrfn', os.path.join(self.model_dir, 'mllr_matrix'),
                    '-accumdir', self.working_dir
                ]
                completedprocess = run_command(cmd)
                response.append(
                    process_completedprocess(
                        completedprocess,
                        output='html'
                    )
                )
                if(completedprocess.returncode != 0):
                    continue_next = False
                nextcommand = "map"
            if(command == "map"):
                # Update the acoustic model files with MAP
                # In this case, unlike MLLR, we don't create a generic transform, but update each parameter in the model
                # We copy the acoustic model directory and overwrite the new directory with the adapted model files
                if(os.path.isdir(self.adapt_dir)):
                    # Remove the adapt dir
                    shutil.rmtree(self.adapt_dir)
                    response.append("Cleared adapt directory {}".format(self.adapt_dir))
                shutil.copytree(self.model_dir, self.adapt_dir)
                map_adapt = '/usr/lib/sphinxtrain/map_adapt'
                if os.path.isfile('/usr/local/libexec/sphinxtrain/map_adapt'):
                    map_adapt = '/usr/local/libexec/sphinxtrain/map_adapt'
                cmd = [
                    map_adapt,
                    '-moddeffn', os.path.join(self.model_dir, 'mdef.txt'),
                    '-ts2cbfn', '.ptm.',
                    '-meanfn', os.path.join(self.model_dir, 'means'),
                    '-varfn', os.path.join(self.model_dir, 'variances'),
                    '-mixwfn', os.path.join(self.model_dir, 'mixture_weights'),
                    '-tmatfn', os.path.join(self.model_dir, 'transition_matrices'),
                    '-accumdir', self.working_dir,
                    '-mapmeanfn', os.path.join(self.adapt_dir, 'means'),
                    '-mapvarfn', os.path.join(self.adapt_dir, 'variances'),
                    '-mapmixwfn', os.path.join(self.adapt_dir, 'mixture_weights'),
                    '-maptmatfn', os.path.join(self.adapt_dir, 'transition_matrices')
                ]
                completedprocess = run_command(cmd)
                response.append(
                    process_completedprocess(
                        completedprocess,
                        output='html'
                    )
                )
                if(completedprocess.returncode != 0):
                    continue_next = False
                nextcommand = "sendump"
            if(command == "sendump"):
                # Recreating the adapted sendump file
                # a sendump file saves space and is supported by pocketsphinx
                mk_s2sendump = '/usr/lib/sphinxtrain/mk_s2sendump'
                if os.path.isfile('/usr/local/libexec/sphinxtrain/mk_s2sendump'):
                    mk_s2sendump = '/usr/local/libexec/sphinxtrain/mk_s2sendump'
                cmd = [
                    mk_s2sendump,
                    '-pocketsphinx', 'yes',
                    '-moddeffn', os.path.join(self.adapt_dir, 'mdef.txt'),
                    '-mixwfn', os.path.join(self.adapt_dir, 'mixture_weights'),
                    '-sendumpfn', os.path.join(self.adapt_dir, 'sendump')
                ]
                completedprocess = run_command(cmd)
                response.append(
                    process_completedprocess(
                        completedprocess,
                        output='html'
                    )
                )
                if(completedprocess.returncode != 0):
                    continue_next = False
                nextcommand = "updateprofile"
            if(command == "updateprofile"):
                # Format the dictionary
                # Remove whitespace at the beginning of each line
                # Remove (#) after first word
                # collapse multiple whitespaces into a single space
                # Remove any whitespaces from the end
                with open(os.path.join(self.adapt_dir, "cmudict.dict"), "r") as in_file:
                    with open(self.formatteddict_path, "w+") as out_file:
                        for line in in_file:
                            # Remove whitespace at beginning and end
                            line = line.strip()
                            # remove the number in parentheses (if there is one)
                            line = re.sub('([^\\(]+)\\(\\d+\\)', '\\1', line)
                            # compress all multiple whitespaces into a single whitespace
                            line = re.sub('\s+', ' ', line)
                            # replace the first whitespace with a tab
                            line = line.replace(' ', '\t', 1)
                            print(line, file=out_file)
                # Use phonetisaurus to prepare an fst model
                cmd = [
                    "phonetisaurus-train",
                    "--lexicon", self.formatteddict_path,
                    "--seq2_del",
                    "--dir_prefix", os.path.join(self.adapt_dir, "train")
                ]
                completedprocess = run_command(cmd)
                response.append(
                    process_completedprocess(
                        completedprocess,
                        output='html'
                    )
                )
                if(completedprocess.returncode == 0):
                    # Now set the values in profile
                    profile.set_profile_var(
                        ['pocketsphinx', 'fst_model'],
                        os.path.join(self.adapt_dir, "train", "model.fst")
                    )
                    profile.set_profile_var(
                        ['pocketsphinx', 'hmm_dir'],
                        self.adapt_dir
                    )
                    profile.save_profile()
                    # Also run through the list of words that have been used
                    # that are not the wake word or a command word and make
                    # sure they are all identified so pocketsphinx can match
                    # them and not get confused on word boundaries.
                    # Pull a list of all words spoken from
                    # verified translations
                    query = " ".join([
                        "with recursive split(",
                        " word,",
                        " rest",
                        ") as (",
                        " select",
                        "  '',"
                        "  upper(replace(replace(verified_transcription,'?',''),',','')) || ' '",
                        " from audiolog",
                        " where type in ('active','passive') and reviewed!=''",
                        " union all select",
                        "  substr(rest, 0, instr(rest,' ')),",
                        "  substr(rest,instr(rest,' ')+1)",
                        " from split where rest <> ''"
                        ")",
                        "select word from split where word!='' group by word"
                    ])
                    c.execute(query)
                    words_used = [x[0].upper() for x in c.fetchall()]
                    # Pull the list of words from the local standard phrases
                    keywords = profile.get_profile_var(['keyword'])
                    if(isinstance(keywords, str)):
                        keywords = [keywords]
                    phrases = [keyword.upper() for keyword in keywords]
                    custom_standard_phrases_dir = paths.sub(os.path.join(
                        "data",
                        "standard_phrases"
                    ))
                    custom_standard_phrases_file = os.path.join(
                        custom_standard_phrases_dir,
                        "{}.txt".format(self.language)
                    )
                    if(os.path.isfile(custom_standard_phrases_file)):
                        with open(
                            custom_standard_phrases_file,
                            mode="r"
                        ) as f:
                            for line in f:
                                phrase = line.strip().upper()
                                if phrase:
                                    phrases.append(phrase)
                    # Get all the phrases that the plugins are looking for
                    ps = pluginstore.PluginStore()
                    ps.detect_plugins("speechhandler")
                    for info in ps.get_plugins_by_category("speechhandler"):
                        try:
                            plugin = info.plugin_class(
                                info,
                                profile.get_profile()
                            )
                            # get_phrases is vestigial now
                            if(hasattr(plugin, "get_phrases")):
                                for phrase in plugin.get_phrases():
                                    phrases.extend([
                                        word.upper() for word in phrase.split()
                                    ])
                            # get the phrases from the plugin intents
                            if(hasattr(plugin, "intents")):
                                intents = plugin.intents()
                                for intent in intents:
                                    for template in intents[intent]['locale'][self.language]['templates']:
                                        phrases.extend([
                                            word.upper() for word in template.split()
                                        ])
                        except Exception as e:
                            message = "Unknown"
                            if hasattr(e, "message"):
                                message = e.message
                            response.append(
                                "Plugin {} skipped! (Reason: {})".format(
                                    info.name, message
                                )
                            )
                            self._logger.warning(
                                "Plugin '{}' skipped! (Reason: {})".format(
                                    info.name, message
                                ),
                                exc_info=True
                            )

                    # Get the set of all words in words_used that do not appear
                    # in phrases
                    print("Phrases:")
                    print(phrases)
                    new_phrases = [
                        word for word in words_used if word not in phrases
                    ]
                    response.append(
                        "{} new phrases detected".format(len(new_phrases))
                    )
                    description.append(
                        "adding {} new phrases".format(len(new_phrases))
                    )
                    if(len(new_phrases) > 0):
                        table = "<table><tr><th>new phrase</th></tr>"
                        # Append the new phrases to the custom
                        # standard_phrases\{language}.txt file
                        if(not os.path.isdir(custom_standard_phrases_dir)):
                            os.makedirs(custom_standard_phrases_dir)
                        with open(custom_standard_phrases_file, mode="a+") as f:
                            for word in new_phrases:
                                table += "<tr><td>{}</td></tr>".format(word)
                                print(word, file=f)
                        table += "</table>"
                        response.append(table)
                    # Finally, force naomi to regenerate all of the
                    # pocketsphinx vocabularies by deleting all the
                    # vocabularies/{language}/sphinx/{}/revision
                    # files:
                    for revision_file in glob.glob(paths.sub(
                        'vocabularies',
                        self.language,
                        'sphinx',
                        "*",
                        "revision"
                    )):
                        os.remove(revision_file)
                    # Add the description
                    c.execute(
                        '''insert into trainings values(?,?,?)''',
                        (
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'Adapt Pocketsphinx',
                            " ".join(description)
                        )
                    )
                    conn.commit()
                else:
                    continue_next = False
        except Exception as e:
            continue_next = False
            message = "Unknown"
            if hasattr(e, "message"):
                message = e.message
            self._logger.error(
                "Error: {}".format(
                    message
                ),
                exc_info=True
            )
            response.append('<span class="failure">{}</span>'.format(
                message
            ))
        if not continue_next:
            nextcommand = ""
        return response, nextcommand, description
