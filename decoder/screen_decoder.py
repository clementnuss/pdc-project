import cv2
import numpy as np

TRACKBAR_WINDOW = 'trackbars'

cap = cv2.VideoCapture(0)


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
    cv2.resizeWindow(TRACKBAR_WINDOW, 400, 300)


def get_min_hsv():
    return [get_trackbar_value('H_min'), get_trackbar_value('S_min'), get_trackbar_value('V_min')]


def get_max_hsv():
    return [get_trackbar_value('H_max'), get_trackbar_value('S_max'), get_trackbar_value('V_max')]


def main():
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Display the resulting frame

        cv2.imshow('original', frame)

        hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        cv2.imshow('hsv', hsv_img)

        min_hsv = np.array(get_min_hsv(), np.uint8)
        max_hsv = np.array(get_max_hsv(), np.uint8)
        frame_threshed = cv2.inRange(hsv_img, min_hsv, max_hsv)

        cv2.imshow('hsv_thresholded', frame_threshed)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


initialize_gui()
main()

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
