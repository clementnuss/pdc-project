import collections
import logging
import time
from enum import Enum

import numpy as np

import cv.CV_GUI_Handler

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

S_VOID = np.array([[[np.uint8(0), np.uint8(0), np.uint8(0)]]])
S_ZERO = np.array([[[np.uint8(180), np.uint8(255), np.uint8(255)]]])
S_ONE = np.array([[[np.uint8(90), np.uint8(255), np.uint8(255)]]])

TRANSMISSION_RATE = 1.0 / 15.0


class State(Enum):
    IDLE = 'Idle'
    SYNC = 'Sync'
    SEND = 'Send'
    RECEIVE = 'Receive'
    WAIT_FOR_ACK = 'Wait'


class Transmitter(object):
    def __init__(self, file_name):
        self.state = State.IDLE
        self.cv_handler = cv.CV_GUI_Handler.OpenCvHandler()
        self.byte_sequence = collections.deque()
        self.last_byte_sent = None
        self.receiver_ack = True
        print('Initialized snd at state ' + str(self.state))

        self._load_file(file_name)

    def run(self):

        while True:
            if self.state == State.IDLE:
                self.doIdle()
            elif self.state == State.SYNC:
                self.doSync()
            elif self.state == State.SEND:
                if len(self.byte_sequence) > 0:
                    self.doSend()
                else:
                    logging.info("Transmission finished")
                    self.state = State.IDLE
            elif self.state == State.RECEIVE:
                self.doReceive()
            elif self.state == State.WAIT_FOR_ACK:
                logging.info("Transmitter branched in wait for ack mode")
                self.do_wait()
            else:
                raise NotImplementedError('Undefined snd state')

    def doIdle(self):
        time.sleep(1)

    def doSync(self):
        pass

    def doSend(self):
        byte_to_send = None

        if self.receiver_ack:
            self.receiver_ack = False
            logging.info("Transmitting new data")
            byte_to_send = self.byte_sequence.popleft()
        else:
            logging.warning("Retransmitting previous data")
            byte_to_send = self.last_byte_sent

        self.last_byte_sent = byte_to_send
        self._send_byte(byte_to_send)
        self.state = State.WAIT_FOR_ACK

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

    def do_wait(self):

        self.cv_handler.display_hsv_color(S_VOID)

        while not self.receiver_ack:
            if input("press enter to trigger ack") != None:
                self.receiver_ack = True

        logging.info("Received ACK from receiver device")
        self.state = State.SEND

    def _load_file(self, file_name):

        with open(file_name, "rb") as f:
            byte = f.read(1)
            while byte:
                self.byte_sequence.append(byte)
                byte = f.read(1)


def main():
    r = Transmitter("../data/dummyText1.txt")
    r.state = State.SEND
    r.run()


if __name__ == "__main__":
    main()
