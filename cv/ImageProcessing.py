import cv2
import numpy as np

ERODE_KERNEL_SIZE = 5


def getMask(frame, color_range):
    processed_frame = cv2.inRange(frame, color_range.min_bounds(), color_range.max_bounds())
    # Erode and dilate the image to remove noise from the HSV filtering
    kernel = np.ones((ERODE_KERNEL_SIZE, ERODE_KERNEL_SIZE), np.uint8)
    return cv2.morphologyEx(processed_frame, cv2.MORPH_OPEN, kernel)


def compute_score(masked_frame, color_ref):
    if not masked_frame.shape == color_ref.shape:
        return None
    # Convert to full size integers to perform substraction
    diff = np.int32(masked_frame) - np.int32(color_ref)
    diff = diff * diff
    return np.sum(diff)


def compute_cyclic_score(value: np.uint8, reference_value: np.uint8) -> int:
    """
    Intended to be used with mean values instead of whole frames
    
    :param value: 
    :param reference_value: 
    :return: 
    """
    delta = 90 - reference_value

    adjusted_value = (np.int32(value) + delta) % 180
    diff = adjusted_value - 90
    return diff * diff

def superimpose(big_frame, small_frame):
    row, col, depth = small_frame.shape
    big_frame[0:row, 0:col, :] = small_frame

    return big_frame


def crop(frame, boundaries):
    """boundaries = [left column, right column, top row, bottom row]
    the default boundaries should then be [0, WIDTH, 0, HEIGHT]
    """
    return frame[boundaries[2]:boundaries[3] + 1, boundaries[0]:boundaries[1] + 1, :]

if __name__ == '__main__':
    a1 = np.full((4, 4, 3), fill_value=255, dtype=np.uint8)
    a2 = np.zeros((2, 2, 1), dtype=np.uint8)

    a1[0:2, 0:2, :] = a2

    print(compute_cyclic_score(np.uint8(170), np.uint8(0)))
