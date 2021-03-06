import numpy
from numpy import linalg
import json
from operator import itemgetter
import time


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
PART_WEIGHT_MULTIPLIERS = {
    'head': 100,
    'left_elbow': 1,
    'left_foot': 1,
    'left_hand': 1,
    'left_hip': 1,
    'left_knee': 1,
    'left_shoulder': 1,
    'neck': 1,
    'right_elbow': 1,
    'right_foot': 1,
    'right_hand': 1,
    'right_hip': 1,
    'right_knee': 1,
    'right_shoulder': 1,
    'torso': 1
}
BODYPARTS_LOWER = [s.lower() for s in BODYPARTS]
CACHE_FRAMES = 4
VELOCITY_DELTA_CUTOFF = 1.15
MAGNITUDE_SUM_CUTOFF = 1
MINIMUM_BEAT_OFFSET = 250
ACTIVE_POINTS_FOR_BEAT = 4


def get_vector_delta(a,b):
    cosang = numpy.dot(a,b)
    sinang = linalg.norm(numpy.cross(a,b))
    return numpy.arctan2(sinang, cosang)

def ms_to_seconds(t):
    return t / 1000.0

def seconds_to_ms(t):
    return t * 1000


class DanceInterpreter(object):

    def __init__(self, redis=None, listen_channel=None):
        self.redis = redis
        self.listen_channel = listen_channel
        self.timestamps = []
        self.positions = {k:[] for k in BODYPARTS_LOWER}
        self.velocities = {k:[] for k in BODYPARTS_LOWER}
        self.velocity_deltas = {k:[] for k in BODYPARTS_LOWER}
        self.last_beat_timestamp = 0

    def run(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(self.listen_channel)
        while True:
            listener = pubsub.listen()
            for message in listener:
                if message['type'] != 'message':
                    continue
                self.frame(json.loads(message['data']))

    def frame(self, message):
        timestamp = message['timestamp']
        # HACK
        if timestamp < self.last_beat_timestamp:
            self.last_beat_timestamp = 0
        #######
        self.timestamps.append(timestamp)
        if len(self.timestamps) > 1:
            self.time_delta = ms_to_seconds(self.timestamps[-1] - self.timestamps[-2])
        if len(self.timestamps) > CACHE_FRAMES:
            self.timestamps.pop(0)
        points = message['points']
        values = []
        for partname in BODYPARTS_LOWER:
            part_positions = self.positions[partname]
            part_positions.append(numpy.array(points[partname]))
            if len(part_positions) > CACHE_FRAMES:
                part_positions.pop(0)
            values.append((partname, self.analyze_part(partname)))
        # pick max value
        if len(values) > ACTIVE_POINTS_FOR_BEAT:
            if timestamp - self.last_beat_timestamp < MINIMUM_BEAT_OFFSET:
                return
            partname, beat_value = max(values, key=itemgetter(1))
            beat_value = sum([v for k,v in values])
            if beat_value > 0:
                self.fire_beat(partname, beat_value)
                print partname, beat_value

    def analyze_part(self, partname):
        positions = self.positions[partname]
        velocities = self.velocities[partname]
        deltas = self.velocity_deltas[partname]
        if len(positions) < 3:
            return 0 #  not enough data to continue
        velocity = (positions[-1] - positions[-2]) * self.time_delta
        if sum([abs(v) for v in velocity]) < MAGNITUDE_SUM_CUTOFF:
            velocity[0] = velocity[1] = velocity[2] = 0
        velocities.append(velocity)
        velocity_count = len(velocities)
        if velocity_count < 2:
            return 0 #  not enough data to continue
        if velocity_count > CACHE_FRAMES:
            velocities.pop(0)
        delta = get_vector_delta(velocities[-2], velocities[-1])
        deltas.append(delta)
        delta_count = len(deltas)
        if delta_count < 2:
            return 0 #  not enough data to continue
        if delta_count > CACHE_FRAMES:
            deltas.pop(0)
        beat_worthy = [
            (d * PART_WEIGHT_MULTIPLIERS[partname] > VELOCITY_DELTA_CUTOFF)
            for d in deltas
        ]
        if beat_worthy[-2] and not beat_worthy[-1]:
            return deltas[-2]
        return 0 #  nothing worth reporting

    def fire_beat(self, partname, value):
        timestamp = self.timestamps[-1]
        payload = {
            'timestamp': timestamp,
            'type': partname,
            'intensity': value
        }
        self.redis.publish('dance-beat', json.dumps(payload))
        self.last_beat_timestamp = timestamp


if __name__ == '__main__':
    import redis
    import sys

    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = 'localhost'

    r = redis.Redis(host=host)
    dance_interpreter = DanceInterpreter(redis=r, listen_channel='dancer-state')
    dance_interpreter.run()
