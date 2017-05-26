import threading
import time

import cv2
import numpy as np
from typing import Tuple

from cv.ImageProcessing import crop


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
            self.polled_frame = None
            self.screen_boundaries = (0, CV_Video_Capture_Handler.WIDTH, 0, CV_Video_Capture_Handler.HEIGHT)
            self.process = threading.Thread(target=self._frame_continuous_poll)
            self.process.setDaemon(True)
            self.process.start()
            time.sleep(0.5)
            print("Video width: %f" % self.width)
            print("Video height: %f" % self.height)

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def _frame_continuous_poll(self):
        while True:
            ret, frame = self.videocapture.read()
            bounds = None

            self.video_lock.acquire()
            bounds = self.screen_boundaries
            self.video_lock.release()

            cropped_frame = crop(frame, bounds)
            cropped_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2HSV)

            self.video_lock.acquire()
            self.polled_frame = cropped_frame
            self.video_lock.release()

    def _get_polled_frame(self):
        retval = None
        self.video_lock.acquire()
        retval = self.polled_frame.copy()
        self.video_lock.release()

        return retval

    def set_screen_boundaries(self, bounds):
        self.video_lock.acquire()
        self.screen_boundaries = bounds
        self.video_lock.release()

    def readHSVFrame(self) -> Tuple[bool, np.ndarray]:
        return True, self._get_polled_frame()

# Commented, because we only have HSV frame now
#   def readFrame(self):
#        return True, self._get_polled_frame()
