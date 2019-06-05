#!/usr/bin/env python3

# This version of NaomiSTTTrainer allows the user to step through one sample
# at a time, instead of returning a table full of samples.
# My assumption is that for the most part, you only need to validate the record
# once, after that it should automatically skip all the records that have
# already been verified.

# -*- coding: utf-8 -*-
import argparse
from datetime import datetime
import wsgiref.simple_server
from socketserver import ThreadingMixIn
import re
import shutil
import socket
import sqlite3
import subprocess
import tarfile
from urllib.parse import unquote
from urllib.request import urlretrieve
import os
from naomi import paths
from naomi import profile
from naomi import pluginstore
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
import pdb
import json
from jiwer import wer


# Set Debug to True to see debugging information
Debug = False


def Get_row(c, rowID):
    c.execute(
        " ".join([
            "select",
            " datetime,",
            " filename,",
            " type,",
            " transcription,",
            " verified_transcription,",
            " speaker,",
            " reviewed,",
            " wer",
            "from audiolog where rowid=:RowID"
        ]),
        ({"RowID": rowID})
    )
    row = c.fetchone()
    if(row is None):
        Record = None
    else:
        if(Debug):
            print("Recorded Type=%s" % type(row[0]))
            print("Filename Type=%s" % type(row[1]))
            print("Type Type=%s" % type(row[2]))
            print("Transcription Type=%s" % type(row[3]))
            print("Verified_transcription Type=%s" % type(row[4]))
            print("Speaker Type=%s" % type(row[5]))
            print("Reviewed Type=%s" % type(row[6]))
            print("WER Type=%s" % type(row[7]))
        Record = {
            "Recorded": str(row[0]),
            "Filename": str(row[1]),
            "Type": str(row[2]),
            "Transcription": str(row[3]),
            "Verified_transcription": str(row[4]),
            "Speaker": str(row[5]),
            "Reviewed": str(row[6]),
            "WER": str(row[7])
        }
    return Record


def verify_row_id(c, rowID):
    Ret = True
    c.execute("select RowID from audiolog where RowID=:RowID", {"RowID": rowID})
    row = c.fetchone()
    if(row is None):
        Ret = False
    return Ret


def fetch_first_rowID(c):
    c.execute("select RowID from audiolog order by RowID asc limit 1")
    row = c.fetchone()
    if(row is None):
        rowID = None
    else:
        rowID = str(row[0])
    return rowID


def fetch_first_unreviewed_rowID(c):
    return fetch_next_unreviewed_rowID(c, "0")


def fetch_prev_rowID(c, rowID):
    # get the previous rowid
    c.execute(
        " ".join([
            "select",
            " RowID",
            "from audiolog",
            "where RowID<:RowID",
            "order by RowID desc",
            "limit 1"
        ]),
        {"RowID": rowID}
    )
    row = c.fetchone()
    if(row is None):
        prev_rowID = None
    else:
        prev_rowID = str(row[0])
    return prev_rowID


def fetch_current_rowID(c, rowID):
    if(rowID):
        c.execute(
            "select RowID from audiolog where RowID=:RowID",
            {"RowID": rowID}
        )
        row = c.fetchone()
        if(row is None):
            raise ValueError("RowID %s not found" % rowID)
        else:
            rowID = str(row[0])
    else:
        rowID = fetch_first_unreviewed_rowID(c)
    if(not rowID):
        # if there are no unreviewed row ID's, set to the last rowid
        rowID = fetch_last_rowID(c)
    return rowID


def fetch_next_rowID(c, rowID):
    # get the previous rowid
    print("rowID={}".format(rowID))
    c.execute(
        " ".join([
            "select",
            " RowID",
            "from audiolog",
            "where RowID>:RowID",
            "order by RowID asc",
            "limit 1"
        ]),
        {
            "RowID": rowID
        }
    )
    row = c.fetchone()
    if(row is None):
        next_rowID = None
    else:
        next_rowID = str(row[0])
    return next_rowID


def fetch_next_unreviewed_rowID(c, rowID):
    c.execute(
        " ".join([
            "select",
            " RowID",
            "from audiolog",
            "where RowID>:RowID and reviewed=''",
            "order by RowID asc",
            "limit 1"
        ]),
        {"RowID": rowID}
    )
    row = c.fetchone()
    if(row is None):
        next_rowID = None
    else:
        next_rowID = str(row[0])
    return next_rowID


def fetch_last_rowID(c):
    c.execute("select RowID from audiolog order by RowID desc limit 1")
    row = c.fetchone()
    if(row is None):
        rowID = None
    else:
        rowID = str(row[0])
    return rowID


# Replaces any punctuation characters with spaces and converts to upper case
def clean_transcription(transcription):
    print("transcription type={}".format(type(transcription)))
    return transcription.translate(
        dict((ord(char), None) for char in """][}{!@#$%^&*)(,."'></?\\|=+-_""")
    ).upper()


# This checks a directory to make sure the pocketsphinx model files
# we need are in there.
def check_pocketsphinx_model(directory):
    # Start by assuming the files exist. If any file is found to not
    # exist, then set this to False
    FilesExist = True
    if(not os.path.isfile(os.path.join(directory,"mdef.txt"))):
        if(os.path.isfile(os.path.join(directory,"mdef"))):
            command = [
                "pocketsphinx_mdef_convert",
                "-text",
                os.path.join(directory,"mdef"),
                os.path.join(directory,"mdef.txt")
            ]
            returnCode = subprocess.run(command)
            print("Command {} returned {}".format(" ".join(returnCode.args),returnCode.returncode))
        if(not os.path.isfile(os.path.join(directory,"mdef.txt"))):
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
        

def process_returncode(returnCode):
    result = "failure"
    command = " ".join(returnCode.args)
    print('{}...{}'.format(command, returnCode.returncode))
    instructions = "<br />Check log for details"
    if(returnCode.returncode == 0):
        result = "success"
        instructions = ""
    return '{}...<span class="{}">{}</span>{}'.format(
        command,
        result,
        result.upper(),
        instructions
    )


def application(environ, start_response):
    language = profile.get_profile_var(["language"],"en-US")
    keyword = profile.get_profile_var(["keyword"], "Naomi")
    print("PATH_INFO=%s" % environ["PATH_INFO"])
    if(environ["PATH_INFO"] == "/favicon.ico"):
        start_response(
            '404 Not Found',
            [('content-type', 'text/plain;charset=utf-8')]
        )
        ret = ["404 Not Found".encode("UTF-8")]
        return ret
    else:
        audiolog_dir = paths.sub("audiolog")
        audiolog_db = os.path.join(audiolog_dir, "audiolog.db")
        wavfile = ""
        rowID = ""
        first_rowID = ""
        prev_rowID = ""
        next_rowID = ""
        result = ""
        verified_transcription = ""
        post_data = ""
        engine = ""
        reQS = re.compile("([^=]+)=([^&]*)&?")

        # gather parameters from GET
        if(environ["QUERY_STRING"]):
            for namevalue in reQS.findall(environ["QUERY_STRING"]):
                if(namevalue[0].lower() == "wavfile"):
                    wavfile = os.path.join(audiolog_dir, namevalue[1])
                if(namevalue[0].lower() == "rowid"):
                    rowID = namevalue[1]

        # gather parameters from POST
        content_length = 0
        if(environ['CONTENT_LENGTH']):
            content_length = int(environ['CONTENT_LENGTH'])
            post_data = environ['wsgi.input'].read(
                content_length
            ).decode("UTF-8")
            # Parse it out
            for namevalue in reQS.findall(post_data):
                if(namevalue[0].lower() == "rowid"):
                    rowID = namevalue[1].lower()
                if(namevalue[0].lower() == "result"):
                    result = namevalue[1].lower()
                if(namevalue[0].lower() == "verified_transcription"):
                    verified_transcription = unquote(
                        namevalue[1].replace('+', ' ')
                    )
                if(namevalue[0].lower() == "engine"):
                    engine = namevalue[1].lower()
                if(namevalue[0].lower() == "command"):
                    command = namevalue[1].lower()

        # Handle the request
        # serve a .wav file
        ErrorMessage = None
        if(len(wavfile) and os.path.isfile(wavfile)):
            start_response('200 OK', [('content-type', 'audio/wav')])
            with open(wavfile, "rb") as w:
                ret = [w.read()]
            return ret
        # open a connection to the database
        conn = sqlite3.connect(audiolog_db)
        c = conn.cursor()
        # Start the html response
        ret = []
        # serve a train response. We will put this in a div on the Train
        # tab, so we don't have to regenerate everything.
        if( len(engine) ):
            start_response(
                '200 OK',
                [('content-type', 'text/json;charset=utf-8')]
            )
            continue_next = True
            nextcommand = ""
            response = []
            description = [] # Description to tell the database what we have done
            if(engine=="pocketsphinx_adapt"):
                description.append("Adapting standard {} pocketsphinx model".format(language))
                base_working_dir = paths.sub("pocketsphinx")
                if not os.path.isdir(base_working_dir):
                    os.mkdir(base_working_dir)
                standard_dir = os.path.join(base_working_dir,"standard")
                if not os.path.isdir(standard_dir):
                    os.mkdir(standard_dir)
                standard_dir = os.path.join(standard_dir,language)
                if not os.path.isdir(standard_dir):
                    os.mkdir(standard_dir)
                working_dir = os.path.join(base_working_dir,"working")
                model_dir = os.path.join(working_dir,language)
                adapt_dir=os.path.join(base_working_dir,"adapt",language)
                formatteddict_path = os.path.join(adapt_dir,"cmudict.formatted.dict")
                if(command=="checkenviron"):
                    # workflow adapted from https://cmusphinx.github.io/wiki/tutorialadapt/
                    response.append("<h2>Preparing to adapt Pocketsphinx model</h2>")
                    # Now run through the steps to adapt the standard model
                    # Start by checking to see if we have a copy of the standard
                    # model for this user's chosen language and download it if not.
                    # Check for the files we need
                    if(not check_pocketsphinx_model(standard_dir)):
                        # Check and see if we already have a copy of the standard language model
                        cmd = [
                            'git',
                            'clone',
                            '-b',
                            language,
                            'git@github.com:aaronchantrill/CMUSphinx_standard_language_models.git',
                            standard_dir
                        ]
                        returnCode = subprocess.run(cmd)
                        response.append(process_returncode(returnCode))
                        if(returnCode.returncode != 0):
                            continue_next = False
                    response.append("Environment configured")
                    nextcommand = "prepareworkingdir"
                if(command == "prepareworkingdir"):
                    # At this point, we should have the standard model we need
                    if(check_pocketsphinx_model(standard_dir)):
                        # FIXME It might be safest to remove the working dir at this
                        # point if it already exists
                        if not os.path.isdir(model_dir):
                            # Copy the sphinx model into model_dir
                            shutil.copytree(standard_dir,model_dir)
                        if(check_pocketsphinx_model(model_dir)):
                            query = " ".join([
                                "select",
                                " rowid,",
                                " case",
                                "  when length(trim(verified_transcription))>0 then (length(trim(verified_transcription))-length(replace(trim(verified_transcription),' ','')))+1",
                                "  else 0",
                                " end as WordCount,",
                                " filename,",
                                " upper(trim(replace(replace(verified_transcription,'?',''),',',''))) as transcription",
                                "from audiolog",
                                "where type in('active','passive') and reviewed!=''"
                            ])
                            df = pd.read_sql_query(query,conn)
                            # Take the above and create naomi.fileids and naomi.transcription
                            # fileids:
                            description.append("on {} wav files".format(str(df.shape[0])))
                            response.append("Adapting on {} wav files".format(df.shape[0]))
                            with open(os.path.join(working_dir,"naomi.fileids"),"w+") as f:
                                for filename in df['filename']:
                                    # No need to copy file, just leave it in audiolog
                                    f.write("{}\n".format(filename.rsplit(".",1)[0]))
                            with open(os.path.join(working_dir,"naomi.transcription"),"w+") as f:
                                [f.write("<s> {} </s>\n".format(t.lower())) for t in df['transcription']]
                            nextcommand = "featureextraction"
                        else:
                            response.append("Error: failed to populate working model")
                if(command == "featureextraction"):
                    cmd=[
                        'sphinx_fe',
                        '-argfile',os.path.join(model_dir,'feat.params'),
                        '-samprate','16000',
                        '-c',os.path.join(working_dir,'naomi.fileids'),
                        '-di',audiolog_dir,
                        '-do',working_dir,
                        '-ei','wav',
                        '-eo','mfc',
                        '-mswav','yes'
                    ]
                    returnCode = subprocess.run(cmd)
                    response.append(process_returncode(returnCode))
                    if(returnCode.returncode != 0):
                        continue_next = False
                    nextcommand = "buildweights"
                if(command == "buildweights"):
                    cmd=[
                        os.path.join('/usr','local','libexec','sphinxtrain','bw'),
                        '-hmmdir',model_dir,
                        '-moddeffn',os.path.join(model_dir,'mdef.txt'),
                        '-ts2cbfn','.ptm.',
                        '-feat','1s_c_d_dd',
                        '-svspec','0-12/13-25/26-38',
                        '-cmn','current',
                        '-agc','none',
                        '-dictfn',os.path.join(model_dir,'cmudict.dict'),
                        '-ctlfn',os.path.join(working_dir,'naomi.fileids'),
                        '-lsnfn',os.path.join(working_dir,'naomi.transcription'),
                        '-cepdir',working_dir,
                        '-accumdir',working_dir
                    ]
                    returnCode = subprocess.run(cmd)
                    response.append(process_returncode(returnCode))
                    if(returnCode.returncode != 0):
                        continue_next = False
                    nextcommand = "mllr"
                if(command == "mllr"):
                    # MLLR is a cheap adaptation method that is suitable when the amount of data is limited. It's good for online adaptation.
                    # MLLR works best for a continuous model. It's effect for semi-continuous models is limited.
                    cmd=[
                        os.path.join("/usr","local","libexec","sphinxtrain","mllr_solve"),
                        '-meanfn',os.path.join(model_dir,'means'),
                        '-varfn',os.path.join(model_dir,'variances'),
                        '-outmllrfn','mllr_matrix',
                        '-accumdir',working_dir
                    ]
                    returnCode = subprocess.run(cmd)
                    response.append(process_returncode(returnCode))
                    if(returnCode.returncode != 0):
                        continue_next = False
                    nextcommand = "map"
                if(command == "map"):
                    # Update the acoustic model files with MAP
                    # In this case, unlike MLLR, we don't create a generic transform, but update each parameter in the model
                    # We copy the acoustic model directory and overwrite the new directory with the adapted model files
                    if(os.path.isdir(adapt_dir)):
                        # Remove the adapt dir
                        shutil.rmtree(adapt_dir)
                        response.append("Cleared adapt directory {}".format(adapt_dir))
                    shutil.copytree(model_dir,adapt_dir)
                    cmd=[
                        os.path.join('/usr','local','libexec','sphinxtrain','map_adapt'),
                        '-moddeffn',os.path.join(model_dir,'mdef.txt'),
                        '-ts2cbfn','.ptm.',
                        '-meanfn',os.path.join(model_dir,'means'),
                        '-varfn',os.path.join(model_dir,'variances'),
                        '-mixwfn',os.path.join(model_dir,'mixture_weights'),
                        '-tmatfn',os.path.join(model_dir,'transition_matrices'),
                        '-accumdir',working_dir,
                        '-mapmeanfn',os.path.join(adapt_dir,'means'),
                        '-mapvarfn',os.path.join(adapt_dir,'variances'),
                        '-mapmixwfn',os.path.join(adapt_dir,'mixture_weights'),
                        '-maptmatfn',os.path.join(adapt_dir,'transition_matrices')
                    ]
                    returnCode = subprocess.run(cmd)
                    response.append(process_returncode(returnCode))
                    if(returnCode.returncode != 0):
                        continue_next = False
                    nextcommand = "sendump"
                if(command == "sendump"):
                    # Recreating the adapted sendump file
                    # a sendump file saves space and is supported by pocketsphinx
                    cmd=[
                        os.path.join('/usr','local','libexec','sphinxtrain','mk_s2sendump'),
                        '-pocketsphinx','yes',
                        '-moddeffn',os.path.join(adapt_dir,'mdef.txt'),
                        '-mixwfn',os.path.join(adapt_dir,'mixture_weights'),
                        '-sendumpfn',os.path.join(adapt_dir,'sendump')
                    ]
                    returnCode = subprocess.run(cmd)
                    response.append(process_returncode(returnCode))
                    if(returnCode.returncode != 0):
                        continue_next = False
                    nextcommand = "updateprofile"
                if(command == "updateprofile"):
                    # Format the dictionary
                    # Remove whitespace at the beginning of each line
                    # Remove (#) after first word
                    # collapse multiple whitespaces into a single space
                    # Remove any whitespaces from the end
                    with open(os.path.join(adapt_dir,"cmudict.dict"),"r") as in_file:
                        with open(formatteddict_path,"w+") as out_file:
                            for line in in_file:
                                # Remove whitespace at beginning and end
                                line = line.strip()
                                line = re.sub('\s+', ' ', line)
                                line = re.sub('([^\(]+)\(\d+\)', '\1', line)
                                print(line, file=out_file)
                    # Use phonetisaurus to prepare an fst model
                    cmd = [
                        "phonetisaurus-train",
                        "--lexicon",formatteddict_path,
                        "--seq2_del",
                        "--dir_prefix",os.path.join(adapt_dir,"train")
                    ]
                    # os.chdir(adapt_dir)
                    returnCode = subprocess.run(cmd)
                    response.append(process_returncode(returnCode))
                    if(returnCode.returncode == 0):
                        # Now set the values in profile
                        profile.set_profile_var(['pocketsphinx','fst_model'],os.path.join(adapt_dir,"train","model.fst"))
                        profile.set_profile_var(['pocketsphinx','hmm_dir'],adapt_dir)
                        profile.save_profile()
                        # Also run through the list of words that have been used that
                        # are not the wake word or a command word and make sure they
                        # are all identified so pocketsphinx can match them and not
                        # get confused on word boundaries.
                        # Pull a list of all words spoken from verified translations
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
                        # Pull the list of words from standard phrases
                        # This right now is a duplicate of the routine in brain,
                        # meaning that they have to be kept in sync. Better to have
                        # both reference the same external routine, probably in
                        # profile.
                        phrases = [keyword.upper()]
                        with open(paths.data('standard_phrases', "%s.txt" % language),mode="r") as f:
                            for line in f:
                                phrase = line.strip().upper()
                                if phrase:
                                    phrases.append(phrase)
                        # Get all the phrases that the plugins are looking for
                        # There are two locations where plugins can be stored,
                        # either in the plugins directory, or in the ~/.naomi/plugins/
                        # directory.
                        # Right now, we always put plugins directly into the plugins
                        # directory, but when we get to the point where Naomi can be
                        # installed as a package, we will want to put user plugins
                        # into the user config directory when using the plugin manager
                        ps = pluginstore.PluginStore([paths.config("plugins"),"plugins"])
                        ps.detect_plugins()
                        for info in ps.get_plugins_by_category("speechhandler"):
                            try:
                                plugin = info.plugin_class(info, profile.get_profile())
                                if(hasattr(plugin,"get_phrases")):
                                    phrases.extend([phrase.upper() for phrase in plugin.get_phrases()])
                            except Exception as e:
                                response.append("Plugin {} skipped! (Reason: {})".format(info.name,e.message if hasattr(e,"message") else "Unknown"))
                        # Get the set of all words in words_used that do not appear
                        # in phrases
                        print("{} {}".format(type(words_used),str(words_used)))
                        print("{} {}".format(type(phrases),str(phrases)))
                        new_phrases = [word for word in words_used if word not in phrases]
                        response.append("{} new phrases detected".format(len(new_phrases)))
                        description.append("adding {} new phrases".format(len(new_phrases)))
                        if(len(new_phrases)>0):
                            table = "<table><tr><th>new phrase</th></tr>"
                            # append the new phrases to 
                            for word in new_phrases:
                                table += "<tr><td>{}</td></tr>".format(word)
                            table += "</table>"
                            response.append(table)
                        table="<table><tr><th>old phrase</th></tr>"
                        for word in phrases:
                            table+="<tr><td>{}</td></tr>".format(word)
                        table += "</table>"
                        response.append(table)
                    else:
                        continue_next = False
            elif(engine=="pocketsphinx_train"):
                # Default to PocketSphinx_train and train new acoustical model
                response.append("<h2>Preparing PocketSphinx training set</h2>")
                # Everything in the training sets gets split up by speaker
                # So get a list of speakers first, then 
                # split the database into train and test data per speaker
                query = " ".join([
                    "select distinct",
                    " speaker",
                    "from audiolog",
                    "where type in ('active','passive') and reviewed != ''"
                ])
                c.execute(query)
                speakers = c.fetchall()
                for speaker in speakers:
                    response.append("Working on speaker: '{}'".format(speaker[0]))
                    # We want to make sure that both sets contain phrases of about
                    # the same complexity. Right now we aren't doing incremental
                    # training, so we don't have to worry about making sure that
                    # data stays in the training set once it is assigned.
                    # Get my distribution of sentence lengths
                    query = " ".join([
                        "select",
                        " count(*) ncount,",
                        " case",
                        "  when length(trim(verified_transcription))>0 then (length(trim(verified_transcription))-length(replace(trim(verified_transcription),' ','')))+1",
                        "  else 0",
                        " end as WordCount",
                        "from audiolog",
                        "where type in('active','passive') and reviewed!='' and speaker='{}'",
                        "group by 2;"
                    ]).format(speaker[0])
                    c.execute(query)
                    rows = c.fetchall()
                    response.append(str(rows))
                    response.append("<table><tr><th>Length</th><th>Count</th></tr>")
                    for row in rows:
                        response.append("<tr><td>{}</td><td>{}</td></tr>".format(str(row[1]),str(row[0])))
                    response.append("</table>")
                    # Get the actual data so we can feed it to StratifiedShuffleSplit
                    query = " ".join([
                        "select",
                        " rowid,",
                        " case",
                        "  when length(trim(verified_transcription))>0 then (length(trim(verified_transcription))-length(replace(trim(verified_transcription),' ','')))+1",
                        "  else 0",
                        " end as WordCount,",
                        " filename,",
                        " upper(trim(replace(replace(verified_transcription,'?',''),',',''))) as transcription",
                        "from audiolog",
                        "where type in('active','passive') and reviewed!='' and speaker='{}'"
                    ]).format(speaker[0])
                    # read the query result directly into pandas
                    df = pd.read_sql_query(query,conn)
                    # Split into train and test
                    split = StratifiedShuffleSplit(n_splits=1,test_size=0.1,random_state=42)
                    for train_index,test_index in split.split(df,df['WordCount']):
                        strat_train_set = df.loc[train_index]
                        strat_test_set = df.loc[test_index]
                    
                    # At this point, we have our training set.
                    # Create a folder for the PocketSphinx training files
                    training_path = os.path.join(audiolog_dir,"pocketsphinx")
                    # The training folder holds two folders - etc/ and wav/
                    etc_path = os.path.join(training_path,"etc")
                    wav_path = os.path.join(training_path,"wav")
                    
                    # Start writing the train.fileids and train.transcription files
                    train_fileids = os.path.join(training_path,"train.fileids")
                    # This is a csv list of 

                # Get the dictionary. We want to list just the words that are
                # represented, so let's extract the actual words used:
                c.execute("with recursive split(word,rest) as (select '',upper(replace(replace(verified_transcription,'?',''),',','')) || ' ' from audiolog where type in ('active','passive') and reviewed!='' union all select substr(rest, 0, instr(rest,' ')),substr(rest,instr(rest,' ')+1) from split where rest <> '') select count(*)ncount,word from split where word!='' group by word order by 1 desc")
                rows = c.fetchall()
                response.append("<table><tr><th>Count</th><th>Word</th></tr>")
                for row in rows:
                    response.append("<tr><td>{}</td><td>{}</td>".format(str(row[0]),row[1]))
                response.append("</table>")
            else:
                response.append("<h2>Unknown STT engine: {}</h2>".format(train))
            # Prepare the json response
            messagetext = "<br /><br />\n".join(response)
            if(not continue_next):
                nextcommand = ""
            jsonstr = json.dumps({
                'message': messagetext,
                'engine': engine,
                'command': nextcommand
            })
            ret.append(jsonstr.encode("UTF-8"))
        else:
            start_response(
                '200 OK',
                [('content-type', 'text/html;charset=utf-8')]
            )
            ret.append(
                '<html><head><title>{} STT Training</title>'.format(
                    keyword
                ).encode("utf-8")
            )
            # Return the main page
            try:
                # If we are performing an update,
                # do so and fetch the next row id
                if(result and rowID):
                    # rowid should have been passed in
                    # if the rowid that was passed in does not exist,
                    # the following lines will have no effect
                    # FIXME: in this case, an error should be returned.
                    Update_record = Get_row(c, rowID)
                    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    if(Update_record):
                        if(result.lower() == "correct"):
                            c.execute(
                                " ".join([
                                    "update audiolog set",
                                    " verified_transcription=transcription,",
                                    " reviewed=:reviewed,",
                                    " wer=0",
                                    "where RowID=:RowID"
                                ]),
                                {
                                    "reviewed": now,
                                    "RowID": rowID
                                }
                            )
                        if(result.lower() == "update"):
                            if(len(verified_transcription)):
                                WER = wer(
                                    Update_record["Transcription"],
                                    verified_transcription
                                )
                                c.execute(
                                    " ".join([
                                        "update audiolog set ",
                                        " verified_transcription=:vt,",
                                        " reviewed=:reviewed,",
                                        " wer=:wer",
                                        "where RowID=:RowID"
                                    ]),
                                    {
                                        "vt": verified_transcription,
                                        "reviewed": now,
                                        "RowID": rowID,
                                        "wer": WER
                                    }
                                )
                            else:
                                c.execute(
                                    " ".join([
                                        "update audiolog set",
                                        " type='noise',",
                                        " verified_transcription='',",
                                        " reviewed=:reviewed,",
                                        " wer=1",
                                        "where RowID=:RowID"
                                    ]),
                                    {
                                        "reviewed": now,
                                        "RowID": rowID
                                    }
                                )
                        if(result.lower() == "nothing"):
                            c.execute(
                                " ".join([
                                    "update audiolog set"
                                    " type='noise',"
                                    " verified_transcription='',"
                                    " reviewed=:reviewed,"
                                    " wer=1 "
                                    "where RowID=:RowID"
                                ]),
                                {
                                    "reviewed": now,
                                    "RowID": rowID
                                }
                            )
                        if(result.lower() == "unclear"):
                            c.execute(
                                " ".join([
                                    "update audiolog set",
                                    " type='unclear',",
                                    " verified_transcription='',",
                                    " reviewed=:reviewed",
                                    "where RowID=:RowID"
                                ]),
                                {
                                    "reviewed": now,
                                    "RowID": rowID
                                }
                            )
                        conn.commit()
                        # fetch the next unreviewed rowid
                        rowID = fetch_next_unreviewed_rowID(c, rowID)
                    else:
                        ErrorMessage = "Row ID {} does not exist".format(
                            str(rowID)
                        )
                # get the first rowID
                first_rowID = fetch_first_rowID(c)
                # get the current rowID
                try:
                    rowID = fetch_current_rowID(c, rowID)
                except ValueError:
                    ErrorMessage = "Row {} not found".format(rowID)
                    rowID = fetch_current_rowID(c, None)
                # get the previous rowid
                prev_rowID = fetch_prev_rowID(c, rowID)
                # get the next rowid
                next_rowID = fetch_next_rowID(c, rowID)

                if(len(first_rowID)):
                    ret.append("""
<meta charset="utf-8"/>
<style type="text/css">
 /* Style the tab */
.tab {
  overflow: hidden;
  border: 1px solid #ccc;
  background-color: #f1f1f1;
}
/* Style the buttons that are used to open the tab content */
.tab button {
  background-color: inherit;
  float: left;
  border: none;
  outline: none;
  cursor: pointer;
  padding: 14px 16px;
  transition: 0.3s;
}
/* Change background color of buttons on hover */
.tab button:hover {
  background-color: #ddd;
}
/* Create an active/current tablink class */
.tab button.active {
  background-color: #ccc;
}
/* Style the tab content */
.tabcontent {
  display: none;
  padding: 6px 12px;
  border: 1px solid #ccc;
  border-top: none;
} 
.tabcontent.active {
  display: block;
}
.success {
  color: #0f0; /* green */
}
.failure {
  color: #f00; /* red */
}
</style>
<script language="javascript">
    var spin=0; // global spinner control
    function startSpinner(){
        // wait for any old spinners to exit before starting a new spinner.
        spintimer=window.setTimeout(function(){spin=1;moveSpinner(0)},250);
    }
    function moveSpinner(position){
        var s=document.getElementById("spinner");
        switch(position){
            case 0:
                s.innerHTML="-";
                break;
            case 1:
                s.innerHTML="\\\\";
                break;
            case 2:
                s.innerHTML="|";
                break;
            case 3:
                s.innerHTML="/";
                break;
        }
        if(spin){
            spintimer=window.setTimeout(function(){moveSpinner((position+1)%4)},250);
        }else{
            s.innerHTML="";
        }
    }
    function stopSpinner(){
        spin=0;
    }
    function openTab(evt, tabName) {
        // Declare all variables
        var i, tabcontent, tablinks;
        // Get all elements with class="tabcontent" and hide them
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].className = "tabcontent";
        }
        // Get all elements with class="tablinks" and remove the class "active"
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        // Show the current tab, and add an "active" class to the button that opened the tab
        document.getElementById(tabName).className = "tabcontent active";
        evt.currentTarget.className += " active";
    }
    
    // Submit an updated transcription to the server. Upon success,
    // make the "revert" button inactive
    function UpdateTranscription(RowID){
        var Transcription=document.getElementById("transcription_"+RowID).value;
        alert( "Transcription="+Transcription );
        var xhttp=new XMLHttpRequest();
        xhttp.onreadystatechange=function(){
            if( this.readyState==4 && this.status==200 ){
                // Check this.responseText
                var message=JSON.parse(this.responseText).message;
                if( message=="SUCCESS;Updated "+RowID ){
                    // disable reset button
                    document.getElementById("reset_"+RowID).disabled=true;
                }else{
                    //alert( "message="+message );
                }
            }else{
                //alert( "responseText="+this.responseText );
            }
        }
        xhttp.open("POST",window.location.href.split(/[?#]/)[0],true);
        var request=JSON.stringify({"action":"update","RowID":RowID,"Transcription":Transcription});
        xhttp.send(request);
    }

    // Delete a line from the database and, if the response is success,
    // delete the line from the page also.
    function DeleteAudio(RowID){
        var xhttp=new XMLHttpRequest();
        xhttp.onreadystatechange=function(){
            if( this.readyState==4 && this.status==200 ){
                // Check this.responseText to make sure it contains a success message
                var message=JSON.parse(this.responseText).message;
                if( message=="SUCCESS;Deleted "+RowID ){
                    document.getElementById("r"+RowID).parentNode.removeChild(document.getElementById("r"+RowID));
                }else{
                    //alert(message);
                }
            }
        };
        xhttp.open("POST",window.location.href.split(/[?#]/)[0],true);
        var request='{"action":"delete","RowID":"'+RowID+'"}';
        xhttp.send(request);
    }

    function GoRowID(RowID){
        document.location.href="http://"+window.location.host+window.location.pathname+"?RowID="+RowID;
    }

    function ValidateForm(){
        var Checked=document.querySelector("input[name='result']:checked");
        var Ret=true;
        if( !Checked ){
            Ret=false;
            alert("Please select an option");
        }
        return Ret;
    }
    
    function Train(clear,engine,command){
        stopSpinner();
        if(clear){
            document.getElementById("Result").innerHTML = "";
        }
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function(){
            if(this.readyState==4){
                stopSpinner();
                if(this.status==200){
                    var response=JSON.parse(this.responseText);
                    document.getElementById("Result").innerHTML += response.message + '<br /><br />';
                    if(response.command){
                        Train(false,response.engine,response.command);
                    }else{
                        document.getElementById("Result").innerHTML += "<h2>Training Complete</h2>";
                    }
                }else{
                    document.getElementById("Result").innerHTML += "An error occurred. ReadyState: "+this.readyState+" Status: "+this.status+"<br />"+this.responseText;
                }
            }
        };
        url = location.toString().replace(location.search, "");
        
        xhttp.open("POST",url,true);
        xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhttp.send("engine="+engine+"&command="+command);
        startSpinner();
    }
</script>""".encode("utf-8"))
                    ret.append('''
</head>
<body>
<!-- Tab links -->
<div class="tab">
  <button class="tablinks active" onclick="openTab(event, 'Verify')">Verify transciptions</button>
  <button class="tablinks" onclick="openTab(event, 'Train')">Train STT Engines</button>
</div>
<!-- Tab content -->
<div id="Verify" class="tabcontent active">
'''.encode("utf-8")
                    )

                    Current_record = Get_row(c, rowID)

                    # if this has been reviewed, figure out
                    # what option was selected
                    Checked = 'checked="checked"'
                    Unchecked = ''
                    Disabled = 'disabled="disabled"'
                    Enabled = ''
                    Result_correct = Unchecked
                    Result_update = Unchecked
                    Result_nothing = Unchecked
                    Result_unclear = Unchecked
                    Verified_transcription_state = Disabled
                    if(len(Current_record["Reviewed"])):
                        if(Current_record["Verified_transcription"]):
                            if(Current_record[
                                "Transcription"
                            ] == Current_record[
                                "Verified_transcription"
                            ]):
                                Result_correct = Checked
                            else:
                                Result_update = Checked
                                Verified_transcription_state = Enabled
                        else:
                            if(Current_record["Type"] == "noise"):
                                Result_nothing = Checked
                            else:
                                Result_unclear = Checked

                    if(not Current_record["Verified_transcription"]):
                        Current_record[
                            "Verified_transcription"
                        ] = Current_record[
                            "Transcription"
                        ]

                    # Serve the body of the page
                    if(Debug):
                        # Debug info
                        ret.append("""<ul>""".encode("utf-8"))
                        ret.append("""<li>post_data: {}</li>""".format(
                            post_data
                        ).encode("utf-8"))
                        ret.append("""<li>Result: {}</li>""".format(
                            result
                        ).encode("utf-8"))

                        if(result == "update"):
                            ret.append(
                                "<li>Verified_transcription: {}</li>".format(
                                    verified_transcription
                                ).encode("utf-8")
                            )
                        ret.append("</ul>".encode("utf-8"))

                        ret.append("<ul>".encode("utf-8"))
                        ret.append("<li>Recorded: {}</li>".format(
                            Current_record["Recorded"]
                        ).encode("utf-8"))
                        ret.append("<li>Filename: {}</li>".format(
                            Current_record["Filename"]
                        ).encode("utf-8"))
                        ret.append("<li>Type: {}</li>".format(
                            Current_record["Type"]
                        ).encode("utf-8"))
                        ret.append("<li>Transcription: {}</li>".format(
                            Current_record["Transcription"]
                        ).encode("utf-8"))
                        ret.append("<li>Verified_transcription: {}</li>".format(
                            Current_record["Verified_transcription"]
                        ).encode("utf-8"))
                        ret.append("<li>Speaker: {}</li>".format(
                            Current_record["Speaker"]
                        ).encode("utf-8"))
                        ret.append("<li>Reviewed: {}</li>".format(
                            Current_record["Reviewed"]
                        ).encode("utf-8"))
                        ret.append("<li>Wer: {}</li>".format(
                            Current_record["WER"]
                        ).encode("utf-8"))
                        ret.append("<li>Result_correct: {}</li>".format(
                            Result_correct
                        ).encode("utf-8"))
                        ret.append("""<li>Result_update: {}</li>""".format(
                            Result_update
                        ).encode("utf-8"))
                        ret.append("""<li>Result_nothing: {}</li>""".format(
                            Result_nothing
                        ).encode("utf-8"))
                        ret.append("""</ul>""".encode("utf-8"))

                    ret.append("""<h1>{} transcription {} ({})</h1>""".format(
                        keyword,
                        rowID,
                        Current_record["Type"]).encode("utf-8")
                    )
                    if(ErrorMessage):
                        ret.append("""<p class="Error">{}</p>""".format(
                            ErrorMessage
                        ).encode("utf-8"))
                    ret.append(
                        " ".join([
                            '<audio',
                            'controls="controls"',
                            'type="audio/wav"',
                            'style="width:100%%">',
                            '<source src="?wavfile={}" />',
                            '</audio><br />'
                        ]).format(Current_record["Filename"]).encode("utf-8")
                    )
                    ret.append(
                        ' '.join([
                            '{} heard',
                            '"<span style="font-weight:bold">{}</span>"<br />'
                        ]).format(
                            keyword,
                            Current_record["Transcription"]
                        ).encode("utf-8"))
                    ret.append("What did you hear?<br />".encode("utf-8"))
                    ret.append(' '.join([
                        '<form method="POST"',
                        'onsubmit="return ValidateForm()">'
                    ]).encode("utf-8"))
                    ret.append(
                        '<input type="hidden" name="RowID" value="{}"/>'.format(
                            rowID
                        ).encode("utf-8")
                    )
                    ret.append("""<input type="radio" id="update_result_correct" name="result" value="correct" {} onclick="document.getElementById('update_verified_transcription').disabled=true"/> <label for="update_result_correct">The transcription is correct. I heard the same thing</label><br />""".format(
                        Result_correct
                    ).encode("utf-8"))
                    ret.append("""<input type="radio" id="update_result_update" name="result" value="update" {} onclick="document.getElementById('update_verified_transcription').disabled=false"/> <label for="update_result_update">The transcription is not correct. This is what I heard:</label><br /><textarea id="update_verified_transcription" name="verified_transcription" style="margin-left: 20px" {}>{}</textarea><br />""".format(
                        Result_update,
                        Verified_transcription_state,
                        Current_record["Verified_transcription"]
                    ).encode("utf-8"))
                    ret.append("""<input type="radio" id="update_result_nothing" name="result" value="nothing" {} onclick="document.getElementById('update_verified_transcription').disabled=true"/> <label for="update_result_nothing">This was just noise with no voices.</label><br />""".format(
                        Result_nothing
                    ).encode("utf-8"))
                    ret.append("""<input type="radio" id="update_result_unclear" name="result" value="unclear" {} onclick="document.getElementById('update_verified_transcription').disabled=true"/> <label for="update_result_unclear">This was too unclear to understand.</label><br />""".format(
                        Result_unclear
                    ).encode("utf-8"))
                    ret.append(
                        '<input type="submit" value="Submit"/><br />'.encode(
                            "utf-8"
                        )
                    )
                    if(prev_rowID):
                        ret.append(
                            ' '.join([
                                '<input type="button" value="Prev"',
                                'onclick="GoRowID({})"/>'
                            ]).format(prev_rowID).encode("utf-8")
                        )
                    if(next_rowID):
                        ret.append(
                            ' '.join([
                                '<input type="button" value="Next"',
                                'onclick="GoRowID({})"/>'
                            ]).format(next_rowID).encode("utf-8")
                        )
                    else:
                        ret.append("""All transcriptions verified""".encode(
                            "utf-8"
                        ))
                    ret.append('''
</div><!-- Verify -->
<div id="Train" class="tabcontent">
<form name="Train">
<input type="button" value="Adapt Pocketsphinx Model" onclick="Train(true,'PocketSphinx_adapt','checkenviron')"><br />
<input type="button" value="Train Pocketsphinx Acoustic Model" onclick="Train(true,'PocketSphinx_train','checkenviron')"><br />
</form>
<div id="Result">
</div>
<div id="spinner">
</div>
</div><!-- Train -->
'''.encode('UTF-8')
                    )
                    ret.append("""</body></html>""".encode("utf-8"))
                else:
                    ret = [
                        "".join([
                            "<html>",
                            "<head><title>Nothing to validate</title></head>",
                            "<body><h1>Nothing to validate</h1></body></html>"
                        ]).encode("utf-8")
                    ]
            except sqlite3.OperationalError as e:
                ret.append(
                    "".join([
                        '</head>',
                        '<body>SQLite error: {}</body>',
                        '</html>'
                    ]).format(e).encode("utf-8"))
        return ret


class ThreadingWSGIServer(ThreadingMixIn, wsgiref.simple_server.WSGIServer):
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Naomi Voice Control Center')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show debug messages'
    )
    p_args = parser.parse_args()
    if p_args.debug:
        Debug = True
    port = 8080
    print("Listening on port {}".format(str(port)))
    print("Point your browser to http://{}:{}".format(socket.getfqdn(),str(port)))
    server = wsgiref.simple_server.make_server(
        '',
        port,
        application,
        ThreadingWSGIServer
    )
    server.serve_forever()
