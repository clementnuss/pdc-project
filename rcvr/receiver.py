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
    def __init__(self):
        self.cv = cv.CV_GUI_Handler.OpenCvHandler()
        self.cap = cv.CV_Video_Capture_Handler.CV_Video_Capture_Handler()
        self.state = State.IDLE
        self.bitCount = 0
        self.screen_mask = None

        print('Initialized rcvr at state ' + str(self.state))

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
        pass

    def doCheck(self):
        pass

    def doWait(self):
        pass

    def _compute_screen_mask(self):
        ret, frame = self.cap.readFrame()
        self.screen_mask = getMask(frame)

        self.cv.send_new_frame(self.screen_mask)


def main():
    r = Receiver()
    print("hi")
    # ret, frame = rcvr.screen_decoder.getCameraSnapshot()
    # rcvr.screen_decoder.displayFrame(frame)
    r._compute_screen_mask()

if __name__ == "__main__":
    main()
    input("Press enter to exit")
