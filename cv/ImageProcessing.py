import cv2
import numpy as np

from utils.HSVBounds import SYNC_RANGE

ERODE_KERNEL_SIZE = 5

def getMask(frame):
    processed_frame = cv2.inRange(frame, SYNC_RANGE.min_bounds(), SYNC_RANGE.max_bounds())
    # Erode and dilate the image to remove noise from the HSV filtering
    kernel = np.ones((ERODE_KERNEL_SIZE, ERODE_KERNEL_SIZE), np.uint8)
    return cv2.morphologyEx(processed_frame, cv2.MORPH_OPEN, kernel)
