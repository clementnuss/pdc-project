import numpy as np


class HSVBounds:
    def __init__(self, min_h: np.uint8, max_h: np.uint8, min_s: np.uint8, max_s: np.uint8,
                 min_v: np.uint8, max_v: np.uint8):
        self.values = np.array([[min_h, max_h], [min_s, max_s], [min_v, max_v]], dtype=np.uint8)

    def __str__(self) -> str:
        return 'H in [' + str(self.values[0, 0]) + ', ' + str(self.values[0, 1]) + '], S in [' + \
               str(self.values[1, 0]) + ', ' + str(self.values[1, 1]) + '], V in [' + \
               str(self.values[2, 0]) + ', ' + str(self.values[2, 1]) + ']'

    def min_bounds(self):
        return self.values[:, 0]

    def max_bounds(self):
        return self.values[:, 1]

SYNC_RANGE = HSVBounds(np.uint8(64), np.uint8(130), np.uint8(126), np.uint8(255), np.uint8(111), np.uint8(255))
