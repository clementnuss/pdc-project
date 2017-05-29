import logging
import math
import time

import cv.CV_GUI_Handler
import cv.CV_Video_Capture_Handler
from cv.ImageProcessing import *
from utils import Constants
from utils.Symbols import *


class State_Machine(object):
    TRANSMISSION_RATE = 1.0 / 10.0
    SAMPLING_OFFSET = 1.0 / 30.0
    CONVERGENCE_BOUND_THRESHOLD = 15
    CONVERGENCE_THRESHOLD = 10000
    BLACK_THRESHOLD = 200000

    def __init__(self):
        self.clock_start = -1
        self.tick_count = 0
        self.log_count = 0
        self.capture_count = 0

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

    def compute_screen_boundaries(self, color_target):
        hue_target = color_target
        saturation_target = 255
        value_target = 255

        max_delta_hue = 20
        max_delta_saturation = 130
        max_delta_value = 130

        min_x = min_y = max_x = max_y = 0

        iteration = 0
        min_iteration = 0
        max_iteration = 30

        converged = False

        while not converged:
            time.sleep(0.2)
            ret, frame = self.cap.readHSVFrame()

            hue_delta_coeff = smooth_step(2.0 * iteration, min_iteration, max_iteration)
            delta_coeff = smooth_step(iteration, min_iteration, max_iteration)
            iteration = iteration + 1

            min_hsv = np.array([u8clamp(hue_target - hue_delta_coeff * max_delta_hue),
                                u8clamp(saturation_target - delta_coeff * max_delta_saturation),
                                u8clamp(value_target - delta_coeff * max_delta_value)])

            max_hsv = np.array([u8clamp(hue_target + hue_delta_coeff * max_delta_hue),
                                u8clamp(saturation_target),
                                u8clamp(value_target)])

            logging.info("Iteration with min: " + str(min_hsv) + " and max: " + str(max_hsv))

            frame_thresholded = getMask(frame, min_hsv, max_hsv)
            # self.cv_handler.display_frame(frame_thresholded)
            canny_frame = cv2.Canny(frame_thresholded, 50, 150, apertureSize=3)
            contoured_frame, contours0, hierarchy = cv2.findContours(canny_frame, mode=cv2.RETR_EXTERNAL,
                                                                     method=cv2.CHAIN_APPROX_SIMPLE)

            # Approximate contour by multiple straight lines
            contours = [cv2.approxPolyDP(cnt, 3, True) for cnt in contours0]

            logging.info("Got " + str(len(contours)) + " contours")

            if 10 > len(contours) > 0:

                # Filter contours
                most_beautiful_contour = None
                max_area = 0

                for cnt in contours:
                    area = cv2.contourArea(cnt, oriented=False)

                    cntmin_x = np.min(cnt[:, 0, 0])
                    cntmax_x = np.max(cnt[:, 0, 0])
                    cntmin_y = np.min(cnt[:, 0, 1])
                    cntmax_y = np.max(cnt[:, 0, 1])

                    from utils.Constants import DETECTION_PROPORTION
                    if Constants.SIMULATE:
                        DETECTION_PROPORTION = 200
                    if (cntmin_x < WIDTH / DETECTION_PROPORTION or
                                cntmin_y < HEIGHT / DETECTION_PROPORTION or
                                cntmax_x > (WIDTH - WIDTH / DETECTION_PROPORTION) or
                                cntmax_y > (HEIGHT - HEIGHT / DETECTION_PROPORTION)):
                        print("Skipping contour, out of bounds")
                        continue

                    print("Contour area: " + str(area))
                    if 30000 > area > (30 if Constants.SIMULATE else 400) and cv2.isContourConvex(cnt):
                        if area > max_area:
                            max_area = area
                            most_beautiful_contour = cnt

                if most_beautiful_contour is not None:
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
                        cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (0, 255, 0), thickness=2)
                        cv2.imwrite("../captured.jpg", frame)

                    min_x = newmin_x + 1
                    max_x = newmax_x
                    min_y = newmin_y + 1
                    max_y = newmax_y

        self.screen_boundaries = (min_x, max_x, min_y, max_y)
        State_Machine._compute_references_values(self)

    def _compute_references_values(self):
        dx = self.screen_boundaries[1] - self.screen_boundaries[0] + 1
        dy = self.screen_boundaries[3] - self.screen_boundaries[2] + 1

        self.SYMBOL_ONE_REF = np.full((dy, dx, 3), fill_value=[S_ONE, 255, 255], dtype=np.uint8)
        self.SYMBOL_ZERO_REF = np.full((dy, dx, 3), fill_value=[S_ZERO, 255, 255], dtype=np.uint8)
        self.ACK_REF = np.full((dy, dx, 3), fill_value=[S_ACK, 255, 255], dtype=np.uint8)
        self.NO_ACK_REF = np.full((dy, dx, 3), fill_value=[S_NO_ACK, 255, 255], dtype=np.uint8)
        self.VOID_REF = np.full((dy, dx, 3), fill_value=[S_VOID, 0, 0], dtype=np.uint8)

    def get_masked_ack_scores(self):
        ret, frame = self.cap.readHSVFrame()
        masked_frame = frame * self.screen_mask

        ack_score = compute_score(masked_frame, self.ACK_MASK)
        no_ack_score = compute_score(masked_frame, self.NO_ACK_MASK)

        return ack_score, no_ack_score

    def get_ack_scores(self):
        hue_mean = self.get_hue_mean()
        logging.info("Hue mean for ack score computation is: " + str(hue_mean))
        ack_score = compute_cyclic_score(hue_mean, np.float64(S_ACK))
        no_ack_score = compute_cyclic_score(hue_mean, np.float64(S_NO_ACK))

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

    def get_hue_mean(self) -> np.float64:
        return self._get_mean(0)

    def get_saturation_mean(self) -> np.float64:
        return self._get_mean(1)

    def get_value_mean(self) -> np.float64:
        return self._get_mean(2)

    def _get_mean(self, i):
        ret, frame = self.cap.readHSVFrame()

        if Constants.DEBUG:
            cvtframe = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)
            cv2.imwrite("capture" + str(self.capture_count) + ".jpg", cvtframe)
            self.capture_count = self.capture_count + 1

        return frame[:, :, i].mean()

    def compute_hue_mean(self, frame) -> np.float64:
        return self._compute_mean(self, frame, 0)

    def get_cyclic_hue_mean_to_reference(self, ref):
        ret, frame = self.cap.readHSVFrame()
        return self.compute_cyclic_hue_mean_to_reference(frame, ref)

    def compute_cyclic_hue_mean_to_reference(self, frame, ref):
        ret, frame = self.cap.readHSVFrame()

        delta = 90 - ref

        adjusted_frame = (np.int32(frame[:, :, 0]) + delta) % 180

        return np.float64(adjusted_frame.mean() - 90 + ref) % np.float64(180)

    def compute_cyclic_hue_frame_score(self, frame, reference_value: np.float64) -> int:

        delta = np.float64(90) - reference_value

        adjusted_frame = (np.float64(frame) + delta) % np.float64(180)
        diff = np.sum(adjusted_frame - np.float64(90))

        return diff * diff

    def compute_saturation_mean(self, frame) -> np.float64:
        return self._compute_mean(self, frame, 1)

    def compute_value_mean(self, frame) -> np.float64:
        return self._compute_mean(self, frame, 2)

    def _compute_mean(self, frame, i):
        return frame[:, :, i].mean()

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
