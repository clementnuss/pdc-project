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

            # Used for akimbo mode
            self.screen_boundaries1 = None
            self.screen_boundaries2 = None
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
        frame = self.cap.readHSVFrame()
        prev_mask = getMask(frame, color_range)

        while not converged:
            frame = self.cap.readHSVFrame()
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
            frame = self.cap.readHSVFrame(True, self.name)

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

                    cntmin_x, cntmax_x, cntmin_y, cntmax_y = self._get_contour_bounds(cnt)

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
                    if 30000 > area > (4000 if Constants.SIMULATE else 400) and cv2.isContourConvex(cnt):
                        if area > max_area:
                            max_area = area
                            most_beautiful_contour = cnt
                    else:
                        print("Contour dropped because it dit not fit size requirements")

                if most_beautiful_contour is not None:
                    # cv2.drawContours(frame, [most_beautiful_contour], -1, (255, 255, 255), thickness=2)
                    # self.cv_handler.display_hsv_frame(frame)

                    # Extract interesting portion of image
                    newmin_x, newmax_x, newmin_y, newmax_y = self._get_contour_bounds(most_beautiful_contour)

                    d1, d2, d3, d4 = abs(newmin_x - min_x), abs(newmin_y - min_y), abs(newmax_x - max_x), abs(
                        newmax_y - max_y)

                    if self._within_convergence(d1, d2, d3, d4):
                        converged = True
                        cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (0, 255, 0), thickness=2)
                        cv2.imwrite("../classic_contour.jpg", frame)

                    min_x, max_x, min_y, max_y = newmin_x + 1, newmax_x, newmin_y + 1, newmax_y

        self.screen_boundaries = (min_x, max_x, min_y, max_y)

    def compute_akimbo_screen_boundaries(self, color_target):
        hue_target = color_target
        saturation_target = 255
        value_target = 255

        max_delta_hue = 20
        max_delta_saturation = 150
        max_delta_value = 45

        min_x1 = min_y1 = max_x1 = max_y1 = 0
        min_x2 = min_y2 = max_x2 = max_y2 = 0

        typical_small_contour_size = 400 if not Constants.SIMULATE else 1000

        iteration = 0
        min_iteration = 0
        max_iteration = 30

        converged = False
        contour1_converged = False
        contour2_converged = False

        while not converged:
            time.sleep(0.2)
            frame = self.cap.readHSVFrame(True, self.name)

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
            #self.cv_handler.display_frame(frame_thresholded)
            canny_frame = cv2.Canny(frame_thresholded, 50, 150, apertureSize=3)
            contoured_frame, contours0, hierarchy = cv2.findContours(canny_frame, mode=cv2.RETR_EXTERNAL,
                                                                     method=cv2.CHAIN_APPROX_SIMPLE)

            # Approximate contour by multiple straight lines
            contours = [cv2.approxPolyDP(cnt, 3, True) for cnt in contours0]

            logging.info("Got " + str(len(contours)) + " contours")

            if 10 > len(contours) > 0:

                # Filter contours
                best_contour1 = None
                best_contour2 = None
                max_area1 = 0
                max_area2 = 0

                for cnt in contours:
                    area = cv2.contourArea(cnt, oriented=False)

                    cntmin_x, cntmax_x, cntmin_y, cntmax_y = self._get_contour_bounds(cnt)

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
                    if 30000 > area > typical_small_contour_size and cv2.isContourConvex(cnt):
                        if area > max_area2:
                            if area > max_area1 and max_area2 != 0:
                                max_area1 = area
                                best_contour1 = cnt
                            else:
                                max_area2 = area
                                best_contour2 = cnt
                    else:
                        print("Contour dropped because did not fit requirements: " + str(cv2.isContourConvex(cnt)))

                if best_contour1 is not None:
                    cv2.drawContours(frame, [best_contour1], -1, (255, 255, 255), thickness=2)
                    #cv2.imshow('contoured frame', frame)

                    newmin_x, newmax_x, newmin_y, newmax_y = self._get_contour_bounds(best_contour1)

                    d1, d2, d3, d4 = abs(newmin_x - min_x1), abs(newmin_y - min_y1), abs(newmax_x - max_x1), abs(
                        newmax_y - max_y1)

                    if self._within_convergence(d1, d2, d3, d4):
                        contour1_converged = True
                        cv2.rectangle(frame, (min_x1, min_y1), (max_x1, max_y1), (0, 255, 0), thickness=2)
                        cv2.imwrite('../contour1_' + self.name + '.jpg', frame)
                        print("Contour 1 converged")
                    else:
                        contour1_converged = False
                        print("Contour 1 Not converged yet")

                    min_x1, max_x1, min_y1, max_y1 = newmin_x + 1, newmax_x, newmin_y + 1, newmax_y

                if best_contour2 is not None:
                    cv2.drawContours(frame, [best_contour2], -1, (255, 255, 255), thickness=2)
                    #cv2.imshow('contoured frame', frame)

                    newmin_x, newmax_x, newmin_y, newmax_y = self._get_contour_bounds(best_contour2)

                    d1, d2, d3, d4 = abs(newmin_x - min_x2), abs(newmin_y - min_y2), abs(newmax_x - max_x2), abs(
                        newmax_y - max_y2)

                    if self._within_convergence(d1, d2, d3, d4):
                        contour2_converged = True
                        cv2.rectangle(frame, (min_x2, min_y2), (max_x2, max_y2), (0, 0, 255), thickness=2)
                        cv2.imwrite('../contour2_' + self.name + '.jpg', frame)
                        print("Contour 2 converged")
                    else:
                        print("Contour 2 Not converged yet")
                        contour2_converged = False

                    min_x2, max_x2, min_y2, max_y2 = newmin_x + 1, newmax_x, newmin_y + 1, newmax_y

                if contour1_converged and max_area1 >= 2 * typical_small_contour_size:
                    converged = True
                    print("Screen detection converged with 1 contour")
                elif contour1_converged and contour2_converged:
                    converged = True
                    print("Screen detection converged with 2 contours")
                else:
                    converged = False

        # Only 1 big screen
        if not contour2_converged:
            # Big screen is vertical
            if (max_x1 - min_x1) < (max_y1 - min_y1):
                self.screen_boundaries1 = (min_x1, max_x1, min_y1, (min_y1 + max_y1) / 2)
                self.screen_boundaries1 = (min_x1, max_x1, (min_y1 + max_y1) / 2, max_y1)
            # Big screen is horizontal
            else:
                self.screen_boundaries1 = (min_x1, (min_x1 + max_x1) / 2, min_y1, max_y1)
                self.screen_boundaries2 = ((min_x1 + max_x1) / 2, max_x1, min_y1, max_y1)

            self.screen_boundaries2 = None

        # 2 contours in diagonal
        elif (min_x1 + max_x1) / 2.0 < (min_x2 + max_x2) / 2.0:
            self.screen_boundaries1 = (min_x1, max_x1, min_y1, max_y1)
            self.screen_boundaries2 = (min_x2, max_x2, min_y2, max_y2)
        else:
            self.screen_boundaries2 = (min_x1, max_x1, min_y1, max_y1)
            self.screen_boundaries1 = (min_x2, max_x2, min_y2, max_y2)

    def _get_contour_bounds(self, contour):
        return (
            np.min(contour[:, 0, 0]),
            np.max(contour[:, 0, 0]),
            np.min(contour[:, 0, 1]),
            np.max(contour[:, 0, 1])
        )

    def _within_convergence(self, d1, d2, d3, d4):
        return (
            d1 < State_Machine.CONVERGENCE_BOUND_THRESHOLD and
            d2 < State_Machine.CONVERGENCE_BOUND_THRESHOLD and
            d3 < State_Machine.CONVERGENCE_BOUND_THRESHOLD and
            d4 < State_Machine.CONVERGENCE_BOUND_THRESHOLD)

    def _compute_references_values(self):
        dx = self.screen_boundaries[1] - self.screen_boundaries[0] + 1
        dy = self.screen_boundaries[3] - self.screen_boundaries[2] + 1

        self.SYMBOL_ONE_REF = np.full((dy, dx, 3), fill_value=[S_ONE, 255, 255], dtype=np.uint8)
        self.SYMBOL_ZERO_REF = np.full((dy, dx, 3), fill_value=[S_ZERO, 255, 255], dtype=np.uint8)
        self.ACK_REF = np.full((dy, dx, 3), fill_value=[S_ACK, 255, 255], dtype=np.uint8)
        self.NO_ACK_REF = np.full((dy, dx, 3), fill_value=[S_NO_ACK, 255, 255], dtype=np.uint8)
        self.VOID_REF = np.full((dy, dx, 3), fill_value=[S_VOID, 0, 0], dtype=np.uint8)

    def get_masked_ack_scores(self):
        frame = self.cap.readHSVFrame()
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
        frame = self.cap.readHSVFrame()
        masked_frame = frame * self.screen_mask

        first_score = compute_score(masked_frame, first_symbol)
        second_score = compute_score(masked_frame, second_symbol)

        return first_score, second_score

    def get_symbols_scores(self, first_symbol, second_symbol):
        frame = self.cap.readHSVFrame()

        first_score = compute_score(frame, first_symbol)
        second_score = compute_score(frame, second_symbol)

        return first_score, second_score

    def get_hue_mean(self) -> np.float64:
        return self._get_mean(0)

    def get_saturation_mean(self) -> np.float64:
        return self._get_mean(1)

    def get_value_mean(self) -> np.float64:
        return self._get_mean(2)

    def _get_mean(self, i, capture=False):
        frame = self.cap.readHSVFrame()

        if Constants.DEBUG:
            cvtframe = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)
            if capture:
                cv2.imwrite("capture" + str(self.capture_count) + ".jpg", cvtframe)
                self.capture_count = self.capture_count + 1

        return frame[:, :, i].mean()

    def compute_hue_mean(self, frame) -> np.float64:
        return self._compute_mean(self, frame, 0)

    def get_cyclic_hue_mean_to_reference(self, ref):
        frame = self.cap.readHSVFrame()
        return self.compute_cyclic_hue_mean_to_reference(frame, ref)

    def compute_cyclic_hue_mean_to_reference(self, frame, ref):
        frame = self.cap.readHSVFrame()

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
