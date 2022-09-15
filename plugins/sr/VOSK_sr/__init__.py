# -*- coding: utf-8 -*-
import numpy as np
import os
import pandas as pd
import sqlite3
import wave
from naomi import paths
from naomi import plugin
from vosk import Model, KaldiRecognizer, SpkModel


def cosine_dist(x, y):
    nx = np.array(x)
    ny = np.array(y)
    return 1 - np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)


class VOSK_sr(plugin.SRPlugin):
    def __init__(self):
        self._audiolog_dir = paths.sub("audiolog")
        self._audiolog_db = os.path.join(audiolog_dir, 'audiolog.db')
        # Default place to put models
        binarydir_path = paths.sub('VOSK')
        if not os.path.isdir(binarydir_path):
            os.makedirs(binarydir_path)
        # Download the lite ASR model
        asr_model = os.path.join(binarydir_path,'vosk-model-small-en-us-0.15')
        if not os.path.isdir(asr_model):
            binary_url = 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip'
            print("Downloading small model from {}".format(binary_url))
            cmd = [
                'wget',
                binary_url,
                '--directory-prefix={}'.format(binarydir_path),
                '--output-document={}'.format(os.path.join(binarydir_path, 'vosk-model-small-en-us-0.15.zip'))
            ]
            print(" ".join(cmd))
            completed_process = run_command(cmd, 2)
            if(completed_process.returncode == 0):
                # unzip the archive into the binarydir_path directory
                cmd = [
                    'unzip',
                    '-d', binarydir_path,
                    os.path.join(binarydir_path, 'vosk-model-small-en-us-0.15.zip')
                ]
                completed_process = run_command(cmd, 2)
                if(completed_process.returncode != 0):
                    print(completed_process.stderr.decode("UTF-8"))
        # Download the SR model
        sr_model = os.path.join(paths.sub('VOSK'),'vosk-model-spk-0.4')
        if not os.path.isdir(sr_model):
            binary_url = 'https://alphacephei.com/vosk/models/vosk-model-spk-0.4.zip'
            print("Downloading speaker recognition model from {}".format(binary_url))
            cmd = [
                'wget',
                binary_url,
                '--directory-prefix={}'.format(binarydir_path),
                '--output-document={}'.format(os.path.join(binarydir_path, 'vosk-model-spk-0.4.zip'))
            ]
            print(" ".join(cmd))
            completed_process = run_command(cmd, 2)
            if(completed_process.returncode == 0):
                # unzip the archive into the binarydir_path directory
                cmd = [
                    'unzip',
                    '-d', binarydir_path,
                    os.path.join(binarydir_path, 'vosk-model-spk-0.4.zip')
                ]
                completed_process = run_command(cmd, 2)
                if(completed_process.returncode != 0):
                    print(completed_process.stderr.decode("UTF-8"))
        self._rec = KaldiRecognizer(model, wf.getframerate())
        self._rec.SetSpkModel(spk_model)

        with sqlite3.connect(self._audiolog_db) as conn:
            cur = conn.cursor()
            cur_speakers = conn.cursor()
            cur_sig = conn.cursor()
            # Create the vosk_speakersig table if it does not already exist
            cur.execute('create table if not exists vosk_speakersig(filename text primary key,speaker text,sig1 real,sig2 real,sig3 real,sig4 real,sig5 real,sig6 real,sig7 real,sig8 real,sig9 real,sig10 real,sig11 real,sig12 real,sig13 real,sig14 real,sig15 real,sig16 real,sig17 real,sig18 real,sig19 real,sig20 real,sig21 real, sig22 real,sig23 real,sig24 real,sig25 real,sig26 real,sig27 real,sig28 real,sig29 real,sig30 real,sig31 real,sig32 real,sig33 real,sig34 real,sig35 real,sig36 real,sig37 real,sig38 real,sig39 real,sig40 real,sig41 real,sig42 real,sig43 real,sig44 real,sig45 real,sig46 real,sig47 real,sig48 real,sig49 real,sig50 real,sig51 real,sig52 real,sig53 real,sig54 real,sig55 real,sig56 real,sig57 real,sig58 real,sig59 real,sig60 real,sig61 real,sig62 real,sig63 real,sig64 real,sig65 real,sig66 real,sig67 real,sig68 real,sig69 real,sig70 real,sig71 real,sig72 real,sig73 real,sig74 real,sig75 real,sig76 real,sig77 real,sig78 real,sig79 real,sig80 real,sig81 real,sig82 real,sig83 real,sig84 real,sig85 real,sig86 real,sig87 real,sig88 real,sig89 real,sig90 real,sig91 real,sig92 real,sig93 real,sig94 real,sig95 real,sig96 real,sig97 real,sig98 real,sig99 real,sig100 real,sig101 real,sig102 real,sig103 real,sig104 real,sig105 real,sig106 real,sig107 real,sig108 real,sig109 real,sig110 real,sig111 real,sig112 real,sig113 real,sig114 real,sig115 real,sig116 real,sig117 real,sig118 real,sig119 real,sig120 real,sig121 real,sig122 real,sig123 real,sig124 real,sig125 real,sig126 real,sig127 real,sig128 real)')
            # Any entries in audiolog with speakers but not a corresponding row
            # in vosk_speakersig should be processed and added now
            cur.execute("select distinct filename,speaker from audiolog left join vosk_speakersig on audiolog.filename = vosk_speakersig.filename where audiolog.reviewed>'' and speaker>'' and vosk_speakersig.filename is null")
            self.insert_speakersig = "insert into vosk_speakersig(filename,speaker,sig1,sig2,sig3,sig4,sig5,sig6,sig7,sig8,sig9,sig10,sig11,sig12,sig13,sig14,sig15,sig16,sig17,sig18,sig19,sig20,sig21,sig22,sig23,sig24,sig25,sig26,sig27,sig28,sig29,sig30,sig31,sig32,sig33,sig34,sig35,sig36,sig37,sig38,sig39,sig40,sig41,sig42,sig43,sig44,sig45,sig46,sig47,sig48,sig49,sig50,sig51,sig52,sig53,sig54,sig55,sig56,sig57,sig58,sig59,sig60,sig61,sig62,sig63,sig64,sig65,sig66,sig67,sig68,sig69,sig70,sig71,sig72,sig73,sig74,sig75,sig76,sig77,sig78,sig79,sig80,sig81,sig82,sig83,sig84,sig85,sig86,sig87,sig88,sig89,sig90,sig91,sig92,sig93,sig94,sig95,sig96,sig97,sig98,sig99,sig100,sig101,sig102,sig103,sig104,sig105,sig106,sig107,sig108,sig109,sig110,sig111,sig112,sig113,sig114,sig115,sig116,sig117,sig118,sig119,sig120,sig121,sig122,sig123,sig124,sig125,sig126,sig127,sig128)values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            for row in cur:
                with wave.open(os.path.join(audiolog_dir,row['filename']), "rb") as wf:
                    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                        print ("Audio file must be WAV format mono PCM.")
                        exit (1)
                    data = wf.readframes(wf.getnframes())
                    if len(data) == 0:
                        print("len(data)=0")
                    else:
                        self.rec.AcceptWaveform(data)
                        res = json.loads(self.rec.Result())
                        if 'spk' in res:
                            cur.execute(self.insert_speakersig, [
                                row['filename'],
                                row['speaker'],
                                res['spk'][0],
                                res['spk'][1],
                                res['spk'][2],
                                res['spk'][3],
                                res['spk'][4],
                                res['spk'][5],
                                res['spk'][6],
                                res['spk'][7],
                                res['spk'][8],
                                res['spk'][9],
                                res['spk'][10],
                                res['spk'][11],
                                res['spk'][12],
                                res['spk'][13],
                                res['spk'][14],
                                res['spk'][15],
                                res['spk'][16],
                                res['spk'][17],
                                res['spk'][18],
                                res['spk'][19],
                                res['spk'][20],
                                res['spk'][21],
                                res['spk'][22],
                                res['spk'][23],
                                res['spk'][24],
                                res['spk'][25],
                                res['spk'][26],
                                res['spk'][27],
                                res['spk'][28],
                                res['spk'][29],
                                res['spk'][30],
                                res['spk'][31],
                                res['spk'][32],
                                res['spk'][33],
                                res['spk'][34],
                                res['spk'][35],
                                res['spk'][36],
                                res['spk'][37],
                                res['spk'][38],
                                res['spk'][39],
                                res['spk'][40],
                                res['spk'][41],
                                res['spk'][42],
                                res['spk'][43],
                                res['spk'][44],
                                res['spk'][45],
                                res['spk'][46],
                                res['spk'][47],
                                res['spk'][48],
                                res['spk'][49],
                                res['spk'][50],
                                res['spk'][51],
                                res['spk'][52],
                                res['spk'][53],
                                res['spk'][54],
                                res['spk'][55],
                                res['spk'][56],
                                res['spk'][57],
                                res['spk'][58],
                                res['spk'][59],
                                res['spk'][60],
                                res['spk'][61],
                                res['spk'][62],
                                res['spk'][63],
                                res['spk'][64],
                                res['spk'][65],
                                res['spk'][66],
                                res['spk'][67],
                                res['spk'][68],
                                res['spk'][69],
                                res['spk'][70],
                                res['spk'][71],
                                res['spk'][72],
                                res['spk'][73],
                                res['spk'][74],
                                res['spk'][75],
                                res['spk'][76],
                                res['spk'][77],
                                res['spk'][78],
                                res['spk'][79],
                                res['spk'][80],
                                res['spk'][81],
                                res['spk'][82],
                                res['spk'][83],
                                res['spk'][84],
                                res['spk'][85],
                                res['spk'][86],
                                res['spk'][87],
                                res['spk'][88],
                                res['spk'][89],
                                res['spk'][90],
                                res['spk'][91],
                                res['spk'][92],
                                res['spk'][93],
                                res['spk'][94],
                                res['spk'][95],
                                res['spk'][96],
                                res['spk'][97],
                                res['spk'][98],
                                res['spk'][99],
                                res['spk'][100],
                                res['spk'][101],
                                res['spk'][102],
                                res['spk'][103],
                                res['spk'][104],
                                res['spk'][105],
                                res['spk'][106],
                                res['spk'][107],
                                res['spk'][108],
                                res['spk'][109],
                                res['spk'][110],
                                res['spk'][111],
                                res['spk'][112],
                                res['spk'][113],
                                res['spk'][114],
                                res['spk'][115],
                                res['spk'][116],
                                res['spk'][117],
                                res['spk'][118],
                                res['spk'][119],
                                res['spk'][120],
                                res['spk'][121],
                                res['spk'][122],
                                res['spk'][123],
                                res['spk'][124],
                                res['spk'][125],
                                res['spk'][126],
                                res['spk'][127]
                            ])
            # Get the speakers and weights
            self.speakers = {}
            cur_speakers.execute('select distinct speaker from vosk_speakersig')
            for speaker_row in cur_speakers:
                # get the average of all values associated with this speaker, including this one
                cur_sig.execute('select avg(sig1) as avg_sig1,avg(sig2) as avg_sig2,avg(sig3) as avg_sig3,avg(sig4) as avg_sig4,avg(sig5) as avg_sig5,avg(sig6) as avg_sig6,avg(sig7) as avg_sig7,avg(sig8) as avg_sig8,avg(sig9) as avg_sig9,avg(sig10) as avg_sig10,avg(sig11) as avg_sig11,avg(sig12) as avg_sig12,avg(sig13) as avg_sig13,avg(sig14) as avg_sig14,avg(sig15) as avg_sig15,avg(sig16) as avg_sig16,avg(sig17) as avg_sig17,avg(sig18) as avg_sig18,avg(sig19) as avg_sig19,avg(sig20) as avg_sig20,avg(sig21) as avg_sig21,avg(sig22) as avg_sig22,avg(sig23) as avg_sig23,avg(sig24) as avg_sig24,avg(sig25) as avg_sig25,avg(sig26) as avg_sig26,avg(sig27) as avg_sig27,avg(sig28) as avg_sig28,avg(sig29) as avg_sig29,avg(sig30) as avg_sig30,avg(sig31) as avg_sig31,avg(sig32) as avg_sig32,avg(sig33) as avg_sig33,avg(sig34) as avg_sig34,avg(sig35) as avg_sig35,avg(sig36) as avg_sig36,avg(sig37) as avg_sig37,avg(sig38) as avg_sig38,avg(sig39) as avg_sig39,avg(sig40) as avg_sig40,avg(sig41) as avg_sig41,avg(sig42) as avg_sig42,avg(sig43) as avg_sig43,avg(sig44) as avg_sig44,avg(sig45) as avg_sig45,avg(sig46) as avg_sig46,avg(sig47) as avg_sig47,avg(sig48) as avg_sig48,avg(sig49) as avg_sig49,avg(sig50) as avg_sig50,avg(sig51) as avg_sig51,avg(sig52) as avg_sig52,avg(sig53) as avg_sig53,avg(sig54) as avg_sig54,avg(sig55) as avg_sig55,avg(sig56) as avg_sig56,avg(sig57) as avg_sig57,avg(sig58) as avg_sig58,avg(sig59) as avg_sig59,avg(sig60) as avg_sig60,avg(sig61) as avg_sig61,avg(sig62) as avg_sig62,avg(sig63) as avg_sig63,avg(sig64) as avg_sig64,avg(sig65) as avg_sig65,avg(sig66) as avg_sig66,avg(sig67) as avg_sig67,avg(sig68) as avg_sig68,avg(sig69) as avg_sig69,avg(sig70) as avg_sig70,avg(sig71) as avg_sig71,avg(sig72) as avg_sig72,avg(sig73) as avg_sig73,avg(sig74) as avg_sig74,avg(sig75) as avg_sig75,avg(sig76) as avg_sig76,avg(sig77) as avg_sig77,avg(sig78) as avg_sig78,avg(sig79) as avg_sig79,avg(sig80) as avg_sig80,avg(sig81) as avg_sig81,avg(sig82) as avg_sig82,avg(sig83) as avg_sig83,avg(sig84) as avg_sig84,avg(sig85) as avg_sig85,avg(sig86) as avg_sig86,avg(sig87) as avg_sig87,avg(sig88) as avg_sig88,avg(sig89) as avg_sig89,avg(sig90) as avg_sig90,avg(sig91) as avg_sig91,avg(sig92) as avg_sig92,avg(sig93) as avg_sig93,avg(sig94) as avg_sig94,avg(sig95) as avg_sig95,avg(sig96) as avg_sig96,avg(sig97) as avg_sig97,avg(sig98) as avg_sig98,avg(sig99) as avg_sig99,avg(sig100) as avg_sig100,avg(sig101) as avg_sig101,avg(sig102) as avg_sig102,avg(sig103) as avg_sig103,avg(sig104) as avg_sig104,avg(sig105) as avg_sig105,avg(sig106) as avg_sig106,avg(sig107) as avg_sig107,avg(sig108) as avg_sig108,avg(sig109) as avg_sig109,avg(sig110) as avg_sig110,avg(sig111) as avg_sig111,avg(sig112) as avg_sig112,avg(sig113) as avg_sig113,avg(sig114) as avg_sig114,avg(sig115) as avg_sig115,avg(sig116) as avg_sig116,avg(sig117) as avg_sig117,avg(sig118) as avg_sig118,avg(sig119) as avg_sig119,avg(sig120) as avg_sig120,avg(sig121) as avg_sig121,avg(sig122) as avg_sig122,avg(sig123) as avg_sig123,avg(sig124) as avg_sig124,avg(sig125) as avg_sig125,avg(sig126) as avg_sig126,avg(sig127) as avg_sig127,avg(sig128) as avg_sig128 from vosk_speakersig where speaker=? group by speaker',[speaker])
                # Only one row should be returned
                for sig in cur_sig:
                    sig_avg=[row2[0],row2[1],row2[2],row2[3],row2[4],row2[5],row2[6],row2[7],row2[8],row2[9],row2[10],row2[11],row2[12],row2[13],row2[14],row2[15],row2[16],row2[17],row2[18],row2[19],row2[20],row2[21],row2[22],row2[23],row2[24],row2[25],row2[26],row2[27],row2[28],row2[29],row2[30],row2[31],row2[32],row2[33],row2[34],row2[35],row2[36],row2[37],row2[38],row2[39],row2[40],row2[41],row2[42],row2[43],row2[44],row2[45],row2[46],row2[47],row2[48],row2[49],row2[50],row2[51],row2[52],row2[53],row2[54],row2[55],row2[56],row2[57],row2[58],row2[59],row2[60],row2[61],row2[62],row2[63],row2[64],row2[65],row2[66],row2[67],row2[68],row2[69],row2[70],row2[71],row2[72],row2[73],row2[74],row2[75],row2[76],row2[77],row2[78],row2[79],row2[80],row2[81],row2[82],row2[83],row2[84],row2[85],row2[86],row2[87],row2[88],row2[89],row2[90],row2[91],row2[92],row2[93],row2[94],row2[95],row2[96],row2[97],row2[98],row2[99],row2[100],row2[101],row2[102],row2[103],row2[104],row2[105],row2[106],row2[107],row2[108],row2[109],row2[110],row2[111],row2[112],row2[113],row2[114],row2[115],row2[116],row2[117],row2[118],row2[119],row2[120],row2[121],row2[122],row2[123],row2[124],row2[125],row2[126],row2[127]]
                    self.speakers[speaker_row[0]] = sig_avg
        print(f"I know the following speakers: {[speaker for speaker in self.speakers]}")

    # Takes the name of the file containing the audio to be identified
    # Returns the name of the speaker, the cosine distance, and the STT transcription
    # In my experience, a cosine distance of less than 30 is a match and over
    # 30 should be verified.
    def recognize_speaker(self, filename):
        with wave.open(os.path.join(audiolog_dir, filename), "rb") as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                print ("Audio file must be WAV format mono PCM.")
                exit (1)
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetSpkModel(spk_model)
            data = wf.readframes(wf.getnframes())
            if len(data) == 0:
                print("len(data)=0")
                break
        self.rec.AcceptWaveform(data)
        res = json.loads(self.rec.Result())
        print(f"Text: {res['text']}")
        # Figure out the speaker (minimum cosine distance)
        result = {'min_cos_dist': None, 'speaker': None}
        if 'spk' in res:
            for speaker in self.speakers:
                cur_cos_dist = cos_dist(self.speakers[speaker], res['spk'])
                if result['min_cos_dist'] is None or result['min_cos_dist'] < cur_cos_dist:
                    result['min_cos_dist'] = cur_cos_dist
                    result['speaker'] = speaker
            cur.execute(self.insert_speakersig, [
                filename,
                result['speaker'],
                res['spk'][0],
                res['spk'][1],
                res['spk'][2],
                res['spk'][3],
                res['spk'][4],
                res['spk'][5],
                res['spk'][6],
                res['spk'][7],
                res['spk'][8],
                res['spk'][9],
                res['spk'][10],
                res['spk'][11],
                res['spk'][12],
                res['spk'][13],
                res['spk'][14],
                res['spk'][15],
                res['spk'][16],
                res['spk'][17],
                res['spk'][18],
                res['spk'][19],
                res['spk'][20],
                res['spk'][21],
                res['spk'][22],
                res['spk'][23],
                res['spk'][24],
                res['spk'][25],
                res['spk'][26],
                res['spk'][27],
                res['spk'][28],
                res['spk'][29],
                res['spk'][30],
                res['spk'][31],
                res['spk'][32],
                res['spk'][33],
                res['spk'][34],
                res['spk'][35],
                res['spk'][36],
                res['spk'][37],
                res['spk'][38],
                res['spk'][39],
                res['spk'][40],
                res['spk'][41],
                res['spk'][42],
                res['spk'][43],
                res['spk'][44],
                res['spk'][45],
                res['spk'][46],
                res['spk'][47],
                res['spk'][48],
                res['spk'][49],
                res['spk'][50],
                res['spk'][51],
                res['spk'][52],
                res['spk'][53],
                res['spk'][54],
                res['spk'][55],
                res['spk'][56],
                res['spk'][57],
                res['spk'][58],
                res['spk'][59],
                res['spk'][60],
                res['spk'][61],
                res['spk'][62],
                res['spk'][63],
                res['spk'][64],
                res['spk'][65],
                res['spk'][66],
                res['spk'][67],
                res['spk'][68],
                res['spk'][69],
                res['spk'][70],
                res['spk'][71],
                res['spk'][72],
                res['spk'][73],
                res['spk'][74],
                res['spk'][75],
                res['spk'][76],
                res['spk'][77],
                res['spk'][78],
                res['spk'][79],
                res['spk'][80],
                res['spk'][81],
                res['spk'][82],
                res['spk'][83],
                res['spk'][84],
                res['spk'][85],
                res['spk'][86],
                res['spk'][87],
                res['spk'][88],
                res['spk'][89],
                res['spk'][90],
                res['spk'][91],
                res['spk'][92],
                res['spk'][93],
                res['spk'][94],
                res['spk'][95],
                res['spk'][96],
                res['spk'][97],
                res['spk'][98],
                res['spk'][99],
                res['spk'][100],
                res['spk'][101],
                res['spk'][102],
                res['spk'][103],
                res['spk'][104],
                res['spk'][105],
                res['spk'][106],
                res['spk'][107],
                res['spk'][108],
                res['spk'][109],
                res['spk'][110],
                res['spk'][111],
                res['spk'][112],
                res['spk'][113],
                res['spk'][114],
                res['spk'][115],
                res['spk'][116],
                res['spk'][117],
                res['spk'][118],
                res['spk'][119],
                res['spk'][120],
                res['spk'][121],
                res['spk'][122],
                res['spk'][123],
                res['spk'][124],
                res['spk'][125],
                res['spk'][126],
                res['spk'][127]
            ])
        return {
            'speaker': result['speaker'],
            'confidence': result['min_cos_dist'],
            'utterance': res['text']
        }
