import logging
import math
import time

import cv.CV_GUI_Handler
import cv.CV_Video_Capture_Handler
from cv.ImageProcessing import *
from utils import Constants
from utils.Symbols import *


class State_Machine(object):
    TRANSMISSION_RATE = 1.0 / 5.0
    SAMPLING_OFFSET = TRANSMISSION_RATE / 2.0
    CONVERGENCE_THRESHOLD = 10000
    BLACK_THRESHOLD = 200000

    def __init__(self):
        self.clock_start = -1
        self.tick_count = 0
        self.log_count = 0

        self.SYMBOL_ZERO_MASK = np.full((HEIGHT, WIDTH, 3), fill_value=S_ZERO, dtype=np.uint8)
        self.SYMBOL_ONE_MASK = np.full((HEIGHT, WIDTH, 3), fill_value=S_ONE, dtype=np.uint8)
        self.ACK_MASK = self.SYMBOL_ONE_MASK
        self.NO_ACK_MASK = self.SYMBOL_ZERO_MASK
        self.VOID_MASK = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        self.screen_mask = None

        if Constants.SIMULATE:
            simulation_handler = Constants.SIMULATION_HANDLER
            self.cv_handler = simulation_handler.tmtr
            self.cap = simulation_handler.tmtr
        else:
            self.cv_handler = cv.CV_GUI_Handler.OpenCvHandler()
            self.cap = cv.CV_Video_Capture_Handler.CV_Video_Capture_Handler()

    def compute_screen_mask(self, color_range):
        converged = False
        ret, frame = self.cap.readHSVFrame()
        prev_mask = getMask(frame, color_range)

        while not converged:
            ret, frame = self.cap.readHSVFrame()
            mask = getMask(frame, color_range)

            s = np.sum(mask)
            diff = np.sum(mask - prev_mask)
            print("Mask sum: ", s)
            print("Mask diff: ", diff)

            if diff < State_Machine.CONVERGENCE_THRESHOLD and s > State_Machine.BLACK_THRESHOLD:
                converged = True
                self.screen_mask = np.uint8(mask / np.uint8(255))[..., np.newaxis]
            else:
                prev_mask = mask

            if not Constants.SIMULATE:
                self.cv_handler.display_hsv_frame(
                    superimpose(self.NO_ACK_MASK, np.uint8(mask[::10, ::10])[..., np.newaxis]))
            time.sleep(0.2)

        print("Synchronization OK")
        self.SYMBOL_ZERO_MASK = self.SYMBOL_ZERO_MASK * self.screen_mask
        self.SYMBOL_ONE_MASK = self.SYMBOL_ONE_MASK * self.screen_mask
        self.ACK_MASK = SYMBOL_ACK_MASK * self.screen_mask
        self.NO_ACK_MASK = SYMBOL_NO_ACK_MASK * self.screen_mask

    def get_ack_scores(self):
        ret, frame = self.cap.readHSVFrame()
        masked_frame = frame * self.screen_mask

        ack_score = compute_score(masked_frame, self.ACK_MASK)
        no_ack_score = compute_score(masked_frame, self.NO_ACK_MASK)

        return ack_score, no_ack_score

    def get_symbols_scores(self, first_symbol_mask, second_symbol_mask):
        ret, frame = self.cap.readHSVFrame()
        masked_frame = frame * self.screen_mask

        first_score = compute_score(masked_frame, first_symbol_mask)
        second_score = compute_score(masked_frame, second_symbol_mask)

        return first_score, second_score

    def _align_clock(self):
        curr_time = time.time()

        # Delay clock towards a whole time to increase sleep relative precision
        while curr_time - np.fix(curr_time) > 0.3:
            curr_time = time.time()

        # Align clock on whole time
        to_sleep = math.floor(curr_time + 1.0) - curr_time
        logging.info(curr_time)
        time.sleep(to_sleep)
        self.clock_start = time.time()
        logging.info("Clock start is at: " + str(self.clock_start))

    def sleep_until_next_tick(self):
        self.tick_count = self.tick_count + 1
        self.log_count = self.log_count + 1

        current_time = time.time()
        sleep_amount = (self.tick_count * State_Machine.TRANSMISSION_RATE + self.clock_start) - current_time

        if self.log_count > 0:
            self.log_count = 0
            logging.info("Going to sleep for : " + str(sleep_amount) + " seconds. Time is " + str(current_time))

        if sleep_amount < 0:
            logging.warning("Skipping sleep time !")
            return

        time.sleep(sleep_amount)
