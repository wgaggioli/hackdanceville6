"""
Install pyaudio here: http://people.csail.mit.edu/hubert/pyaudio/

"""
import argparse

import pyaudio
import wave

from subscriber import Subscriber

CHUNK = 1024


class Bumper(Subscriber):
    """Simple object that listens to beat output and hits the bass, yo"""
    def __init__(self, bass_path, channels=None, **kwargs):
        # pubsub connection
        if channels is None:
            channels = ['dance-beat']
        super(Bumper, self).__init__(channels, **kwargs)

        # audio player
        self.bass_path = bass_path

    def on_subscribe(self):
        self.fp = wave.open(self.bass_path, 'rb')
        self.audio = pyaudio.PyAudio()

    def on_close(self):
        self.audio.terminate()
        self.fp.close()

    def on_event(self, beat):
        data = self.fp.readframes(CHUNK)
        self.audio_stream = self.audio.open(
            format=self.audio.get_format_from_width(self.fp.getsampwidth()),
            channels=self.fp.getnchannels(),
            rate=self.fp.getframerate(),
            output=True
        )
        while data:
            self.audio_stream.write(data)
            data = self.fp.readframes(CHUNK)
        self.fp.rewind()
        self.audio_stream.stop_stream()
        self.audio_stream.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Subscribes to pubsub and outputs a bass bump")
    parser.add_argument('--bass_file', default='bass.wav')
    parser.add_argument('--redis_host', default='localhost')
    args = parser.parse_args()
    bumper = Bumper(args.bass_file, redis_host=args.redis_host)
    bumper.subscribe()