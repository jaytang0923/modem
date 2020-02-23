import threading
import time
import StringIO
import Queue
import sys
from modem import *


class FakeIO(object):
    streams = [Queue.Queue(), Queue.Queue()]
    stdin = []
    stdot = []
    delay = 0.01  # simulate modem delays

    def putc(self, data, q=0):
        for char in data:
            self.streams[1 - q].put(char)
            # print 'p%d(0x%x)' % (q, ord(char)),
            sys.stdout.flush()
        return len(data)

    def getc(self, size, q=0):
        data = []
        while size:
            try:
                char = self.streams[q].get()
                # print 'r%d(0x%x)' % (q, ord(char)),
                sys.stdout.flush()
                data.append(char)
                size -= 1
            except Queue.Empty:
                return None
        return ''.join(data)


class Client(threading.Thread):
    def __init__(self, io, server, filename):
        threading.Thread.__init__(self)
        self.io = io
        self.server = server
        self.stream = filename  # open(filename, 'rb')

    def getc(self, data, timeout=0):
        return self.io.getc(data, 0)

    def putc(self, data, timeout=0):
        return self.io.putc(data, 0)

    def run(self):
        self.ymodem = YMODEM(self.getc, self.putc)
        print 'c.send', self.ymodem.send(self.stream)


class Server(FakeIO, threading.Thread):
    def __init__(self, io):
        threading.Thread.__init__(self)
        self.io = io
        self.stream = './recv'  # StringIO.StringIO()

    def getc(self, data, timeout=0):
        return self.io.getc(data, 1)

    def putc(self, data, timeout=0):
        return self.io.putc(data, 1)

    def run(self):
        self.ymodem = YMODEM(self.getc, self.putc)
        print 's.recv', self.ymodem.recv(self.stream)
        print 'got'


if __name__ == '__main__':
    files = './send/*'
    import glob
    print glob.glob(files)

    i = FakeIO()
    s = Server(i)
    c = Client(i, s, files)
    s.start()
    c.start()
