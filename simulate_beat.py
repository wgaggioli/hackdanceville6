import argparse
import time
import random

import redis

BODYPARTS = [
    'RIGHT_HIP',
    'TORSO',
    'HEAD',
    'RIGHT_SHOULDER',
    'LEFT_FOOT',
    'LEFT_HAND',
    'RIGHT_HAND',
    'RIGHT_FOOT',
    'LEFT_SHOULDER',
    'LEFT_ELBOW',
    'RIGHT_KNEE',
    'LEFT_KNEE',
    'NECK',
    'RIGHT_ELBOW',
    'LEFT_HIP'
]


class BeatSimulator(object):
    def __init__(self, init_bpm=60., avg_drift=0.5, drift_prob=.7,
                 channel='dance-beat', redis_host='localhost',
                 redis_port=6379):
        self.bpm = init_bpm
        self.avg_drift = avg_drift
        self.drift_prob = drift_prob
        self.redis = redis.StrictRedis(host=redis_host, port=redis_port)
        self.channel = channel

    def get_interval(self):
        if random.random() < self.drift_prob:
            drift = 2 * random.random() * self.avg_drift - self.avg_drift
            self.bpm += drift
        return 60. / self.bpm

    def get_msg(self):
        return {
            "timestamp": time.time(),
            "type": random.choice(BODYPARTS),
            "intensity": random.randint(1, 65536)
        }

    def run(self):
        while True:
            interval = self.get_interval()
            time.sleep(interval)
            msg = self.get_msg()
            self.redis.publish(self.channel, msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("beat simulation")
    parser.add_argument('--redis_host', default='localhost')
    parser.add_argument('--channel', default='dance-beat')
    args = parser.parse_args()
    simulator = BeatSimulator(redis_host=args.redis_host, channel=args.channel)
    simulator.run()

