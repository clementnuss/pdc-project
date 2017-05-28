import cv2
import numpy as np

ERODE_KERNEL_SIZE = 5


def u8clamp(x) -> np.uint8:
    return np.uint8(max(0, min(255, x)))


def smooth_step(x, edge0, edge1):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);


def getMask_with_hsvrange(frame, color_range):
    processed_frame = cv2.inRange(frame, color_range.min_bounds(), color_range.max_bounds())
    # Erode and dilate the image to remove noise from the HSV filtering
    kernel = np.ones((ERODE_KERNEL_SIZE, ERODE_KERNEL_SIZE), np.uint8)
    return cv2.morphologyEx(processed_frame, cv2.MORPH_OPEN, kernel)


def getMask(frame, min_range, max_range):
    processed_frame = cv2.inRange(frame, min_range, max_range)
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


def compute_cyclic_score(value: np.float64, reference_value: np.float64) -> int:
    """
    Intended to be used with mean values instead of whole frames
    
    :param value: 
    :param reference_value: 
    :return: 
    """
    delta = np.float64(90) - reference_value

    adjusted_value = (value + delta) % np.float64(180)
    diff = adjusted_value - np.float64(90)
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
    print(np.float64(180.1) % np.float64(180))
    print(compute_cyclic_score(np.uint8(170), np.uint8(0)))
