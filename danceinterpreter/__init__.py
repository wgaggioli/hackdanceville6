import numpy
from numpy import linalg
import json


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
BODYPARTS_LOWER = [s.lower() for s in BODYPARTS]
CACHE_FRAMES = 4
VELOCITY_BEAT_CUTOFF = 1.5


def get_vector_delta(a,b):
    cosang = numpy.dot(a,b)
    sinang = linalg.norm(numpy.cross(a,b))
    return numpy.arctan2(sinang, cosang)


class DanceInterpreter(object):

    def __init__(self, redis=None, listen_channel=None):
        self.redis = redis
        self.listen_channel = listen_channel
        self.timestamps = []
        self.positions = {k:[] for k in BODYPARTS_LOWER}
        self.velocities = {k:[] for k in BODYPARTS_LOWER}
        self.velocity_deltas = {k:[] for k in BODYPARTS_LOWER}
    
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
        self.timestamps.append(message['timestamp'])
        if len(self.timestamps) > 1:
            self.time_delta = (self.timestamps[-1] - self.timestamps[-2])/1000.0
        if len(self.timestamps) > CACHE_FRAMES:
            self.timestamps.pop(0)
        points = message['points']
        for partname in BODYPARTS_LOWER:
            part_positions = self.positions[partname]
            part_positions.append(numpy.array(points[partname]))
            if len(part_positions) > CACHE_FRAMES:
                part_positions.pop(0)
            self.analyze_part(partname)
    
    def analyze_part(self, partname):
        positions = self.positions[partname]
        #print positions[-1],
        velocities = self.velocities[partname]
        deltas = self.velocity_deltas[partname]
        if len(positions) < 3:
            return #  not enough data to continue
        velocity = (positions[-1] - positions[-2]) * self.time_delta
        print velocity
        if sum([abs(v) for v in velocity]) < 0.15:
            velocity[0] = velocity[1] = velocity[2] = 0
        #print velocity,
        velocities.append(velocity)
        velocity_count = len(velocities)
        if velocity_count < 2:
            return #  not enough data to continue
        if velocity_count > CACHE_FRAMES:
            velocities.pop(0)
        delta = get_vector_delta(velocities[-2], velocities[-1])
        #print delta,
        deltas.append(delta)
        delta_count = len(deltas)
        if delta_count < 2:
            return #  not enough data to continue
        if delta_count > CACHE_FRAMES:
            deltas.pop(0)
        beat_worthy = [(d > VELOCITY_BEAT_CUTOFF) for d in deltas]
        if beat_worthy[-2] and not beat_worthy[-1]:
            self.fire_beat(partname)
            #print 'beat',
        #print

    def fire_beat(self, partname):
        payload = {
            'timestamp': self.timestamps[-1],
            'type': partname,
            'intensity': self.velocity_deltas[partname][-2]
        }
        self.redis.publish('dance-beat', json.dumps(payload))
