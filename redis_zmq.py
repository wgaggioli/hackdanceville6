import argparse
import json

import zmq

from subscriber import Subscriber


class RedisZmqPublisher(Subscriber):
    def __init__(self, channels=None, zmq_port=5556, **kwargs):
        if channels is None:
            channels = ['*']
        super(RedisZmqPublisher, self).__init__(channels, **kwargs)
        self.zmq_port = zmq_port
        self.init_zmq()

    def do_subscribe(self):
        self.pubsub.psubscribe(self.channels)

    def init_zmq(self):
        context = zmq.Context()
        self.zmq_socket = context.socket(zmq.PUB)
        self.zmq_socket.bind("tcp://*:{}".format(self.zmq_port))

    def on_event(self, item):
        print item['channel'], item['data']
        self.zmq_socket.send("{} {}".format(item['channel'], item['data']))


if __name__ == "__main__":
    parser = argparse.ArgumentParser("redis --> zmq")
    parser.add_argument('--redis_host', default='localhost')
    args = parser.parse_args()
    publisher = RedisZmqPublisher(redis_host=args.redis_host)
    publisher.subscribe()
