import json
import time
import wave

import pyaudio
import redis

from sound_master import SongPlayer


redis = redis.Redis()


def rate_adjust():
    rate = 1.
    while rate:
        rate = raw_input('New rate >> ')
        if rate:
            rate = float(rate)
            data = {"rateAdjustFactor": rate}
            redis.publish('song-adjust', json.dumps(data))


def offset_madness():
    offset = 1
    while offset:
        offset = raw_input("Add offset (ms) >> ")
        if offset:
            offset = float(offset)
            data = {"offsetInMillis": offset}
            redis.publish('song-adjust', json.dumps(data))


offset_madness()