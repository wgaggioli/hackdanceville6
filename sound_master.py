#!/usr/bin/env python

import librosa
import json
import time
import redis


class SoundMaster(object):

    def __init__(self, audio_files=None):
        if audio_files is None:
            self.audio_files = ['bass.wav']
        else:
            self.audio_files = audio_files
        try:
            wavedict_file = open('waveforms.json', 'r')
            self.wavedict = json.load(wavedict_file)
            wavedict_file.close()
        except:
            self.wavedict = self.get_waveforms()
        try:
            anal_file = open('bpmAnalysis.json', 'r')
            self.bpm_analysis = json.load(anal_file)
            anal_file.close()
        except:
            print('in init except')
            self.bpm_analysis = self.get_audio_bpm()

    def get_waveforms(self):
        wavedict = {}
        for af in self.audio_files:
            y, sr = librosa.load(af)
            wavedict[af] = y
        # wavedict_file = open('waveforms.json', 'w')
        # json.dump(wavedict, wavedict_file)
        # wavedict_file.close()
        #print(wavedict)
        return wavedict

    def get_audio_bpm(self):
        bpmdict = {}
        for wave in self.wavedict:
            tempo, beat_frames = librosa.beat.beat_track(\
                y=self.wavedict[wave], hop_length=64)
            #print(tempo)
            #print(beat_frames)
            bpmdict[wave] = (tempo, list(beat_frames))
        anal_file = open('bpmAnalysis.json', 'w')
        json.dump(bpmdict, anal_file)
        anal_file.close()
        #print(bpmdict)
        return bpmdict

    def manip_audio(self, payload):
        delta = 0.5  # BS var
        af = 'bass.wav'  # BS var
        for wav in self.wavedict:
            y = self.wavedict[wav]
            new_wav = librosa.effects.time_stretch(y, delta)
            librosa.output.write_wav('new_wav.wav', y, 22050)
            # TODO: how to get this to play?

    def run(self):
        r = redis.StrictRedis(host='172.31.253.53', port=6379, db=0)
        while True:
            ps = r.pubsub()
            ps.subscribe('dance-beat')  # TODO: change channel
            l = ps.listen()
            for msg in l:
                if msg['type'] == 'message':
                    payload = json.loads(msg['data'])
                    self.manip_audio(payload)

if __name__ == '__main__':
    sm = SoundMaster()
    print(sm.wavedict)
    print(sm.get_audio_bpm())
    #sm.run()


