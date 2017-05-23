import collections
import time
from enum import Enum

import numpy as np

import cv.CV_GUI_Handler

S_ZERO = np.array([[[np.uint8(180), np.uint8(255), np.uint8(255)]]])
S_ONE = np.array([[[np.uint8(90), np.uint8(255), np.uint8(255)]]])

TRANSMISSION_RATE = 1.0 / 15.0


class State(Enum):
    IDLE = 'Idle'
    SYNC = 'Sync'
    SEND = 'Send'
    RECEIVE = 'Receive'
    WAIT = 'Wait'


class Transmitter(object):
    def __init__(self, file_name):
        self.state = State.IDLE
        self.cv_handler = cv.CV_GUI_Handler.OpenCvHandler()
        self.byte_sequence = collections.deque()
        print('Initialized snd at state ' + str(self.state))

        self._load_file(file_name)

    def run(self):
        if self.state == State.IDLE:
            self.doIdle()
        elif self.state == State.SYNC:
            self.doSync()
        elif self.state == State.SEND:
            self.doSend()
        elif self.state == State.RECEIVE:
            self.doReceive()
        elif self.state == State.WAIT:
            self.doWait()
        else:
            raise NotImplementedError('Undefined snd state')

    def doIdle(self):
        pass

    def doSync(self):
        pass

    def doSend(self):
        while len(self.byte_sequence) != 0:
            byte_to_send = self.byte_sequence.popleft()
            self._send_byte(byte_to_send)

    def _send_byte(self, b):
        """
        Send one byte starting from the least significant bit
        
        :param b: 
        :return: 
        """
        processed_b = b[0]
        for i in range(0, 8):
            bit_to_send = processed_b & 1
            processed_b = processed_b >> 1

            if bit_to_send:
                self.cv_handler.display_hsv_color(S_ONE)
                print(1)
                time.sleep(TRANSMISSION_RATE)
            else:
                self.cv_handler.display_hsv_color(S_ZERO)
                print(0)
                time.sleep(TRANSMISSION_RATE)


    def doReceive(self):
        pass

    def doWait(self):
        pass

    def _load_file(self, file_name):

        with open(file_name, "rb") as f:
            byte = f.read(1)
            while byte:
                self.byte_sequence.append(byte)
                byte = f.read(1)

def main():
    r = Transmitter("../data/dummyText1.txt")
    r.doSend()


if __name__ == "__main__":
    main()
