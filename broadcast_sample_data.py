import sys
import redis
import re
import time


if __name__ == '__main__':
    for file in sys.argv[1:]:
        with open(file, 'r') as fp:
            datapoints = list(fp)
    r = redis.Redis()
    i = 0
    total = len(datapoints)
    while True:
        time.sleep(0.01)
        r.publish('dancer-state', datapoints[i])
        i = (i + 1) % total
