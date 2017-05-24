import time
from enum import Enum

import cv.CV_GUI_Handler
import cv.CV_Video_Capture_Handler
from cv.ImageProcessing import *


class State(Enum):
    IDLE = 'Idle'
    SYNC = 'Sync'
    RECEIVE = 'Receive'
    CHECK = 'Check'
    WAIT = 'Wait'


class Receiver(object):
    # At distance ~3.20m, np.sum of the thresholded image gives ~510000 (because values are 255)
    # The threshold then needs to be around 500000
    CONVERGENCE_THRESHOLD = 500000
    BLACK_THRESHOLD = 2000000
    DUMMY_MASK = np.zeros((480, 640), dtype=np.uint8)
    DUMMY_MASK[200:300, 200:400] = np.uint8(1)
    DUMMY_MASK = np.dstack([DUMMY_MASK] * 3)

    def __init__(self):
        self.cv_handler = cv.CV_GUI_Handler.OpenCvHandler()
        self.cap = cv.CV_Video_Capture_Handler.CV_Video_Capture_Handler()
        self.state = State.IDLE
        self.bitCount = 0
        self.screen_mask = None

        print('Initialized rcvr at state ' + str(self.state))
        time.sleep(1)

    def run(self):
        if self.state == State.IDLE:
            self.doIdle()
        elif self.state == State.SYNC:
            self.doSync()
        elif self.state == State.RECEIVE:
            self.doReceive()
        elif self.state == State.CHECK:
            self.doCheck()
        elif self.state == State.WAIT:
            self.doWait()
        else:
            raise NotImplementedError('Undefined receiver state')

    def doIdle(self):
        pass

    def doSync(self):
        """
        Compute the location of sender's screen. 
        :return: 
        """

        pass

    def doReceive(self):
        while True:
            ret, frame = self.cap.readHSVFrame()
            masked_frame = frame * self.DUMMY_MASK
            self.cv_handler.send_new_frame(masked_frame)

    def doCheck(self):
        pass

    def doWait(self):
        pass

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
    print("hi")
    # ret, frame = rcvr.screen_decoder.getCameraSnapshot()
    # rcvr.screen_decoder.displayFrame(frame)
    r._compute_screen_mask()
    r.doReceive()

if __name__ == "__main__":
    main()
    print(test)
    input("")
