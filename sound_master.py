#!/usr/bin/env python

import librosa
import json
#import time
#import sys
#import redis


class SoundMaster(object):

    def __init__(self, audio_files=None):
        if audio_files is None:
            self.audio_files = ['bass.wav']
        else:
            self.audio_files = audio_files
        
    def get_audio_bpm(self):
        afdict = {}
        for af in self.audio_files:
            y, sr = librosa.load(af)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=64)
            #print(tempo)
            #print(beat_frames)
            afdict[af] = (tempo, list(beat_frames))
        return json.dumps(afdict)

if __name__ == '__main__':
    sm = SoundMaster()
    print(sm.get_audio_bpm())

