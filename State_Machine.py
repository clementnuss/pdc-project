import logging
import math
import time

import cv.CV_GUI_Handler
import cv.CV_Video_Capture_Handler
from cv.ImageProcessing import *
from utils import Constants
from utils.Symbols import *


class State_Machine(object):
    TRANSMISSION_RATE = 1.0 / 4.0
    SAMPLING_OFFSET = TRANSMISSION_RATE / 2.0
    CONVERGENCE_BOUND_THRESHOLD = 15
    CONVERGENCE_THRESHOLD = 10000
    BLACK_THRESHOLD = 200000

    def __init__(self):
        self.clock_start = -1
        self.tick_count = 0
        self.log_count = 0

        if Constants.USE_MASK:
            self.SYMBOL_ZERO_MASK = np.full((HEIGHT, WIDTH, 3), fill_value=S_ZERO, dtype=np.uint8)
            self.SYMBOL_ONE_MASK = np.full((HEIGHT, WIDTH, 3), fill_value=S_ONE, dtype=np.uint8)
            self.ACK_MASK = self.SYMBOL_ONE_MASK
            self.NO_ACK_MASK = self.SYMBOL_ZERO_MASK
            self.VOID_MASK = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            self.screen_mask = None
        else:
            self.screen_boundaries = None
            self.SYMBOL_ZERO_REF = None
            self.SYMBOL_ONE_REF = None
            self.ACK_REF = None
            self.NO_ACK_REF = None
            self.VOID_REF = None

        if Constants.SIMULATE:
            self.cv_handler = None
            self.cap = None
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
        self.ACK_MASK = SYMBOL_ACK_REF * self.screen_mask
        self.NO_ACK_MASK = SYMBOL_NO_ACK_REF * self.screen_mask

    def compute_screen_boundaries(self, color_range):
        converged = False
        min_x = min_y = max_x = max_y = 0

        while not converged:
            time.sleep(0.2)
            ret, frame = self.cap.readHSVFrame()

            frame_thresholded = getMask(frame, color_range)

            canny_frame = cv2.Canny(frame_thresholded, 50, 150, apertureSize=3)

            contoured_frame, contours0, hierarchy = cv2.findContours(canny_frame, mode=cv2.RETR_EXTERNAL,
                                                                     method=cv2.CHAIN_APPROX_SIMPLE)

            # Approximate contour by multiple straight lines
            contours = [cv2.approxPolyDP(cnt, 3, True) for cnt in contours0]

            logging.info("Got " + str(len(contours)) + " contours")

            if 20 > len(contours) > 0:

                # Filter contours
                most_beautiful_contour = None
                max_area = 0

                for cnt in contours:
                    area = cv2.contourArea(cnt, oriented=False)
                    print(area)
                    if 10000 > area > 20 and cv2.isContourConvex(cnt):
                        if area > max_area:
                            max_area = area
                            most_beautiful_contour = cnt

                if most_beautiful_contour is None:
                    continue

                # cv2.drawContours(frame, [most_beautiful_contour], -1, (255, 255, 255), thickness=2)

                # self.cv_handler.display_hsv_frame(frame)

                # Extract interesting portion of image
                newmin_x = np.min(most_beautiful_contour[:, 0, 0])
                newmax_x = np.max(most_beautiful_contour[:, 0, 0])
                newmin_y = np.min(most_beautiful_contour[:, 0, 1])
                newmax_y = np.max(most_beautiful_contour[:, 0, 1])

                d1 = abs(newmin_x - min_x)
                d2 = abs(newmin_y - min_y)
                d3 = abs(newmax_x - max_x)
                d4 = abs(newmax_y - max_y)

                if [d1, d2, d3, d4] < [State_Machine.CONVERGENCE_BOUND_THRESHOLD] * 4:
                    converged = True

                min_x = newmin_x
                max_x = newmax_x
                min_y = newmin_y
                max_y = newmax_y

                # cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (0, 255, 0), thickness=5)
                self.cv_handler.display_hsv_frame(
                    superimpose(SYMBOL_NO_ACK_REF, crop(frame, (min_x, max_x, min_y, max_y))))

        self.screen_boundaries = (min_x, max_x, min_y, max_y)
        State_Machine._compute_references_values(self)

    def _compute_references_values(self):
        dx = self.screen_boundaries[1] - self.screen_boundaries[0] + 1
        dy = self.screen_boundaries[3] - self.screen_boundaries[2] + 1

        self.SYMBOL_ONE_REF = np.full((dy, dx, 3), fill_value=S_ONE, dtype=np.uint8)
        self.SYMBOL_ZERO_REF = np.full((dy, dx, 3), fill_value=S_ZERO, dtype=np.uint8)
        self.ACK_REF = np.full((dy, dx, 3), fill_value=S_ACK, dtype=np.uint8)
        self.NO_ACK_REF = np.full((dy, dx, 3), fill_value=S_NO_ACK, dtype=np.uint8)
        self.VOID_REF = np.full((dy, dx, 3), fill_value=S_VOID, dtype=np.uint8)

    def get_masked_ack_scores(self):
        ret, frame = self.cap.readHSVFrame()
        masked_frame = frame * self.screen_mask

        ack_score = compute_score(masked_frame, self.ACK_MASK)
        no_ack_score = compute_score(masked_frame, self.NO_ACK_MASK)

        return ack_score, no_ack_score

    def get_ack_scores(self):
        ret, frame = self.cap.readHSVFrame()

        ack_score = compute_score(frame, self.ACK_REF)
        no_ack_score = compute_score(frame, self.NO_ACK_REF)

        return ack_score, no_ack_score

    def get_masked_symbols_scores(self, first_symbol, second_symbol):
        ret, frame = self.cap.readHSVFrame()
        masked_frame = frame * self.screen_mask

        first_score = compute_score(masked_frame, first_symbol)
        second_score = compute_score(masked_frame, second_symbol)

        return first_score, second_score

    def get_symbols_scores(self, first_symbol, second_symbol):
        ret, frame = self.cap.readHSVFrame()

        first_score = compute_score(frame, first_symbol)
        second_score = compute_score(frame, second_symbol)

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


    def sleep_until_next_tick(self):
        self.tick_count = self.tick_count + 1
        self.log_count = self.log_count + 1

        current_time = time.time()
        sleep_amount = (self.tick_count * State_Machine.TRANSMISSION_RATE + self.clock_start) - current_time

        if self.log_count > State_Machine.TRANSMISSION_RATE:
            self.log_count = 0
            logging.info("Going to sleep for : " + str(sleep_amount) + " seconds. Time is: " + str(current_time))

        if sleep_amount < 0:
            logging.warning("Skipping sleep time !")
            return

        time.sleep(sleep_amount)