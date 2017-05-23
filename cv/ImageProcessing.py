import cv2
import numpy as np

ERODE_KERNEL_SIZE = 5

def getMask(frame):
    processed_frame = frame
    # processed_frame = cv2.inRange(frame, SYNC_RANGE.min_bounds(), SYNC_RANGE.max_bounds())
    processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2GRAY)
    processed_frame = np.round(processed_frame / 255.0, 0)
    # Erode and dilate the image to remove noise from the HSV filtering
    kernel = np.ones((ERODE_KERNEL_SIZE, ERODE_KERNEL_SIZE), np.uint8)
    return cv2.morphologyEx(processed_frame, cv2.MORPH_OPEN, kernel)
