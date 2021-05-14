#!/usr/bin/env python3

# This version of NaomiSTTTrainer allows the user to step through one sample
# at a time, instead of returning a table full of samples.
# My assumption is that for the most part, you only need to validate the record
# once, after that it should automatically skip all the records that have
# already been verified.

# -*- coding: utf-8 -*-
import argparse
import cgi
import cgitb
import json
import logging
import os
import pkg_resources
import socket
import sqlite3
import webbrowser
import wsgiref.simple_server
from datetime import datetime
from jiwer import wer
from naomi import paths
from naomi import profile
from naomi import pluginstore
from socketserver import ThreadingMixIn
from threading import Thread


# Set Debug to True to see debugging information
# or use the --debug flag on the command line
Debug = False
_logger = logging.getLogger(__name__)


def Get_row(conn, rowID):
    c = conn.execute(
        " ".join([
            "select",
            " datetime,",
            " filename,",
            " type,",
            " transcription,",
            " verified_transcription,",
            " speaker,",
            " reviewed,",
            " wer,",
            " intent,",
            " score,",
            " verified_intent",
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
            print("Intent Type=%s" % type(row[8]))
            print("Score Type=%s" % type(row[9]))
            print("Verified Intent Type=%s" % type(row[10]))
        Record = {
            "Recorded": str(row[0]),
            "Filename": str(row[1]),
            "Type": str(row[2]),
            "Transcription": str(row[3]),
            "Verified_transcription": str(row[4]),
            "Speaker": str(row[5]),
            "Reviewed": str(row[6]),
            "WER": str(row[7]),
            "intent": str(row[8]),
            "score": str(row[9]),
            "verified_intent": str(row[10])
        }
    return Record


def verify_row_id(conn, rowID):
    Ret = True
    c = conn.execute("select RowID from audiolog where RowID=:RowID", {"RowID": rowID})
    row = c.fetchone()
    if(row is None):
        Ret = False
    return Ret


def fetch_first_rowID(conn):
    c = conn.execute("select RowID from audiolog order by RowID asc limit 1")
    row = c.fetchone()
    if(row is None):
        rowID = None
    else:
        rowID = str(row[0])
    return rowID


def fetch_first_unreviewed_rowID(conn):
    return fetch_next_unreviewed_rowID(conn, "0")


def fetch_prev_rowID(conn, rowID):
    # get the previous rowid
    c = conn.execute(
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


def fetch_current_rowID(conn, rowID):
    if(rowID):
        c = conn.execute(
            "select RowID from audiolog where RowID=:RowID",
            {"RowID": rowID}
        )
        row = c.fetchone()
        if(row is None):
            raise ValueError("RowID %s not found" % rowID)
        else:
            rowID = str(row[0])
    else:
        rowID = fetch_first_unreviewed_rowID(conn)
    if(not rowID):
        # if there are no unreviewed row ID's, set to the last rowid
        rowID = fetch_last_rowID(c)
    return rowID


def fetch_next_rowID(conn, rowID):
    # get the previous rowid
    print("rowID={}".format(rowID))
    c = conn.execute(
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


def fetch_next_unreviewed_rowID(conn, rowID):
    # Here, if there is both a passive and active transcription
    # then I want to look at the active.
    # This is because only the active has the intent.
    c = conn.execute(
        " ".join([
            "select",
            " filename",
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
        filename = str(row[0])
        c = conn.execute(
            " ".join([
                "select",
                " RowID",
                "from audiolog",
                "where filename=:Filename and reviewed=''",
                "order by type asc",
                "limit 1"
            ]),
            {"Filename": filename}
        )
        row = c.fetchone()
        if(row is None):
            next_rowID = None
        else:
            next_rowID = str(row[0])
    return next_rowID


def fetch_last_rowID(conn):
    c = conn.execute("select RowID from audiolog order by RowID desc limit 1")
    row = c.fetchone()
    if(row is None):
        rowID = None
    else:
        rowID = str(row[0])
    return rowID


def fetch_total_rows(conn):
    c = conn.execute("select max(RowID)MaxRow from audiolog")
    return str(c.fetchone()[0])


# Replaces any punctuation characters with spaces and converts to upper case
def clean_transcription(transcription):
    print("transcription type={}".format(type(transcription)))
    return transcription.translate(
        dict((ord(char), None) for char in """][}{!@#$%^&*)(,."'></?\\|=+-_""")
    ).upper()


def fetch_intents(conn):
    # Get a list of all intents
    # This will be a combination of all intents from detected
    # plugins, plus any intents in either intents or verified intents
    c = conn.execute(" ".join([
        "select intent from (",
        "   select ",
        "       intent",
        "   from audiolog",
        "   union select",
        "       verified_intent as intent",
        "   from audiolog",
        ")a where intent not in ('', 'unclear') order by intent"
    ]))
    _intents = {}
    for row in c.fetchall():
        _intents[row[0]] = 1
    ps = pluginstore.PluginStore()
    ps.detect_plugins()
    for info in ps.get_plugins_by_category("speechhandler"):
        try:
            plugin = info.plugin_class(
                info,
                profile.get_profile()
            )
            if(hasattr(plugin, "intents")):
                intents = [intent for intent in plugin.intents()]
                for intent in intents:
                    _intents[intent] = 1
        except Exception as e:
            _logger.warn(
                "Plugin '{}' skipped! (Reason: {})".format(
                    info.name,
                    e.message if hasattr(e, 'message') else 'Unknown'
                ),
                exc_info=True
            )
    return sorted([intent for intent in _intents])


def application(environ, start_response):
    keyword = profile.get_profile_var(["keyword"], ["Naomi"])
    if(isinstance(keyword, list)):
        keyword = keyword[0]
    print("PATH_INFO=%s" % environ["PATH_INFO"])
    if(environ["PATH_INFO"] == "/favicon.ico"):
        start_response(
            '404 Not Found',
            [('content-type', 'text/plain;charset=utf-8')]
        )
        ret = ["404 Not Found"]
        return [line.encode("UTF-8") for line in ret]
    else:
        audiolog_dir = paths.sub("audiolog")
        audiolog_db = os.path.join(audiolog_dir, "audiolog.db")
        wavfile = ""
        rowID = ""
        first_rowID = ""
        prev_rowID = ""
        next_rowID = ""
        result = ""
        speaker = ""
        verified_transcription = ""
        post_data = ""
        engine = ""
        verified_intent = ""
        description = []

        # gather parameters from GET
        fields = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=environ,
            keep_blank_values=1
        )
        for field in fields:
            # Don't try to process files here
            f = fields[field]
            # if a parameter has been passed in more than once (sometimes
            # this happens when a parameter is passed in through a form and
            # the querystring) just take the first value.
            if isinstance(f, list):
                f = f[0]
            value = f.value
            if not f.filename:
                if(field.lower() == "wavfile"):
                    wavfile = os.path.join(audiolog_dir, value)
                if(field.lower() == "rowid"):
                    rowID = value
                if(field.lower() == "result"):
                    result = value.lower()
                if(field.lower() == "verified_transcription"):
                    verified_transcription = value
                if(field.lower() == "engine"):
                    engine = value
                if(field.lower() == "command"):
                    command = value
                if(field.lower() == "description"):
                    description.append(value)
                if(field.lower() == "speaker"):
                    speaker = value
                if(field.lower() == "verified_intent"):
                    verified_intent = value

        # Handle the request
        # serve a .wav file
        ErrorMessage = None
        if(len(wavfile) and os.path.isfile(wavfile)):
            start_response('200 OK', [('content-type', 'audio/wav')])
            with open(wavfile, "rb") as w:
                ret = [w.read()]
            return ret
        # open a connection to the database
        try:
            conn = sqlite3.connect(audiolog_db)
        except sqlite3.OperationalError:
            ret = []
            start_response(
                '200 OK',
                [('content-type', 'text/html;charset=utf-8')]
            )
            ret.append("<html><head><title>Could not open database</title></head>")
            ret.append("<body><h2>Could not open database file {}</h2>".format(audiolog_db))
            ret.append("<p>Try adding the following lines to your profile ({}) and then asking me a few questions:<br />".format(profile.profile_file))
            ret.append("<pre>\taudiolog:\n\t\tsave_audio\n</pre>")
            return [line.encode("UTF-8") for line in ret]
        # Check and make sure the speaker field exists
        c = conn.execute("select distinct speaker from audiolog order by 1")
        # fetchall returns all rows as tuples, take the first (and only)
        # element of each tuple
        speakers = [speaker[0] for speaker in c.fetchall()]
        # Start the html response
        ret = []
        # serve a train response. We will put this in a div on the Train
        # tab, so we don't have to regenerate everything.
        if(len(engine)):
            start_response(
                '200 OK',
                [('content-type', 'text/json;charset=utf-8')]
            )
            continue_next = True
            nextcommand = ""
            response = []
            found_plugin = False
            for info in plugins.get_plugins_by_category('stt_trainer'):
                if(info.name == engine):
                    found_plugin = True
                    try:
                        plugin = info.plugin_class(info, profile.get_profile())
                        print("plugin.HandleCommand(command='{}', description='{}', conn=conn, fields=fields, output_type='html')".format(command, description))
                        response, nextcommand, description = plugin.HandleCommand(command=command, description=description, conn=conn, fields=fields, output_type='html')
                    except Exception as e:
                        _logger.warn(
                            "Plugin '{}' skipped! (Reason: {})".format(
                                info.name,
                                e.message if hasattr(e, 'message') else 'Unknown'
                            ),
                            exc_info=True
                        )
            if(not found_plugin):
                response = ["Unknown STT Trainer: {}".format(engine)]
            # Prepare the json response
            messagetext = "\n".join(response)
            if(not continue_next):
                nextcommand = ""
            jsonstr = json.dumps({
                'message': messagetext,
                'engine': engine,
                'command': nextcommand,
                'description': description
            })
            ret.append(jsonstr)
        else:
            start_response(
                '200 OK',
                [('content-type', 'text/html;charset=utf-8')]
            )
            ret.append(
                '<html><head><title>{} STT Training</title>'.format(
                    keyword
                )
            )
            # Return the main page
            try:
                # If we are performing an update,
                # do so and fetch the next row id
                if(result and rowID):
                    print("Result: {}".format(result))
                    # rowid should have been passed in
                    # if the rowid that was passed in does not exist,
                    # the following lines will have no effect
                    # FIXME: in this case, an error should be returned.
                    Update_record = Get_row(conn, rowID)
                    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    if(Update_record):
                        # Since an audio file can be associated with more
                        # than one transcription (since both a passive and
                        # active transcription can be run on the same audio
                        # file) we need to update each record with the same
                        # transcription with its own WER.
                        # Get a list of records that have the same filename
                        result = result.lower()
                        if(result == "correct"):
                            # if the current result matches the transcription,
                            # then verified transcription = transcription
                            # and the type should remain unchanged
                            verified_transcription = Update_record['Transcription']
                        if(result == "noise"):
                            # If the user selected "noise" then the verified
                            # transcription is blank
                            verified_transcription = ""
                        if(result == "unclear"):
                            # Unclear means that there is no verified
                            # transcription and the sample is unusable
                            # for either training the speech recognition
                            # or the noise detection. We can go ahead
                            # and run WER on it, but it is unlikely to
                            # be used.
                            verified_transcription = ""
                            recording_type = "unclear"
                        verified_transcription = verified_transcription.strip()
                        filename = Update_record["Filename"]
                        c = conn.execute(
                            " ".join([
                                "select",
                                " RowID,",
                                " transcription,",
                                " type",
                                "from audiolog",
                                "where RowID=:RowID or (",
                                " filename=:filename and reviewed=''",
                                ")"
                            ]),
                            {
                                'RowID': rowID,
                                'filename': filename
                            }
                        )
                        for row in c.fetchall():
                            rowID = row[0]
                            transcription = row[1]
                            recording_type = row[2]
                            if(len(verified_transcription) == 0):
                                recording_type = "noise"
                                print("Setting recording_type to noise")
                                if(result == "unclear"):
                                    recording_type = "unclear"
                                    print("Setting recording_type to unclear")
                            # calculate the word error rate
                            WER = 0
                            if(len(transcription) > 0):
                                WER = wer(
                                    transcription,
                                    verified_transcription
                                )
                            c = conn.execute(
                                " ".join([
                                    "update audiolog set ",
                                    " type=:type,",
                                    " verified_transcription=:vt,",
                                    " speaker=:speaker,"
                                    " reviewed=:reviewed,",
                                    " wer=:wer,",
                                    " verified_intent=:verified_intent",
                                    "where RowID=:RowID"
                                ]),
                                {
                                    "type": recording_type,
                                    "vt": verified_transcription,
                                    "speaker": speaker,
                                    "reviewed": now,
                                    "wer": WER,
                                    "verified_intent": verified_intent,
                                    "RowID": rowID
                                }
                            )
                            conn.commit()
                        # fetch the next unreviewed rowid
                        rowID = fetch_next_unreviewed_rowID(conn, rowID)
                    else:
                        ErrorMessage = "Row ID {} does not exist".format(
                            str(rowID)
                        )
                # get the first rowID
                first_rowID = fetch_first_rowID(conn)
                # get the current rowID
                try:
                    rowID = fetch_current_rowID(conn, rowID)
                except ValueError:
                    ErrorMessage = "Row {} not found".format(rowID)
                    rowID = fetch_current_rowID(conn, None)
                # get the previous rowid
                prev_rowID = fetch_prev_rowID(conn, rowID)
                # get the next rowid
                next_rowID = fetch_next_rowID(conn, rowID)
                totalRows = fetch_total_rows(conn)

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
    var spintimer;
    function startSpinner(){
        // kill any old spinner
        window.clearTimeout(spintimer);
        spin=1;
        spintimer=window.setTimeout(function(){moveSpinner(0)},250);
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
        window.clearTimeout(spintimer);
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

    function Train(clear, engine, command, description, additionaldata=""){
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
                        var description = "";
                        if(response.description){
                            description = response.description;
                        }
                        Train(false,response.engine,response.command,description);
                    }
                }else{
                    document.getElementById("Result").innerHTML += "An error occurred. ReadyState: "+this.readyState+" Status: "+this.status+"<br />"+this.responseText;
                }
            }
        };
        url = location.toString().replace(location.search, "");

        xhttp.open("POST",url,true);
        xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhttp.send("engine="+encodeURIComponent(engine)+"&command="+encodeURIComponent(command)+"&description="+encodeURIComponent(description));
        startSpinner();
        return false;
    }
</script>""")
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
                    ''')

                    Current_record = Get_row(conn, rowID)

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
                        ret.append("""<ul>""")
                        ret.append("""<li>post_data: {}</li>""".format(
                            post_data
                        ))
                        ret.append("""<li>Result: {}</li>""".format(
                            result
                        ))

                        if(result == "update"):
                            ret.append(
                                "<li>Verified_transcription: {}</li>".format(
                                    verified_transcription
                                )
                            )
                        ret.append("</ul>")

                        ret.append("<ul>")
                        ret.append("<li>Recorded: {}</li>".format(
                            Current_record["Recorded"]
                        ))
                        ret.append("<li>Filename: {}</li>".format(
                            Current_record["Filename"]
                        ))
                        ret.append("<li>Type: {}</li>".format(
                            Current_record["Type"]
                        ))
                        ret.append("<li>Transcription: {}</li>".format(
                            Current_record["Transcription"]
                        ))
                        ret.append("<li>Verified_transcription: {}</li>".format(
                            Current_record["Verified_transcription"]
                        ))
                        ret.append("<li>Speaker: {}</li>".format(
                            Current_record["Speaker"]
                        ))
                        ret.append("<li>Speaker: {}</li>".format(
                            Current_record["Speaker"]
                        ))
                        ret.append("<li>Reviewed: {}</li>".format(
                            Current_record["Reviewed"]
                        ))
                        ret.append("<li>Wer: {}</li>".format(
                            Current_record["WER"]
                        ))
                        ret.append("<li>Result_correct: {}</li>".format(
                            Result_correct
                        ))
                        ret.append("""<li>Result_update: {}</li>""".format(
                            Result_update
                        ))
                        ret.append("""<li>Result_nothing: {}</li>""".format(
                            Result_nothing
                        ))
                        ret.append("""</ul>""")
                    ret.append("""<h1>{} transcription {} of {} ({} - {})</h1>""".format(
                        keyword,
                        rowID,
                        totalRows,
                        Current_record["Type"],
                        Current_record["Recorded"]
                    ))
                    if(ErrorMessage):
                        ret.append("""<p class="Error">{}</p>""".format(
                            ErrorMessage
                        ))
                    ret.append(
                        " ".join([
                            '<audio',
                            'controls="controls"',
                            'type="audio/wav"',
                            'style="width:100%%">',
                            '<source src="?wavfile={}" />',
                            '</audio><br />'
                        ]).format(Current_record["Filename"])
                    )
                    ret.append(
                        ' '.join([
                            '{} heard',
                            '"<span style="font-weight:bold">{}</span>"<br />'
                        ]).format(
                            keyword,
                            Current_record["Transcription"]
                        ))
                    ret.append("What did you hear?<br />")
                    ret.append(' '.join([
                        '<form method="POST" action="/"',
                        'onsubmit="return ValidateForm()">'
                    ]))
                    ret.append(
                        '<input type="hidden" name="RowID" value="{}"/>'.format(
                            rowID
                        )
                    )
                    ret.append("""<input type="radio" id="update_result_correct" name="result" value="correct" {} onclick="document.getElementById('update_verified_transcription').disabled=true"/> <label for="update_result_correct">The transcription is correct. I heard the same thing</label><br />""".format(
                        Result_correct
                    ))
                    ret.append("""<input type="radio" id="update_result_update" name="result" value="update" {} onclick="document.getElementById('update_verified_transcription').disabled=false"/> <label for="update_result_update">The transcription is not correct. This is what I heard:</label><br /><textarea id="update_verified_transcription" name="verified_transcription" style="margin-left: 20px" {}>{}</textarea><br />""".format(
                        Result_update,
                        Verified_transcription_state,
                        Current_record["Verified_transcription"]
                    ))
                    ret.append("""<input type="radio" id="update_result_nothing" name="result" value="noise" {} onclick="document.getElementById('update_verified_transcription').disabled=true"/> <label for="update_result_nothing">This was just noise with no voices.</label><br />""".format(
                        Result_nothing
                    ))
                    ret.append("""<input type="radio" id="update_result_unclear" name="result" value="unclear" {} onclick="document.getElementById('update_verified_transcription').disabled=true"/> <label for="update_result_unclear">This was not directed to {} or was too unclear to understand.</label><br />""".format(
                        Result_unclear,
                        keyword
                    ))
                    ret.append("""<label for="Speaker">Speaker</label><br /><input type="text" id="Speaker" name="Speaker" value="{}" list="speakerList"><datalist id="speakerList">""".format(Current_record["Speaker"] if len(Current_record["Speaker"]) else speaker))
                    for speaker in speakers:
                        ret.append("""<option value="{}">""".format(speaker))
                    ret.append("""</datalist><br /><br />""")
                    if(Current_record["Type"] == 'active'):
                        Verified_intent = Current_record["verified_intent"]
                        if(Verified_intent == "None"):
                            Verified_intent = Current_record["intent"]
                        ret.append("""Intent: {} ({})<br />""".format(Current_record["intent"], Current_record["score"]))
                        ret.append("""Correct intent: <select name="Verified_Intent">""")
                        ret.append("""<option value="unclear">unclear</option>""")
                        for intent in fetch_intents(c):
                            selected = ""
                            if(intent == Verified_intent):
                                selected = " selected"
                            ret.append("""<option{}>{}</option>""".format(selected, intent))
                        ret.append("""</select><br /><br />""")
                    ret.append(
                        '<input type="submit" value="Submit"/><br />'
                    )
                    if(prev_rowID):
                        ret.append(
                            ' '.join([
                                '<input type="button" value="Prev"',
                                'onclick="GoRowID({})"/>'
                            ]).format(prev_rowID)
                        )
                    if(next_rowID):
                        ret.append(
                            ' '.join([
                                '<input type="button" value="Next"',
                                'onclick="GoRowID({})"/>'
                            ]).format(next_rowID)
                        )
                    else:
                        ret.append("""All transcriptions verified""")
                    ret.append('''
</div><!-- Verify -->
<div id="Train" class="tabcontent">
<form name="Train">
                    ''')
                    for info in plugins.get_plugins_by_category('stt_trainer'):
                        ret.append('''<input type="button" value="{plugin_name}" onclick="Train(true,'{plugin_name}','','')"><br />'''.format(plugin_name=info.name))
                    ret.append('''
</form>
<div id="Result">
</div>
<div id="spinner">
</div>
</div><!-- Train -->
                    ''')
                    ret.append("""</body></html>""")
                else:
                    ret = [
                        "".join([
                            "<html>",
                            "<head><title>Nothing to validate</title></head>",
                            "<body><h1>Nothing to validate</h1></body></html>"
                        ])
                    ]
            except sqlite3.OperationalError as e:
                ret.append(
                    "".join([
                        '</head>',
                        '<body>SQLite error: {}</body>',
                        '</html>'
                    ]).format(e))
        # Save (commit) the changes
        conn.commit()
        conn.close()
        return [line.encode("UTF-8") for line in ret]


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
        print("Setting logging level to DEBUG")
        logging.basicConfig(
            level=logging.DEBUG
        )
    # Load the STT_Trainer plugins
    plugin_directories = [
        paths.sub('plugins', 'stt_trainer'),
        pkg_resources.resource_filename(__name__, os.path.join('plugins', 'stt_trainer'))
    ]
    plugins = pluginstore.PluginStore(plugin_directories)
    plugins.detect_plugins()
    port = 8080
    url = "http://{}:{}".format(socket.getfqdn(), str(port))
    print("Listening on port {}".format(str(port)))
    print("Point your browser to {}".format(url))
    cgitb.enable()
    server = wsgiref.simple_server.make_server(
        '',
        port,
        application,
        ThreadingWSGIServer
    )
    thread = Thread(target=webbrowser.open, args=([url]))
    thread.start()
    server.serve_forever()
