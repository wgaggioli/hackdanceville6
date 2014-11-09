import json
import time
import wave

import pyaudio
import redis

from sound_master import SongPlayer


redis = redis.Redis()
rate = 1.
while rate:
    rate = raw_input('New rate >> ')
    if rate:
        rate = float(rate)
        data = {"rate_adjust": rate}
        redis.publish('song-adjust', json.dumps(data))