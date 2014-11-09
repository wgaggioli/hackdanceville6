"""
Install pyaudio here: http://people.csail.mit.edu/hubert/pyaudio/

"""
import sys
import argparse

import pyaudio
import wave
import subprocess

from subscriber import Subscriber


CHUNK = 1024
if sys.platform == 'darwin':
    PLAY_COMMAND = 'afplay'
elif sys.platform == 'win32':
    sys.stderr.write("UH OH! we need a real command for this...\n")
    PLAY_COMMAND = 'open'
else:
    PLAY_COMMAND = 'aplay'


class Bumper(Subscriber):
    """Simple object that listens to beat output and hits the bass, yo"""
    def __init__(self, bass_path, channels=None, **kwargs):
        # pubsub connection
        if channels is None:
            channels = ['dance-beat']
        super(Bumper, self).__init__(channels, **kwargs)
        
        self.bass_path = bass_path

    def on_subscribe(self):
        return
        self.fp = wave.open(self.bass_path, 'rb')
        self.audio = pyaudio.PyAudio()
        self.audio_stream = self.audio.open(
            format=self.audio.get_format_from_width(self.fp.getsampwidth()),
            channels=self.fp.getnchannels(),
            rate=self.fp.getframerate(),
            output=True
        )

    def on_close(self):
        return
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.audio.terminate()
        self.fp.close()

    def on_event(self, beat):
        subprocess.Popen(['afplay', self.bass_path])
        return
        data = self.fp.readframes(CHUNK)
        while data:
            self.audio_stream.write(data)
            data = self.fp.readframes(CHUNK)
        self.fp.rewind()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Subscribes to pubsub and outputs a bass bump")
    parser.add_argument('--bass_file', default='bass.wav')
    parser.add_argument('--redis_host', default='localhost')
    args = parser.parse_args()
    bumper = Bumper(args.bass_file, redis_host=args.redis_host)
    bumper.subscribe()