import zmq


if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    port = 5556
    socket.connect("tcp://localhost:%s" % port)
    socket.setsockopt(zmq.SUBSCRIBE, 'dance-beat')
    while True:
        resp = socket.recv()
        topic, data = resp.split(' ', 1)
        print topic, data
