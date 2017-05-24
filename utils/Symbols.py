import numpy as np

S_VOID = np.array([[[np.uint8(0), np.uint8(0), np.uint8(0)]]])
S_ZERO = np.array([[[np.uint8(180), np.uint8(255), np.uint8(255)]]])
S_ONE = np.array([[[np.uint8(90), np.uint8(255), np.uint8(255)]]])

S_SYNC = np.array([[[np.uint8(60), np.uint8(100), np.uint8(100)]]])

S_ACK = S_ONE
S_NO_ACK = S_ZERO
