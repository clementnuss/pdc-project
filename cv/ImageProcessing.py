import cv2
import numpy as np

from utils.HSVBounds import SYNC_RANGE


def getMask(frame):
    frame_thresholded = cv2.inRange(frame, SYNC_RANGE.min_bounds(), SYNC_RANGE.max_bounds())

    # Erode and dilate the image to remove noise from the HSV filtering
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(frame_thresholded, cv2.MORPH_OPEN, kernel)
