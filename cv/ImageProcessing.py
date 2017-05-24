import cv2
import numpy as np

from utils.HSVBounds import SYNC_RANGE

ERODE_KERNEL_SIZE = 5

def getMask(frame):
    processed_frame = cv2.inRange(frame, SYNC_RANGE.min_bounds(), SYNC_RANGE.max_bounds())
    # Erode and dilate the image to remove noise from the HSV filtering
    kernel = np.ones((ERODE_KERNEL_SIZE, ERODE_KERNEL_SIZE), np.uint8)
    return cv2.morphologyEx(processed_frame, cv2.MORPH_OPEN, kernel)


def compute_score(masked_frame, color_mask):
    # Convert to full size integers to perform substraction
    diff = np.int32(masked_frame) - np.int32(color_mask)
    diff = diff * diff
    return np.sum(diff)


if __name__ == '__main__':
    a1 = np.full((2, 4, 3), fill_value=[1, 2, 3])
    a2 = np.ones((4, 4, 3))

    print(a1[:, :, 0])
