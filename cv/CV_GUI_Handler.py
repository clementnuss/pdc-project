import threading
import time

import cv2
import numpy as np
import scipy.misc as scm

from utils import Constants

WIDTH = 800
HEIGHT = 600
MAIN_WINDOW = 'main_window'
SECONDARY_WINDOW = 'secondary_window'


class OpenCvHandler:
    class __CV_Handler:
        def __init__(self):
            pass

        def __str__(self):
            return "OpenCV handler singleton" + repr(self)

    instance = None

    def wait_key_func(self):
        print("Initializing main window")
        cv2.namedWindow(MAIN_WINDOW, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(MAIN_WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        if Constants.SIMULATE:
            cv2.namedWindow(SECONDARY_WINDOW, cv2.WINDOW_GUI_EXPANDED | cv2.WINDOW_KEEPRATIO)
        cv2.startWindowThread()
        while True:
            if self.refresh:
                cv2.imshow(MAIN_WINDOW, self.instance.new_frame)
                self.instance.refresh = False
            if self.refresh_scnd and Constants.SIMULATE:
                cv2.imshow(SECONDARY_WINDOW, self.instance.scnd_new_frame)
                self.instance.refresh_scnd = False
            if (cv2.waitKey(1) & 0xFF) == 27:
                break
        print("Escape key pressed - terminating the GUI")
        cv2.destroyAllWindows()

    def __init__(self):
        if not OpenCvHandler.instance:
            OpenCvHandler.instance = OpenCvHandler.__CV_Handler
            self.instance.new_frame = np.full((HEIGHT, WIDTH, 3), (255, 255, 255), dtype=np.uint8)
            self.instance.scnd_new_frame = np.full((HEIGHT, WIDTH, 3), (255, 255, 255), dtype=np.uint8)
            self.instance.refresh = True
            self.instance.refresh_scnd = True
            self.instance.waiting_thread = threading.Thread(target=self.wait_key_func)
            self.instance.waiting_thread.setDaemon(True)
            self.instance.waiting_thread.start()

    def join_waiting_thread_handler(self):
        self.instance.waiting_thread.join()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def send_new_frame(self, new_frame):
        if self.instance.refresh:
            print('A frame was dropped!')
        else:
            self.instance.refresh = True
        self.instance.new_frame = new_frame

    def send_scnd_new_frame(self, new_frame):
        if self.instance.refresh_scnd:
            print('A frame was dropped!')
        else:
            self.instance.refresh_scnd = True
        self.instance.scnd_new_frame = new_frame

    def display_bgr_color(self, bgr_col):
        """Displays the given color on the whole screen"""
        color_frame = np.full((HEIGHT, WIDTH, 3), bgr_col, dtype=np.uint8)
        self.send_new_frame(color_frame)

    def display_hsv_color(self, hsv_col):
        """Converts the given color from HSV to BGR, and displays it"""
        converted_color = cv2.cvtColor(hsv_col, cv2.COLOR_HSV2BGR)
        color_frame = np.full((HEIGHT, WIDTH, 3), converted_color, dtype=np.uint8)
        self.send_new_frame(color_frame)

    def display_hsv_frame(self, hsvframe, use_interpolation=False):
        frame = hsvframe

        if use_interpolation:
            frame = scm.imresize(frame, (WIDTH, HEIGHT), interp='bilinear')

        frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)
        self.send_new_frame(frame)

    def display_frame(self, frame):
        resized_frame = scm.imresize(frame, (WIDTH, HEIGHT), interp='bilinear')
        self.send_new_frame(resized_frame)

    def display_binary_pattern(self, color_vector):
        self._display_isoquadrant_frame(self._get_binary_quadrant(color_vector[0], color_vector[1]))

    def display_quaternary_pattern(self, color_matrix):
        self._display_isoquadrant_frame(self._get_quaternary_quadrant(color_matrix))

    def display_octonary_pattern(self, color_matrices_vector,
                                 top_left, top_right, bottom_left, bottom_right):

        quadrant1 = self._get_quaternary_quadrant(color_matrices_vector[0])
        quadrant2 = self._get_quaternary_quadrant(color_matrices_vector[1])
        self._display_biquadrant_frame(quadrant1, quadrant2,
                                       top_left, top_right,
                                       bottom_left, bottom_right)

    def _display_isoquadrant_frame(self, quadrant):
        frame = np.empty((HEIGHT, WIDTH, 3), dtype=np.uint8)

        # sets up the quadrants
        frame[0: HEIGHT / 2, 0: WIDTH / 2, :] = quadrant
        frame[0: HEIGHT / 2, WIDTH / 2: WIDTH] = quadrant
        frame[HEIGHT / 2: HEIGHT, 0: WIDTH / 2, :] = quadrant
        frame[HEIGHT / 2: HEIGHT, WIDTH / 2: WIDTH, :] = quadrant

        self.display_hsv_frame(frame)

    def _display_biquadrant_frame(self, quadrant1, quadrant2, top_left, top_right, bottom_left, bottom_right):
        """
        Pattern description:
        0 - XXOO    2 - XXXX    4 - XXOO    Quadrants are distributed as follow:
            XXOO        OOOO        OOXX        - from left to right
        1 - OOXX    3 - OOOO    5 - OOXX    if on the same column:     
            OOXX        XXXX        XXOO        - from top to bottom
        """
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        if top_left and bottom_left:
            frame[0: HEIGHT / 2, 0: WIDTH / 2, :] = quadrant1  # top left quadrant
            frame[HEIGHT / 2: HEIGHT, 0: WIDTH / 2, :] = quadrant2  # bottom left quadrant

        elif top_right and bottom_right:
            frame[0: HEIGHT / 2, WIDTH / 2: WIDTH] = quadrant1  # top right quadrant
            frame[HEIGHT / 2: HEIGHT, WIDTH / 2: WIDTH, :] = quadrant2  # bottom right quadrant

        elif top_left and top_right:
            frame[0: HEIGHT / 2, 0: WIDTH / 2, :] = quadrant1  # top left quadrant
            frame[0: HEIGHT / 2, WIDTH / 2: WIDTH] = quadrant2  # top right quadrant

        elif bottom_left and bottom_right:
            frame[HEIGHT / 2: HEIGHT, 0: WIDTH / 2, :] = quadrant1  # bottom left quadrant
            frame[HEIGHT / 2: HEIGHT, WIDTH / 2: WIDTH, :] = quadrant2  # bottom right quadrant

        elif top_left and bottom_right:
            frame[0: HEIGHT / 2, 0: WIDTH / 2, :] = quadrant1  # top left quadrant
            frame[HEIGHT / 2: HEIGHT, WIDTH / 2: WIDTH, :] = quadrant2  # bottom right quadrant

        elif bottom_left and top_right:
            frame[0: HEIGHT / 2, WIDTH / 2: WIDTH] = quadrant2  # top right quadrant
            frame[HEIGHT / 2: HEIGHT, 0: WIDTH / 2, :] = quadrant1  # bottom left quadrant

        self.display_hsv_frame(frame)

    def _get_binary_quadrant(self, hsv_col1, hsv_col2):
        col1_subquadrant = np.full((HEIGHT / 2, WIDTH / 4, 3), [hsv_col1, 255, 255], dtype=np.uint8)
        col2_subquadrant = np.full((HEIGHT / 2, WIDTH / 4, 3), [hsv_col2, 255, 255], dtype=np.uint8)

        quadrant = np.empty((HEIGHT / 2, WIDTH / 2, 3), dtype=np.uint8)
        quadrant[:, 0:WIDTH / 4, :] = col1_subquadrant
        quadrant[:, WIDTH / 4:WIDTH / 2, :] = col2_subquadrant

        return quadrant

    def _get_quaternary_quadrant(self, color_matrix):
        col1_subquadrant = np.full((HEIGHT / 4, WIDTH / 4, 3), [color_matrix[0, 0], 255, 255], dtype=np.uint8)
        col2_subquadrant = np.full((HEIGHT / 4, WIDTH / 4, 3), [color_matrix[0, 1], 255, 255], dtype=np.uint8)
        col3_subquadrant = np.full((HEIGHT / 4, WIDTH / 4, 3), [color_matrix[1, 0], 255, 255], dtype=np.uint8)
        col4_subquadrant = np.full((HEIGHT / 4, WIDTH / 4, 3), [color_matrix[1, 1], 255, 255], dtype=np.uint8)

        quadrant = np.empty((HEIGHT / 2, WIDTH / 2, 3), dtype=np.uint8)

        quadrant[0: HEIGHT / 4, 0: WIDTH / 4, :] = col1_subquadrant
        quadrant[0: HEIGHT / 4, WIDTH / 4: WIDTH] = col2_subquadrant
        quadrant[HEIGHT / 4: HEIGHT, 0: WIDTH / 4, :] = col3_subquadrant
        quadrant[HEIGHT / 4: HEIGHT, WIDTH / 4: WIDTH, :] = col4_subquadrant

        return quadrant


if __name__ == '__main__':
    test = np.zeros((1, 1, 3))
    print(test)
    sampleHandler = OpenCvHandler()
    sampleHandler.display_binary_pattern([15, 105])
    time.sleep(2)
    sampleHandler.display_quaternary_pattern(np.array([[15, 45], [80, 105]]))
    time.sleep(2)
    sampleHandler.display_octonary_pattern(np.array([
        [[10, 20], [30, 40]],
        [[50, 60], [70, 80]]]),
        1, 1,
        0, 0
    )
    # print(timeit.timeit(quatpat_wrapper, number=1))
    sampleHandler.join_waiting_thread_handler()
