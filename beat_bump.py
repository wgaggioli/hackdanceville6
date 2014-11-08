"""
Install pyaudio here: http://people.csail.mit.edu/hubert/pyaudio/

"""

import argparse
import redis
import pyaudio
import wave

CHUNK = 1024


class Bumper(object):
    """Simple object that listens to beat output and hits the bass, yo"""
    def __init__(self, bass_path, redis_host='localhost', redis_port=6379,
                 channels=None):
        # pubsub connection
        if channels is None:
            channels = ['dance-beat']
        self.channels = channels
        client = redis.StrictRedis(host=redis_host, port=redis_port)
        self.pubsub = client.pubsub()

        # audio player
        self.bass_path = bass_path
        self.open_audio_stream()

    def open_audio_stream(self):
        self.fp = wave.open(self.bass_path, 'rb')
        self.audio = pyaudio.PyAudio()
        self.audio_stream = self.audio.open(
            format=self.audio.get_format_from_width(self.fp.getsampwidth()),
            channels=self.fp.getnchannels(),
            rate=self.fp.getframerate(),
            output=True
        )

    def close_audio_stream(self):
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.audio.terminate()
        self.fp.close()

    def subscribe(self):
        self.open_audio_stream()
        self.pubsub.subscribe(self.channels)
        for beat in self.pubsub.listen():
            self.play_beat()
        self.close_audio_stream()

    def play_beat(self):
        data = self.fp.readframes(CHUNK)
        while data:
            self.audio_stream.write(data)
            data = self.fp.readframes(CHUNK)
        self.fp.rewind()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Subscribes to pubsub and outputs a bass bump")
    parser.add_argument('--bass_file', default='bass.wav')
    args = parser.parse_args()
    bumper = Bumper(args.bass_file)
    bumper.subscribe()