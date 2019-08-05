#!/usr/bin/env python3

# This version of NaomiSTTTrainer allows the user to step through one sample
# at a time, instead of returning a table full of samples.
# My assumption is that for the most part, you only need to validate the record
# once, after that it should automatically skip all the records that have
# already been verified.

# -*- coding: utf-8 -*-
import argparse
import json
import logging
import os
import pkg_resources
import re
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
from urllib.parse import unquote


# Set Debug to True to see debugging information
Debug = False
_logger = logging.getLogger(__name__)


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


def application(environ, start_response):
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
        description = []
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
                    engine = namevalue[1]
                if(namevalue[0].lower() == "command"):
                    command = namevalue[1].lower()
                if(namevalue[0].lower() == "description"):
                    description.append(namevalue[1])

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
                        print("plugin.HandleCommand({}, {})".format(command, description))
                        response, nextcommand, description = plugin.HandleCommand(command, description)
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
            messagetext = "<br /><br />\n".join(response)
            if(not continue_next):
                nextcommand = ""
            jsonstr = json.dumps({
                'message': messagetext,
                'engine': engine,
                'command': nextcommand,
                'description': description
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
                    print("Result: {}".format(result))
                    # rowid should have been passed in
                    # if the rowid that was passed in does not exist,
                    # the following lines will have no effect
                    # FIXME: in this case, an error should be returned.
                    Update_record = Get_row(c, rowID)
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
                        c.execute(
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
                            WER = wer(
                                transcription,
                                verified_transcription
                            )
                            c.execute(
                                " ".join([
                                    "update audiolog set ",
                                    " type=:type,",
                                    " verified_transcription=:vt,",
                                    " reviewed=:reviewed,",
                                    " wer=:wer",
                                    "where RowID=:RowID"
                                ]),
                                {
                                    "type": recording_type,
                                    "vt": verified_transcription,
                                    "reviewed": now,
                                    "wer": WER,
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
                        var description = "";
                        if(response.description){
                            description = response.description;
                        }
                        Train(false,response.engine,response.command,description);
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
                    ret.append("""<input type="radio" id="update_result_nothing" name="result" value="noise" {} onclick="document.getElementById('update_verified_transcription').disabled=true"/> <label for="update_result_nothing">This was just noise with no voices.</label><br />""".format(
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
'''.encode('utf-8')
                    )
                    for info in plugins.get_plugins_by_category('stt_trainer'):
                        ret.append('''<input type="button" value="{plugin_name}" onclick="Train(true,'{plugin_name}','checkenviron')"><br />'''.format(plugin_name=info.name).encode("utf-8"))
                    ret.append('''
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
        print("Setting logging level to DEBUG")
        logging.basicConfig(
            level=logging.DEBUG
        )
    # Load the STT_Trainer plugins
    plugin_directories = [
        paths.config('plugins', 'stt_trainer'),
        pkg_resources.resource_filename(__name__, os.path.join('plugins', 'stt_trainer'))
    ]
    plugins = pluginstore.PluginStore(plugin_directories)
    plugins.detect_plugins()
    port = 8080
    url = "http://{}:{}".format(socket.getfqdn(), str(port))
    print("Listening on port {}".format(str(port)))
    print("Point your browser to {}".format(url))
    server = wsgiref.simple_server.make_server(
        '',
        port,
        application,
        ThreadingWSGIServer
    )
    thread = Thread(target=webbrowser.open, args=([url]))
    thread.start()
    server.serve_forever()
