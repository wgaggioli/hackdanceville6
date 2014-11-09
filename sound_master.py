#!/usr/bin/env python
import json
import time
import argparse
import os
import wave
import threading

import pyaudio
import librosa
import redis

from subscriber import Subscriber

NFRAMES_BUFFER = 1024


class BeatAnalyzer(object):
    """
    Analyzes a song for beat information

    """

    def __init__(self, song_file, cache_file='.bpm_cache.json'):
        self.song_file = song_file
        self.cache_file = cache_file
        if cache_file and os.path.exists(cache_file):
            with open(cache_file) as fp:
                self.cache = json.load(fp)
        else:
            self.cache = {}

    def write_cache(self):
        if self.cache_file:
            with open(self.cache_file, 'w') as fp:
                json.dump(self.cache, fp)

    def get_waveform(self):
        y, sr = librosa.load(self.song_file)
        return y

    def get_audio_bpm(self):
        if self.song_file in self.cache:
            data = self.cache[self.song_file]
            tempo, beat_frames = data['tempo'], data['beat_frames']
        else:
            tempo, beat_frames = librosa.beat.beat_track(
                y=self.get_waveform(), hop_length=64)
            beat_frames = list(beat_frames)
            self.cache[self.song_file] = {
                "tempo": tempo,
                "beat_frames": beat_frames
            }
            self.write_cache()
        return tempo, list(beat_frames)

    # def manip_audio(self, payload):
    #     delta = 0.5  # BS var
    #     af = 'bass.wav'  # BS var
    #     for wav in self.wavedict:
    #         y = self.wavedict[wav]
    #         new_wav = librosa.effects.time_stretch(y, delta)
    #         librosa.output.write_wav('new_wav.wav', y, 22050)
    #         # TODO: how to get this to play?


class SongThread(threading.Thread):
    def __init__(self, audio_stream, fp):
        self.audio_stream = audio_stream
        self.fp = fp
        self.do_run = True
        threading.Thread.__init__(self)

    def run(self):
        while self.do_run:
            data = self.fp.readframes(NFRAMES_BUFFER)
            if not data:
                self.fp.rewind()
                data = self.fp.readframes(NFRAMES_BUFFER)
            t = NFRAMES_BUFFER / float(self.audio_stream._rate)
            self.audio_stream.write(data)
            time.sleep(t - .003)

    def stop(self):
        self.do_run = False
        self.join(1)


class SongPlayer(Subscriber):
    def __init__(self, song_file, channels=None, **kwargs):
        if channels is None:
            channels = ['song-adjust']
        super(SongPlayer, self).__init__(channels, **kwargs)
        self.song_file = song_file
        self.rate = None

    def on_subscribe(self):
        # load the song and start to play
        self.fp = wave.open(self.song_file, 'rb')
        self.audio = pyaudio.PyAudio()
        self.rate = self.fp.getframerate()
        self.audio_stream = self.audio.open(
            format=self.audio.get_format_from_width(self.fp.getsampwidth()),
            channels=self.fp.getnchannels(),
            rate=self.rate,
            output=True
        )
        self.song_thread = SongThread(self.audio_stream, self.fp)
        self.song_thread.start()

    def on_close(self):
        self.song_thread.stop()
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.audio.terminate()
        self.fp.close()

    def adjust_rate(self, factor):
        self.rate = int(self.rate * factor)
        self.audio_stream = self.audio.open(
            format=self.audio.get_format_from_width(self.fp.getsampwidth()),
            channels=self.fp.getnchannels(),
            rate=self.rate,
            output=True
        )
        self.song_thread.audio_stream = self.audio_stream

    def add_offset(self, offset_in_ms):
        offset = int(offset_in_ms / 1000. * self.rate)
        new_pos = (self.fp.tell() + offset) % self.fp.getnframes()
        self.fp.setpos(new_pos)

    def on_event(self, item):
        # adjust the song
        print item
        if item['type'] == 'message':
            data = json.loads(item['data'])
            if 'offsetInMillis' in data:
                self.add_offset(data['offsetInMillis'])
                print 'Adding offset of {}'.format(data['offsetInMillis'])
            if 'rateAdjustFactor' in data:
                self.adjust_rate(data['rateAdjustFactor'])
                print 'Adjusting rate by {}'.format(data['rateAdjustFactor'])
                self.audio_stream._rate = self.rate


class SongMaster(object):
    def __init__(self, song_file, redis_host='localhost',
                 channel='song-analysis'):
        # publish nonsense
        self.channel = channel
        self.redis = redis.Redis(host=redis_host)

        # init player
        self.player = SongPlayer(song_file, redis_host=redis_host)

        # analyze and publish beat analysis
        self.beater = BeatAnalyzer(song_file)

    def play(self):
        print 'getting bpmz'
        tempo, beat_frames = self.beater.get_audio_bpm()
        print 'publishing that shit'
        self.publish_beat_info(tempo, beat_frames)

        # play that shit
        print 'playing that shit'
        self.play_song()

    def publish_beat_info(self, tempo, beat_frames):
        self.redis.publish(self.channel, {
            "title": "FUCKYEAH",
            "tempo": tempo,
            "initialLength": len(beat_frames),
            "startTimestamp": time.time(),
            "beatFrames": beat_frames
        })

    def play_song(self):
        self.player.subscribe()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Analyze, play, and live-manipulate an inputted song")
    parser.add_argument('--song_file', default='bass.wav')
    parser.add_argument('--redis_host', default='localhost')
    args = parser.parse_args()

    songmaster = SongMaster(args.song_file, redis_host=args.redis_host)
    songmaster.play()

