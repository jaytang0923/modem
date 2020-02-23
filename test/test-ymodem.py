import threading
import time
import StringIO
import Queue
import sys
from modem import *
import serial,datetime

class CserialControl(object):
    def __init__(self, sleepfunc=time.sleep):
        self.comnum = None  ###COMx
        self.com = None  ####fd

        self.sleepfunc = sleepfunc
        self.timeout_flag = True

    def Open(self, comx, baudrate=115200):
        self.comnum = comx
        try:
            self.com = serial.Serial(self.comnum, baudrate, bytesize=8, parity='N', stopbits=1, timeout=0.04,
                                     interCharTimeout=0.04)
            self.com.reset_input_buffer()
            self.com.reset_output_buffer()
            return True
        except:
            self.com = None
            return False

    def Close(self):
        if self.com is not None:
            self.com.close()
            self.com = None
            return True
        return False

    def SendData(self, databytes):
        try:
            self.flushport()
            self.com.write(databytes)
            return True
        except Exception, e:
            #log.error('write com error')
            return False

    def ReadData(self, readsize, timeout):
        try:
            st = datetime.datetime.now()
            dlen = 0
            buf = ''
            while ((((datetime.datetime.now() - st).seconds) + float(
                    (datetime.datetime.now() - st).microseconds) / 1000000) < timeout) and self.timeout_flag:
                inlen = self.com.inWaiting()
                if inlen > 0:
                    if inlen > (readsize - len(buf)):
                        inlen = (readsize - len(buf))
                    rcv = self.com.read(inlen)
                    if len(rcv) > 0:
                        buf += rcv
                        dlen += len(rcv)

                    if len(buf) >= readsize:
                        break
                else:
                    self.sleepfunc(0.02)
        except:
            #log.exception('read error')
            return ''

        return buf

    def flushport(self):
        try:
            self.com.flushInput()
            self.com.flushOutput()
            return True
        except:
            return False

import binascii


class SerialIO(CserialControl):
    streams = [Queue.Queue(), Queue.Queue()]
    stdin = []
    stdot = []
    delay = 0.01  # simulate modem delays

    def __init__(self, com):
        self.comnum = com
        super(SerialIO, self).__init__()

    def putc(self, data, q=0):
        print '->', self.comnum, binascii.b2a_hex(data)
        self.SendData(data)
        return len(data)

    def getc(self, size, q=0):
        return self.ReadData(size, 200)

    def open(self, com):
        print 'open', com
        return self.Open(com)

    def close(self):
        return self.Close()


class Client(threading.Thread):
    def __init__(self, io, server, filename):
        threading.Thread.__init__(self)
        self.io = io
        # self.server = server
        self.stream = filename  # open(filename, 'rb')
        print 'client com:', self.io.comnum

    def getc(self, data, timeout=0):
        print 'cg'
        return self.io.getc(data, 0)

    def putc(self, data, timeout=0):
        print "cp", self.io.comnum
        return self.io.putc(data, 0)

    def run(self):
        self.io.open('com8')
        print 'Copen:', self.io.comnum
        self.ymodem = YMODEM(self.getc, self.putc)
        print 'c.send', self.ymodem.send(self.stream)
        self.io.close()


class Server(SerialIO, threading.Thread):
    def __init__(self, io):
        threading.Thread.__init__(self)
        self.io = io
        self.stream = './recv'  # StringIO.StringIO()
        print 'servercom:', self.io.comnum

    def getc(self, data, timeout=0):
        return self.io.getc(data, 1)

    def putc(self, data, timeout=0):
        return self.io.putc(data, 1)

    def run(self):
        self.io.open('com7')
        print 'sopen', self.io.comnum
        self.ymodem = YMODEM(self.getc, self.putc)
        print 's.recv', self.ymodem.recv(self.stream)
        print 'got'


if __name__ == '__main__':
    files = './send/*'
    import glob
    print glob.glob(files)

    iser = SerialIO('com8')
    icli = SerialIO('com7')
    s = Server(iser)
    c = Client(icli, s, files)
    s.start()
    # c.start()
