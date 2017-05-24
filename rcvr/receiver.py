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


def compute_score(masked_frame, color_mask) -> int:
    diff = masked_frame - color_mask
    diff = diff * diff
    return np.sum(diff)


class Receiver(object):
    # At distance ~3.20m, np.sum of the thresholded image gives ~510000 (because values are 255)
    # The threshold then needs to be around 500000
    CONVERGENCE_THRESHOLD = 500000
    BLACK_THRESHOLD = 2000000
    DUMMY_MASK = np.zeros((480, 640), dtype=np.uint8)
    DUMMY_MASK[200:300, 200:400] = np.uint8(1)
    DUMMY_MASK = np.dstack([DUMMY_MASK] * 3)

    SYMBOL_ZERO_MASK = np.full((480, 640, 3), fill_value=S_ZERO, dtype=np.uint8)
    SYMBOL_ONE_MASK = np.full((480, 640, 3), fill_value=S_ONE, dtype=np.uint8)

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
            masked_frame = frame * self.screen_mask
            self.cv_handler.send_new_frame(masked_frame)
            zero_score = compute_score(masked_frame, self.SYMBOL_ZERO_MASK)
            one_score = compute_score(masked_frame, self.SYMBOL_ONE_MASK)
            if (zero_score > one_score):
                print("0")
            else:
                print("1")

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
                self.screen_mask = mask
            else:
                prev_mask = mask

            self.cv_handler.send_new_frame(mask)
            time.sleep(1)

        print("Synchronization OK")
        self.SYMBOL_ZERO_MASK = self.SYMBOL_ZERO_MASK * self.screen_mask
        self.SYMBOL_ONE_MASK = self.SYMBOL_ONE_MASK * self.screen_mask


def main():
    r = Receiver()
    # ret, frame = rcvr.screen_decoder.getCameraSnapshot()
    # rcvr.screen_decoder.displayFrame(frame)
    r._compute_screen_mask()
    r.do_receive()
    r.do_validate_data()


if __name__ == "__main__":
    main()
    input("")
