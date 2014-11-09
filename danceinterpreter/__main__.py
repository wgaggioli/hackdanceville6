import redis
from danceinterpreter import DanceInterpreter


r = redis.Redis()
dance_interpreter = DanceInterpreter(redis=r, listen_channel='dancer-state')
dance_interpreter.run()
