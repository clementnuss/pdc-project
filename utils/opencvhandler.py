import threading
from time import sleep, time

import cv2
import numpy as np

WIDTH = 800
HEIGHT = 600
MAIN_WINDOW = 'main_window'


class OpenCvHandler:
    class __CV_Handler:
        def __init__(self):
            pass

        def __str__(self):
            return "OpenCV handler singleton" + repr(self)

    instance = None

    def wait_key_func(self):
        print("Initializing main window")
        cv2.namedWindow(MAIN_WINDOW)
        cv2.startWindowThread()
        while True:
            if self.refresh:
                cv2.imshow(MAIN_WINDOW, self.instance.new_frame)
                self.instance.refresh = False
            if (cv2.waitKey(1) & 0xFF) == 27:
                break
        print("Escape key pressed - terminating the GUI")
        cv2.destroyAllWindows()

    def __init__(self):
        if not OpenCvHandler.instance:
            OpenCvHandler.instance = OpenCvHandler.__CV_Handler
            self.instance.new_frame = np.full((WIDTH, HEIGHT, 3), (255, 255, 255), dtype=np.uint8)
            self.instance.refresh = True
            self.instance.waiting_thread = threading.Thread(target=self.wait_key_func)
            self.instance.waiting_thread.setDaemon(True)
            self.instance.waiting_thread.start()

    def join_waiting_thread_handler(self):
        self.instance.waiting_thread.join()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __send_new_frame(self, new_frame):
        if self.instance.refresh:
            print('A frame was dropped!')
        else:
            self.instance.refresh = True
        self.instance.new_frame = new_frame

    def display_bgr_color(self, bgr_col):
        """Displays the given color on the whole screen"""
        color_frame = np.full((WIDTH, HEIGHT, 3), bgr_col, dtype=np.uint8)
        self.__send_new_frame(color_frame)

    def display_hsv_color(self, hsv_col):
        """Converts the given color from HSV to BGR, and displays it"""
        converted_color = cv2.cvtColor(hsv_col, cv2.COLOR_HSV2BGR)
        color_frame = np.full((WIDTH, HEIGHT, 3), converted_color, dtype=np.uint8)
        self.__send_new_frame(color_frame)


"""
# Code showing usage of the OpenCvHandler class
sampleHandler = OpenCvHandler()
sleep(1)
sampleHandler.display_bgr_color((255,0,255))
sleep(1)
sampleHandler.display_bgr_color((255,255,255))
sampleHandler.join_waiting_thread_handler()
"""
