import logging
import threading
from time import sleep

import cv2
import numpy as np
import scipy.misc as scm
from typing import Tuple

from cv import CV_GUI_Handler, CV_Video_Capture_Handler
from cv.CV_GUI_Handler import OpenCvHandler, NO_FRAME
from cv.ImageProcessing import crop
from rcvr import receiver
from snd import transmitter
from utils import Constants


def simulate_camera_tmtr(frame):
    frame[0:CV_GUI_Handler.HEIGHT / 2 + 1, 0:CV_GUI_Handler.WIDTH / 2 + 1, :] = 0
    frame[CV_GUI_Handler.HEIGHT / 2: CV_GUI_Handler.HEIGHT, CV_GUI_Handler.WIDTH / 2: CV_GUI_Handler.WIDTH, :] = 0
    scaled_frame = frame[::10, ::10]

    scaled_frame = np.uint8(np.clip(scaled_frame, (0, 0, 0), (255, 255, 255)))

    from utils.Constants import WIDTH, HEIGHT
    camera_frame = np.full((HEIGHT, WIDTH, 3), (0, 0, 0), dtype=np.uint8)
    if len(scaled_frame.shape) == 2:
        logging.error("Received a frame with only one dimension "
                      "(probably a binary image, used for debugging), so won't display it")
        return camera_frame
    camera_frame[80:80 + scaled_frame.shape[0], 5:5 + scaled_frame.shape[1]] = scaled_frame
    return camera_frame


def simulate_camera_rcvr(frame):
    scaled_frame = frame[::10, ::10]

    scaled_frame = np.uint8(np.clip(scaled_frame, (0, 0, 0), (255, 255, 255)))

    from utils.Constants import WIDTH, HEIGHT
    camera_frame = np.full((HEIGHT, WIDTH, 3), (0, 0, 0), dtype=np.uint8)
    if len(scaled_frame.shape) == 2:
        logging.error("Received a frame with only one dimension "
                      "(probably a binary image, used for debugging), so won't display it")
        return camera_frame
    camera_frame[80:80 + scaled_frame.shape[0], 5:5 + scaled_frame.shape[1]] = scaled_frame
    return camera_frame

class SimulationHandler:
    class __SimulationHandler:
        tmtr = None
        rcvr = None

        def __init__(self):
            # Instantiate the 2 receiver/transmitter singletons
            self.tmtr = SimulationHandler.TmtrSide()
            self.rcvr = SimulationHandler.RcvrSide()

        def __str__(self):
            return "Simulation handler singleton" + repr(self)

    instance = None

    def __init__(self):
        if not SimulationHandler.instance:
            SimulationHandler.instance = SimulationHandler.__SimulationHandler()

    def __getattr__(self, item):
        return getattr(self.instance, item)

    def __setattr__(self, item, value):
        return setattr(self.instance, item, value)

    class TmtrSide:
        class __TmtrSide:
            def __init__(self):
                pass

        tmtrInst = None

        def __init__(self):
            if not SimulationHandler.TmtrSide.tmtrInst:
                SimulationHandler.TmtrSide.tmtrInst = SimulationHandler.TmtrSide.__TmtrSide()
            self.frame = simulate_camera_tmtr(
                np.full((CV_GUI_Handler.HEIGHT, CV_GUI_Handler.WIDTH, 3), (0, 0, 14), dtype=np.uint8))

            self.screen_boundaries = (0, CV_Video_Capture_Handler.CV_Video_Capture_Handler.WIDTH,
                                      0, CV_Video_Capture_Handler.CV_Video_Capture_Handler.HEIGHT)

            self.hsv_frame_count = 0

        def send_new_frame(self, new_frame):
            self.frame = simulate_camera_tmtr(new_frame)

        def display_bgr_color(self, bgr_col):
            """Displays the given color on the whole screen"""
            color_frame = np.full((CV_GUI_Handler.HEIGHT, CV_GUI_Handler.WIDTH, 3), bgr_col, dtype=np.uint8)
            self.send_new_frame(color_frame)

        def display_hsv_color(self, hsv_col):
            """Converts the given color from HSV to BGR, and displays it"""
            converted_color = cv2.cvtColor(np.array([[[hsv_col, 255, 255]]], dtype=np.uint8), cv2.COLOR_HSV2BGR)
            color_frame = np.full((CV_GUI_Handler.HEIGHT, CV_GUI_Handler.WIDTH, 3), converted_color, dtype=np.uint8)
            self.send_new_frame(color_frame)

        def black_out(self):
            self.send_new_frame(NO_FRAME)

        def display_hsv_frame(self, hsvframe):
            resized_frame = scm.imresize(hsvframe, (Constants.WIDTH, Constants.HEIGHT), interp='bilinear')
            resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_HSV2BGR)
            self.send_new_frame(resized_frame)

        def readHSVFrame(self, write=False, caller='') -> np.ndarray:
            ret, frame = True, SimulationHandler.instance.rcvr.frame
            cropped_frame = crop(frame, self.screen_boundaries)

            if write:
                cv2.imwrite('../simulation_readHSVFrame_at_' + caller + str(self.hsv_frame_count) + '.jpg', frame)
                self.hsv_frame_count += 1

            return cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2HSV)

        def set_screen_boundaries(self, bounds):
            self.screen_boundaries = bounds

        def __getattr__(self, item):
            return getattr(self.tmtrInst, item)

        def __setattr__(self, name, value):
            return setattr(self.tmtrInst, name, value)

    class RcvrSide:
        class __ReceiverSide:
            def __init__(self):
                pass

        rcvrInst = None

        def __init__(self):
            if not SimulationHandler.RcvrSide.rcvrInst:
                SimulationHandler.RcvrSide.rcvrInst = SimulationHandler.RcvrSide.__ReceiverSide()
            self.frame = simulate_camera_rcvr(
                np.full((CV_GUI_Handler.HEIGHT, CV_GUI_Handler.WIDTH, 3), (0, 0, 14), dtype=np.uint8))

            self.screen_boundaries = (0, CV_Video_Capture_Handler.CV_Video_Capture_Handler.WIDTH,
                                      0, CV_Video_Capture_Handler.CV_Video_Capture_Handler.HEIGHT)
            self.hsv_frame_count = 0

        def send_new_frame(self, new_frame):
            self.frame = simulate_camera_rcvr(new_frame)

        def display_bgr_color(self, bgr_col):
            """Displays the given color on the whole screen"""
            color_frame = np.full((CV_GUI_Handler.HEIGHT, CV_GUI_Handler.WIDTH, 3), bgr_col, dtype=np.uint8)
            self.send_new_frame(color_frame)

        def display_hsv_color(self, hsv_col):
            """Converts the given color from HSV to BGR, and displays it"""
            converted_color = cv2.cvtColor(np.array([[[hsv_col, 255, 255]]], dtype=np.uint8), cv2.COLOR_HSV2BGR)
            color_frame = np.full((CV_GUI_Handler.HEIGHT, CV_GUI_Handler.WIDTH, 3), converted_color, dtype=np.uint8)
            self.send_new_frame(color_frame)

        def black_out(self):
            self.send_new_frame(NO_FRAME)

        def display_hsv_frame(self, hsvframe):
            resized_frame = scm.imresize(hsvframe, (Constants.WIDTH, Constants.HEIGHT), interp='bilinear')
            resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_HSV2BGR)
            self.send_new_frame(resized_frame)

        def readHSVFrame(self, write=False, caller='') -> np.ndarray:
            frame = SimulationHandler.instance.tmtr.frame
            cropped_frame = crop(frame, self.screen_boundaries)

            if write:
                cv2.imwrite('../simulation_readHSVFrame_at_' + caller + str(self.hsv_frame_count) + '.jpg',
                            cropped_frame)
            return cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2HSV)

        def readHSVFrame_akimbo(self, write=False, caller='') -> Tuple[np.ndarray, np.ndarray]:
            frame = SimulationHandler.instance.tmtr.frame

            cropped_frame1 = crop(frame, self.screen_boundaries1)
            cropped_frame2 = crop(frame, self.screen_boundaries2)
            cropped_frame1 = cv2.cvtColor(cropped_frame1, cv2.COLOR_BGR2HSV)
            cropped_frame2 = cv2.cvtColor(cropped_frame2, cv2.COLOR_BGR2HSV)

            if write:
                cv2.imwrite('../simulation_readHSVFrame_akimbo1_at_' + caller + str(self.hsv_frame_count) + '.jpg',
                            cropped_frame1)
                cv2.imwrite('../simulation_readHSVFrame_akimbo2_at_' + caller + str(self.hsv_frame_count) + '.jpg',
                            cropped_frame2)

            return cropped_frame1, cropped_frame2

        def set_screen_boundaries(self, bounds):
            self.screen_boundaries = bounds

        def set_akimbo_screen_boundaries(self, bounds1, bounds2):
            self.akimbo_mode = True
            self.screen_boundaries1 = bounds1
            self.screen_boundaries2 = bounds2

        def __getattr__(self, item):
            return getattr(self.rcvrInst, item)

        def __setattr__(self, name, value):
            return setattr(self.rcvrInst, name, value)


def main():
    Constants.SIMULATE = True

    simulation_handler = SimulationHandler()
    Constants.SIMULATION_HANDLER = simulation_handler

    cv_handler = OpenCvHandler()
    cv_handler.send_new_frame(simulation_handler.rcvr.frame)

    rcvr_thread = threading.Thread(target=receiver.main)
    rcvr_thread.setDaemon(True)
    rcvr_thread.start()

    tmtr_thread = threading.Thread(target=transmitter.main)
    tmtr_thread.setDaemon(True)
    tmtr_thread.start()

    while True:
        # main window shows what the transmitter is displaying, secondary shows what the receiver is displaying
        cv_handler.send_new_frame(simulation_handler.tmtr.frame)
        cv_handler.send_scnd_new_frame(simulation_handler.rcvr.frame)
        sleep(0.1)

    cv_handler.join_waiting_thread_handler()


if __name__ == '__main__':
    main()
