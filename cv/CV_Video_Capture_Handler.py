import logging
import threading
import time

import cv2
import numpy as np
from typing import Tuple

import utils.Constants
from cv.ImageProcessing import crop

logging.basicConfig(format='%(module)15s # %(levelname)s: %(message)s', level=logging.INFO)

class CV_Video_Capture_Handler:
    WIDTH = 640
    HEIGHT = 480

    class __CV_Video_Capture_Handler:
        def __init__(self):
            pass

        def __str__(self):
            return "OpenCV video capture handler singleton" + repr(self)

    instance = None

    def __init__(self):
        if not CV_Video_Capture_Handler.instance:
            CV_Video_Capture_Handler.instance = CV_Video_Capture_Handler.__CV_Video_Capture_Handler
            self.videocapture = cv2.VideoCapture(0)
            self.videocapture.set(cv2.CAP_PROP_FRAME_WIDTH, CV_Video_Capture_Handler.WIDTH)
            self.videocapture.set(cv2.CAP_PROP_FRAME_HEIGHT, CV_Video_Capture_Handler.HEIGHT)
            self.videocapture.set(cv2.CAP_PROP_FPS, 60.0)
            self.video_lock = threading.Lock()
            self.width = self.videocapture.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.height = self.videocapture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.fps = self.videocapture.get(cv2.CAP_PROP_FPS)
            self.polled_frame1 = None
            self.polled_frame2 = None
            self.screen_boundaries1 = (0, CV_Video_Capture_Handler.WIDTH, 0, CV_Video_Capture_Handler.HEIGHT)
            self.screen_boundaries2 = (0, CV_Video_Capture_Handler.WIDTH, 0, CV_Video_Capture_Handler.HEIGHT)

            self.process = threading.Thread(target=
                                            self._frame_continuous_poll_akimbo if utils.Constants.USE_AKIMBO_SCREEN
                                            else self._frame_continuous_poll)

            self.process.setDaemon(True)
            self.process.start()
            time.sleep(0.5)
            print("Video width: %f" % self.width)
            print("Video height: %f" % self.height)

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def _frame_continuous_poll(self):
        logging.info("Starting classic frame polling mode.")
        while True:
            ret, frame = self.videocapture.read()
            bounds = None

            self.video_lock.acquire()
            bounds = self.screen_boundaries1
            self.video_lock.release()

            cropped_frame = crop(frame, bounds)
            cropped_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2HSV)

            self.video_lock.acquire()
            self.polled_frame1 = cropped_frame
            self.video_lock.release()

    def _frame_continuous_poll_akimbo(self):
        logging.info("Starting akimbo frame polling mode.")
        while True:
            ret, frame = self.videocapture.read()
            bounds1 = None
            bounds2 = None

            self.video_lock.acquire()
            bounds1 = self.screen_boundaries1
            bounds2 = self.screen_boundaries2
            self.video_lock.release()

            cropped_frame1 = crop(frame, bounds1)
            cropped_frame2 = crop(frame, bounds2)
            cropped_frame1 = cv2.cvtColor(cropped_frame1, cv2.COLOR_BGR2HSV)
            cropped_frame2 = cv2.cvtColor(cropped_frame2, cv2.COLOR_BGR2HSV)

            self.video_lock.acquire()
            self.polled_frame1 = cropped_frame1
            self.polled_frame2 = cropped_frame2
            self.video_lock.release()

    def _get_polled_frame(self):
        retval = None
        self.video_lock.acquire()
        retval = self.polled_frame1.copy()
        self.video_lock.release()

        return retval

    def _get_polled_akimbo_frame(self):
        retval1 = None
        retval2 = None
        self.video_lock.acquire()
        retval1 = self.polled_frame1.copy()
        retval2 = self.polled_frame2.copy()
        self.video_lock.release()

        return retval1, retval2

    def set_screen_boundaries(self, bounds):
        self.video_lock.acquire()
        self.screen_boundaries1 = bounds
        self.video_lock.release()

    def set_akimbo_screen_boundaries(self, bounds1, bounds2):
        self.akimbo_mode = True
        self.screen_boundaries1 = bounds1
        self.screen_boundaries2 = bounds2

    def readHSVFrame(self) -> Tuple[bool, np.ndarray]:
        return True, self._get_polled_frame()

# Commented, because we only have HSV frame now
#   def readFrame(self):
#        return True, self._get_polled_frame()
