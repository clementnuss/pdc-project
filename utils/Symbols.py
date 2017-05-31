from utils.Constants import CAMERA_WIDTH, CAMERA_HEIGHT, NUM_BITS_PER_COLOR
from utils.HSVBounds import *

S_VOID = 0
S_NO_ACK = 15
S_ACK = 105

# Deprecated variables
S_ZERO = S_NO_ACK
S_ONE = S_ACK

S_SYNC = S_ACK

SYMBOL_ACK_REF = np.full((CAMERA_HEIGHT, CAMERA_WIDTH, 3), fill_value=[S_ACK, 255, 255], dtype=np.uint8)
SYMBOL_ZERO_REF = np.full((CAMERA_HEIGHT, CAMERA_WIDTH, 3), fill_value=[S_ZERO, 255, 255], dtype=np.uint8)
SYMBOL_NO_ACK_REF = np.full((CAMERA_HEIGHT, CAMERA_WIDTH, 3), fill_value=[S_NO_ACK, 255, 255], dtype=np.uint8)
SYMBOL_VOID_REF = np.full((CAMERA_HEIGHT, CAMERA_WIDTH, 3), fill_value=[S_VOID, 255, 255], dtype=np.uint8)

ZERO_RANGE = HSVBounds(np.uint8(0), np.uint8(30), np.uint8(125), np.uint8(255), np.uint8(150), np.uint8(255))
ONE_RANGE = HSVBounds(np.uint8(90), np.uint8(120), np.uint8(155), np.uint8(255), np.uint8(170), np.uint8(255))
ZERO_RANGE_NIGHT = HSVBounds(np.uint8(0), np.uint8(30), np.uint8(80), np.uint8(255), np.uint8(130), np.uint8(255))
ONE_RANGE_NIGHT = HSVBounds(np.uint8(90), np.uint8(120), np.uint8(200), np.uint8(255), np.uint8(200), np.uint8(255))

NUM_SYMBOLS = np.power(2, NUM_BITS_PER_COLOR)
BIT_MASK = NUM_SYMBOLS - 1

SYMBOLS = np.zeros((NUM_SYMBOLS), dtype=np.uint8)

SYMBOLS[0] = np.uint8(10)
SYMBOLS[1] = np.uint8(20)
SYMBOLS[2] = np.uint8(30)
SYMBOLS[3] = np.uint8(50)
SYMBOLS[4] = np.uint8(80)
SYMBOLS[5] = np.uint8(110)
SYMBOLS[6] = np.uint8(140)
SYMBOLS[7] = np.uint8(170)

FEEDBACK_SYMBOLS = np.zeros((4), dtype=np.uint8)

FEEDBACK_SYMBOLS[0] = np.uint(10)
FEEDBACK_SYMBOLS[1] = np.uint()
FEEDBACK_SYMBOLS[2]
FEEDBACK_SYMBOLS[3]
