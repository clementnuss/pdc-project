import time

import cv2

import cv.CV_GUI_Handler
from utils.Constants import *

TRACKBAR_WINDOW = 'trackbars'

cap = cv.CV_Video_Capture_Handler.CV_Video_Capture_Handler()
cv_handler = cv.CV_GUI_Handler.OpenCvHandler()


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
        frame = cap.readFrame()

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
    hue_target = 105
    saturation_target = 255
    value_target = 255

    max_delta_hue = 20
    max_delta_saturation = 100
    max_delta_value = 40

    min_x1 = min_y1 = max_x1 = max_y1 = 0
    min_x2 = min_y2 = max_x2 = max_y2 = 0

    delta_screen_bounds = 10
    typical_small_countour_size = 400

    iteration = 0
    min_iteration = 0
    max_iteration = 30

    manual = True

    converged = False
    contour1_converged = False
    contour2_converged = False

    kernel = np.ones((5, 5), np.uint8)

    while not converged:
        time.sleep(0.2)

        frame = cap.readHSVFrame()

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

            best_contour1 = None
            best_contour2 = None
            max_area1 = 0
            max_area2 = 0

            for cnt in contours:
                area = cv2.contourArea(cnt, oriented=False)

                cntmin_x, cntmax_x, cntmin_y, cntmax_y = _get_contour_bounds(cnt)

                if (cntmin_x < WIDTH / DETECTION_PROPORTION or
                            cntmin_y < HEIGHT / DETECTION_PROPORTION or
                            cntmax_x > (WIDTH - WIDTH / DETECTION_PROPORTION) or
                            cntmax_y > (HEIGHT - HEIGHT / DETECTION_PROPORTION)):
                    print("Skipping contour, out of bounds")
                    continue

                print(area)

                if 30000 > area > typical_small_countour_size and cv2.isContourConvex(cnt):
                    if area > max_area2:
                        if area > max_area1:
                            max_area1 = area
                            best_contour1 = cnt
                        else:
                            max_area2 = area
                            best_contour2 = cnt

            if best_contour1 is not None:
                cv2.drawContours(frame, [best_contour1], -1, (255, 255, 255), thickness=2)
                cv2.imshow('contoured frame', frame)

                newmin_x, newmax_x, newmin_y, newmax_y = _get_contour_bounds(best_contour1)

                d1, d2, d3, d4 = abs(newmin_x - min_x1), abs(newmin_y - min_y1), abs(newmax_x - max_x1), abs(
                    newmax_y - max_y1)

                if [d1, d2, d3, d4] < [20] * 4:
                    if not manual:
                        contour1_converged = True
                    cv2.rectangle(frame, (min_x1, min_y1), (max_x1, max_y1), (0, 255, 0), thickness=2)
                    cv2.imshow('bounded frame', frame)
                    print("Contour 1 converged")
                else:
                    contour1_converged = False
                    print("Contour 1 Not converged yet")

                min_x1, max_x1, min_y1, max_y1 = newmin_x + 1, newmax_x, newmin_y + 1, newmax_y

            if best_contour2 is not None:
                cv2.drawContours(frame, [best_contour2], -1, (255, 255, 255), thickness=2)
                cv2.imshow('contoured frame', frame)

                newmin_x, newmax_x, newmin_y, newmax_y = _get_contour_bounds(best_contour2)

                d1, d2, d3, d4 = abs(newmin_x - min_x2), abs(newmin_y - min_y2), abs(newmax_x - max_x2), abs(
                    newmax_y - max_y2)

                if [d1, d2, d3, d4] < [10] * 4:
                    if not manual:
                        contour2_converged = True
                    cv2.rectangle(frame, (min_x2, min_y2), (max_x2, max_y2), (0, 0, 255), thickness=2)
                    cv2.imshow('bounded frame', frame)
                    print("Contour 2 converged")
                else:
                    print("Contour 2 Not converged yet")
                    contour2_converged = False

                min_x2, max_x2, min_y2, max_y2 = newmin_x + 1, newmax_x, newmin_y + 1, newmax_y

            if contour1_converged and max_area1 >= 2.0 * typical_small_countour_size:
                converged = True
                print("Screen detection converged with 1 contour")
            elif contour1_converged and contour2_converged:
                converged = True
                print("Screen detection converged with 2 contours")
            else:
                converged = False

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def _get_contour_bounds(contour):
    return (
        np.min(contour[:, 0, 0]),
        np.max(contour[:, 0, 0]),
        np.min(contour[:, 0, 1]),
        np.max(contour[:, 0, 1])
    )


def pass_through():
    frame_time = 0
    last_frame_time = 0
    frame_count = 0
    while 1:
        last_frame_time = time.time()
        frame = cap.readHSVFrame()
        frame_time = time.time()

        frame_count = frame_count + 1

        if frame_count > 60:
            fps = 1.0 / (frame_time - last_frame_time)
            print("fps: ", fps)
            frame_count = 0

        cv_handler.display_hsv_frame(frame)


if __name__ == '__main__':
    time.sleep(0.5)
    # pass_through()
    initialize_gui()
    main_contour()

    # When everything done, release the capture
    input("Press Enter")
    # cap.release()
    # cv2.destroyAllWindows()
