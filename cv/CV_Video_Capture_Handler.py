import cv2
import numpy as np
import threading


class CV_Video_Capture_Handler:
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
            self.videocapture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.videocapture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.videocapture.set(cv2.CAP_PROP_FPS, 60.0)
            self.frame_lock = threading.Lock()
            self.width = self.videocapture.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.height = self.videocapture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.fps = self.videocapture.get(cv2.CAP_PROP_FPS)
            self.polled_frame = None
            self.process = threading.Thread(target=self._frame_continuous_poll)
            self.process.setDaemon(True)
            self.process.start()
            print("Video width: %f" % self.width)
            print("Video height: %f" % self.height)

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def _frame_continuous_poll(self):
        while True:
            ret, frame = self.videocapture.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            self.frame_lock.acquire()
            self.polled_frame = frame
            self.frame_lock.release()


    def _get_polled_frame(self):
        retval = None
        self.frame_lock.acquire()
        retval = self.polled_frame
        self.frame_lock.release()

        return retval

    def readHSVFrame(self):
        frame = self._get_polled_frame()
        return True, frame

    def readFrame(self):
        return True, self._get_polled_frame()
