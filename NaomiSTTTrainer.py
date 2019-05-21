#!/usr/bin/env python3

# This version of NaomiSTTTrainer allows the user to step through one sample
# at a time, instead of returning a table full of samples.
# My assumption is that for the most part, you only need to validate the record
# once, after that it should automatically skip all the records that have
# already been verified.

# -*- coding: utf-8 -*-
from datetime import datetime
import wsgiref.simple_server
from socketserver import ThreadingMixIn
import re
import sqlite3
from urllib.parse import unquote
import os
from naomi import paths
from naomi import profile


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


# Calculate word error rate as a percent between 1 and 0 with 0 being a perfect
# translation and 1 being completely wrong.
# That being said, I'm not sure if it's better to atomocize each transaction,
# so a single word misheard has the same weight as several words misheard.
# Based on the python implementation by Space Pinapple
# http://progfruits.blogspot.com/2014/02/word-error-rate-wer-and-word.html
def wer(hypothesis, reference):
    h = clean_transcription(hypothesis).split()
    r = clean_transcription(reference).split()
    if(Debug):
        print("Hypothesis %s" % h)
        print("Reference %s" % r)
    # Costs contains costs
    c = [[0 for inner in range(len(h) + 1)] for outer in range(len(r) + 1)]
    # Backtrace holds operations performed so
    # we can backtrace the shortest route
    b = [[0 for inner in range(len(h) + 1)] for outer in range(len(r) + 1)]

    OP_OK  = 0
    OP_SUB = 1
    OP_INS = 2
    OP_DEL = 3

    # First row achieve zero hypothesis words by deleting reference words
    for i in range(1, len(r) + 1):
        c[i][0] = i
        b[i][0] = OP_DEL

    # First column achieve full hypothesis by adding
    # all words to empty reference
    for j in range(1, len(h) + 1):
        c[0][j] = j
        b[0][j] = OP_INS

    # Computation
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if(r[i - 1] == h[j - 1]):
                c[i][j] = c[i - 1][j - 1]
                b[i][j] = OP_OK
            else:
                substitutionCost = c[i - 1][j - 1]
                insertionCost = c[i][j - 1]
                deletionCost = c[i - 1][j]

                c[i][j] = min(substitutionCost, insertionCost, deletionCost)
                if(c[i][j] == substitutionCost):
                    b[i][j] = OP_SUB
                elif(c[i][j] == insertionCost):
                    b[i][j] = OP_INS
                else:
                    b[i][j] = OP_DEL
    # back trace through best route
    i = len(r)
    j = len(h)
    numSub = 0
    numDel = 0
    numIns = 0
    numCor = 0
    if(Debug):
        print("OP\tREF\tHYP")
        lines = []
    while(i > 0 or j > 0):
        if(b[i][j] == OP_OK):
            numCor += 1
            i -= 1
            j -= 1
            if(Debug):
                lines.append("OK\t" + r[i] + "\t" + h[j])
        elif(b[i][j] == OP_SUB):
            numSub += 1
            i -= 1
            j -= 1
            if(Debug):
                lines.append("OK\t" + r[i] + "\t" + h[j])
        elif(b[i][j] == OP_INS):
            numIns += 1
            j -= 1
            if(Debug):
                lines.append("INS\t" + "****" + "\t" + h[j])
        elif(b[i][j] == OP_DEL):
            numDel += 1
            i -= 1
            if(Debug):
                lines.append("DEL\t" + r[i] + "\t" + "****")
    if(Debug):
        lines = reversed(lines)
        for line in lines:
            print(line)
        print("#cor " + str(numCor))
        print("#sub " + str(numSub))
        print("#del " + str(numDel))
        print("#ins " + str(numIns))
    return round((numSub + numDel + numIns) / (float)(len(r)), 3)


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
        audiolog_path = paths.sub("audiolog")
        audiolog_db = os.path.join(audiolog_path, "audiolog.db")
        wavfile = ""
        rowID = ""
        first_rowID = ""
        prev_rowID = ""
        next_rowID = ""
        result = ""
        verified_transcription = ""
        post_data = ""
        reQS = re.compile("([^=]+)=([^&]*)&?")

        # gather parameters from GET
        if(environ["QUERY_STRING"]):
            for namevalue in reQS.findall(environ["QUERY_STRING"]):
                if(namevalue[0].lower() == "wavfile"):
                    wavfile = os.path.join(audiolog_path, namevalue[1])
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

        # Handle the request
        # serve a .wav file
        ErrorMessage = None
        if(len(wavfile) and os.path.isfile(wavfile)):
            start_response('200 OK', [('content-type', 'audio/wav')])
            with open(wavfile, "rb") as w:
                ret = [w.read()]
            return ret
        else:
            ret = []
            # Get the first unvalidated row from the database
            start_response(
                '200 OK',
                [('content-type', 'text/html;charset=utf-8')]
            )
            ret.append(
                '<html><head><title>{} STT Training</title>'.format(
                    keyword
                ).encode("utf-8")
            )
            conn = sqlite3.connect(audiolog_db)
            c = conn.cursor()
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
                        rowID = fetch_next_rowID(c, rowID)
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
<script language="javascript">
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
</script>""".encode("utf-8"))
                    ret.append('</head>\n<body>\n'.encode("utf-8"))

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
                            '<audio'
                            'controls="controls"'
                            'type="audio/wav"'
                            'style="width:100%%">'
                            '<source src="?wavfile={}" />'
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


port = 8080
print("Listening on port {}".format(str(port)))
server = wsgiref.simple_server.make_server(
    '',
    port,
    application,
    ThreadingWSGIServer
)
server.serve_forever()
