import collections
import time
from enum import Enum

import cv.CV_GUI_Handler
import cv.CV_Video_Capture_Handler
import snd.transmitter
from cv.ImageProcessing import *
from utils.Symbols import *


class State(Enum):
    IDLE = 'Idle'
    SYNC = 'Sync'
    RECEIVE = 'Receive'
    CHECK = 'Check'
    VALIDATE_DATA = 'Validate data'


class Receiver(object):
    CONVERGENCE_THRESHOLD = 10000
    BLACK_THRESHOLD = 2000000
    DUMMY_MASK = np.zeros((480, 640), dtype=np.uint8)
    DUMMY_MASK[200:300, 200:400] = np.uint8(1)
    DUMMY_MASK = np.dstack([DUMMY_MASK] * 3)

    def __init__(self):
        self.cv_handler = cv.CV_GUI_Handler.OpenCvHandler()
        self.cap = cv.CV_Video_Capture_Handler.CV_Video_Capture_Handler()
        self.state = State.IDLE
        self.decoded_byte = 0
        self.decoded_sequence = collections.deque
        self.bitCount = 0
        self.screen_mask = None

        print('Initialized rcvr at state ' + str(self.state))
        time.sleep(1)

    def run(self):
        if self.state == State.IDLE:
            self.do_idle()
        elif self.state == State.SYNC:
            self.do_sync()
        elif self.state == State.RECEIVE:
            self.do_receive()
        elif self.state == State.CHECK:
            self.do_check()
        elif self.state == State.VALIDATE_DATA:
            self.do_validate_data()
        else:
            raise NotImplementedError('Undefined receiver state')

    def do_idle(self):
        pass

    def do_sync(self):
        """
        Compute the location of sender's screen. 
        :return: 
        """

        pass

    def do_receive(self):
        while True:
            ret, frame = self.cap.readHSVFrame()
            masked_frame = frame * self.DUMMY_MASK
            self.cv_handler.send_new_frame(masked_frame)

    def do_check(self):
        pass

    def do_validate_data(self):
        data_is_valid = True

        if data_is_valid:
            self.cv_handler.display_hsv_color(S_ACK)
        else:
            self.cv_handler.display_hsv_color(S_NO_ACK)

        time.sleep(snd.transmitter.TRANSMISSION_RATE)
        self.cv_handler.display_hsv_color(S_VOID)
        self.state = State.RECEIVE

    def _compute_checksum(self):
        return True

    def _compute_screen_mask(self):
        converged = False
        ret, frame = self.cap.readHSVFrame()
        prev_mask = getMask(frame)

        while not converged:
            ret, frame = self.cap.readHSVFrame()
            mask = getMask(frame)

            s = np.sum(mask)
            diff = np.sum(mask - prev_mask)
            print("Mask sum: ", s)
            print("Mask diff: ", diff)

            if diff < Receiver.CONVERGENCE_THRESHOLD and s > Receiver.BLACK_THRESHOLD:
                converged = True
            else:
                prev_mask = mask

            self.cv_handler.send_new_frame(mask)
            time.sleep(1)

        print("Synchronization OK")


def main():
    r = Receiver()
    # ret, frame = rcvr.screen_decoder.getCameraSnapshot()
    # rcvr.screen_decoder.displayFrame(frame)
    r.do_validate_data()

if __name__ == "__main__":
    main()
    print(test)
    input("")
