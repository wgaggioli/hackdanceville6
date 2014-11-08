#!/usr/bin/env python

import librosa
import json
#import time
#import sys
#import redis
#import song_loader


def getAudioBPM():
    #audio_files = song_loader.getAudioFiles()
    audio_files = ['bass.wav']
    afDict = {}
    for af in audio_files:
        y, sr = librosa.load(af)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=64)
        #print(tempo)
        #print(beat_frames)
        afDict[af] = (tempo, list(beat_frames))
    return json.dumps(afDict)

if __name__ == '__main__':
    print(getAudioBPM())

