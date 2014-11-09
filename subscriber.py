
import redis


class Subscriber(object):
    def __init__(self, channels, redis_host='localhost', redis_port=6379):
        self.channels = channels
        client = redis.StrictRedis(host=redis_host, port=redis_port)
        self.pubsub = client.pubsub()

    def on_subscribe(self):
        pass

    def on_close(self):
        pass

    def do_subscribe(self):
        self.pubsub.subscribe(self.channels)

    def subscribe(self):
        self.do_subscribe()
        self.on_subscribe()
        try:
            for item in self.pubsub.listen():
                self.on_event(item)
        finally:
            self.on_close()

    def on_event(self, item):
        pass