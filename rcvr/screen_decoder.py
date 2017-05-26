import time

import cv2
import numpy as np

import cv.CV_Video_Capture_Handler
from utils.Constants import *

TRACKBAR_WINDOW = 'trackbars'

cap = cv.CV_Video_Capture_Handler.CV_Video_Capture_Handler()


def nothing(val):
    return


def create_trackbar(name, min, max):
    cv2.createTrackbar(name, TRACKBAR_WINDOW, min, max, nothing)


def get_trackbar_value(name):
    return cv2.getTrackbarPos(name, TRACKBAR_WINDOW)


def initialize_gui():
    cv2.namedWindow(TRACKBAR_WINDOW, cv2.WINDOW_AUTOSIZE)
    create_trackbar('H_min', 0, 180)
    create_trackbar('H_max', 0, 180)
    cv2.setTrackbarPos('H_max', TRACKBAR_WINDOW, 180)
    create_trackbar('S_min', 0, 255)
    create_trackbar('S_max', 0, 255)
    cv2.setTrackbarPos('S_max', TRACKBAR_WINDOW, 255)
    create_trackbar('V_min', 0, 255)
    create_trackbar('V_max', 0, 255)
    cv2.setTrackbarPos('V_max', TRACKBAR_WINDOW, 255)
    create_trackbar('Canny_tres0', 0, 255)
    create_trackbar('Canny_tres1', 0, 255)

    cv2.resizeWindow(TRACKBAR_WINDOW, 400, 300)


def getCameraSnapshot():
    return cap.read()


def displayFrame(frame):
    cv2.imshow("OpenCV", frame)
    cv2.waitKey(1)


def get_min_hsv():
    return [get_trackbar_value('H_min'), get_trackbar_value('S_min'), get_trackbar_value('V_min')]


def get_max_hsv():
    return [get_trackbar_value('H_max'), get_trackbar_value('S_max'), get_trackbar_value('V_max')]


def main():
    while True:
        # Capture frame-by-frame
        ret, frame = cap.readFrame()

        # Display the resulting frame
        hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        cv2.imshow('hsv', hsv_img)

        min_hsv = np.array(get_min_hsv(), np.uint8)
        max_hsv = np.array(get_max_hsv(), np.uint8)
        frame_thresholded = cv2.inRange(hsv_img, min_hsv, max_hsv)

        # We erode and dilate the image to remove noise from the HSV filtering More info here:
        # http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_morphological_ops/py_morphological_ops.html
        kernel = np.ones((5, 5), np.uint8)
        frame_thresholded = cv2.morphologyEx(frame_thresholded, cv2.MORPH_OPEN, kernel)
        cv2.imshow('hsv_thresholded', frame_thresholded)

        edges = cv2.Canny(frame_thresholded, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.imshow('original', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def smooth_step(x, edge0, edge1):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t)

def main_contour():
    hue_target = 15
    saturation_target = 255
    value_target = 255

    max_delta_hue = 20
    max_delta_saturation = 130
    max_delta_value = 130

    min_x = min_y = max_x = max_y = 0

    iteration = 0
    min_iteration = 0
    max_iteration = 30

    manual = True

    converged = False
    kernel = np.ones((7, 7), np.uint8)

    while not converged:
        time.sleep(0.1)

        ret, frame = cap.readHSVFrame()

        hue_delta_coeff = smooth_step(2.0 * iteration, min_iteration, max_iteration)
        delta_coeff = smooth_step(iteration, min_iteration, max_iteration)
        iteration = iteration + 1

        min_hsv = (hue_target - hue_delta_coeff * max_delta_hue,
                   saturation_target - delta_coeff * max_delta_saturation,
                   value_target - delta_coeff * max_delta_value)

        max_hsv = (hue_target + hue_delta_coeff * max_delta_hue,
                   saturation_target,
                   value_target)

        canny0 = 50
        canny1 = 150

        if manual:
            min_hsv = np.array(get_min_hsv(), np.uint8)
            max_hsv = np.array(get_max_hsv(), np.uint8)
            canny0 = get_trackbar_value('Canny_tres0')
            canny1 = get_trackbar_value('Canny_tres1')
            print(canny0)
            print(canny1)

        print("Iteration with min: " + str(min_hsv) + " and max: " + str(max_hsv))
        frame_thresholded = cv2.inRange(frame, min_hsv, max_hsv)
        frame_thresholded = cv2.morphologyEx(frame_thresholded, cv2.MORPH_OPEN, kernel)
        cv2.imshow('hsv_thresholded', frame_thresholded)
        canny_frame = cv2.Canny(frame_thresholded, canny0, canny1, apertureSize=3)
        cv2.imshow('canny result', canny_frame)
        contoured_frame, contours0, hierarchy = cv2.findContours(canny_frame, mode=cv2.RETR_EXTERNAL,
                                                                 method=cv2.CHAIN_APPROX_SIMPLE)
        contours = [cv2.approxPolyDP(cnt, 3, True) for cnt in contours0]

        if len(contours) < 10 and len(contours) > 0:

            print("Got " + str(len(contours)) + " contours")
            # Filter contours

            most_beautiful_contour = None
            max_area = 0

            for cnt in contours:
                area = cv2.contourArea(cnt, oriented=False)

                cntmin_x = np.min(cnt[:, 0, 0])
                cntmax_x = np.max(cnt[:, 0, 0])
                cntmin_y = np.min(cnt[:, 0, 1])
                cntmax_y = np.max(cnt[:, 0, 1])

                if (cntmin_x < WIDTH / DETECTION_PROPORTION or
                            cntmin_y < HEIGHT / DETECTION_PROPORTION or
                            cntmax_x > (WIDTH - WIDTH / DETECTION_PROPORTION) or
                            cntmax_y > (HEIGHT - HEIGHT / DETECTION_PROPORTION)):
                    print("Skipping contour, out of bounds")
                    continue

                print(area)

                if 30000 > area > 500 and cv2.isContourConvex(cnt):
                    if area > max_area:
                        max_area = area
                        most_beautiful_contour = cnt

            if most_beautiful_contour is not None:
                cv2.drawContours(frame, [most_beautiful_contour], -1, (255, 255, 255), thickness=2)
                cv2.imshow('contoured frame', frame)

                newmin_x = np.min(most_beautiful_contour[:, 0, 0])
                newmax_x = np.max(most_beautiful_contour[:, 0, 0])
                newmin_y = np.min(most_beautiful_contour[:, 0, 1])
                newmax_y = np.max(most_beautiful_contour[:, 0, 1])

                d1 = abs(newmin_x - min_x)
                d2 = abs(newmin_y - min_y)
                d3 = abs(newmax_x - max_x)
                d4 = abs(newmax_y - max_y)

                if [d1, d2, d3, d4] < [10] * 4:
                    if not manual:
                        converged = True
                    cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (0, 255, 0), thickness=2)
                    cv2.imshow('bounded frame', frame)
                else:
                    print("Not converged yet")

                min_x = newmin_x + 1
                max_x = newmax_x
                min_y = newmin_y + 1
                max_y = newmax_y



        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def pass_through():
    frame_time = 0
    last_frame_time = 0
    frame_count = 0
    while 1:
        last_frame_time = time.time()
        ret, frame = cap.readFrame()
        frame_time = time.time()

        frame_count = frame_count + 1

        if frame_count > 60:
            fps = 1.0 / (frame_time - last_frame_time)
            print("fps: ", fps)
            frame_count = 0

        cv_handler.send_new_frame(frame)


if __name__ == '__main__':
    time.sleep(0.5)
    # pass_through()
    initialize_gui()
    main_contour()

    # When everything done, release the capture
    input("Press Enter")
    # cap.release()
    # cv2.destroyAllWindows()
