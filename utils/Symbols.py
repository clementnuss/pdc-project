from utils.Constants import WIDTH, HEIGHT
from utils.HSVBounds import *

S_VOID = 0
S_NO_ACK = 15
S_ACK = 105

# Deprecated variables
S_ZERO = S_NO_ACK
S_ONE = S_ACK

S_SYNC = S_ACK

SYMBOL_ACK_REF = np.full((HEIGHT, WIDTH, 3), fill_value=[S_ACK, 255, 255], dtype=np.uint8)
SYMBOL_ZERO_REF = np.full((HEIGHT, WIDTH, 3), fill_value=[S_ZERO, 255, 255], dtype=np.uint8)
SYMBOL_NO_ACK_REF = np.full((HEIGHT, WIDTH, 3), fill_value=[S_NO_ACK, 255, 255], dtype=np.uint8)
SYMBOL_VOID_REF = np.full((HEIGHT, WIDTH, 3), fill_value=[S_VOID, 255, 255], dtype=np.uint8)

ZERO_RANGE = HSVBounds(np.uint8(0), np.uint8(30), np.uint8(125), np.uint8(255), np.uint8(150), np.uint8(255))
ONE_RANGE = HSVBounds(np.uint8(90), np.uint8(120), np.uint8(155), np.uint8(255), np.uint8(170), np.uint8(255))
ZERO_RANGE_NIGHT = HSVBounds(np.uint8(0), np.uint8(30), np.uint8(80), np.uint8(255), np.uint8(130), np.uint8(255))
ONE_RANGE_NIGHT = HSVBounds(np.uint8(90), np.uint8(120), np.uint8(200), np.uint8(255), np.uint8(200), np.uint8(255))

NUM_BITS = 3
NUM_SYMBOLS = np.power(2, NUM_BITS)
BIT_MASK = NUM_SYMBOLS - 1

SYMBOLS = np.zeros((NUM_SYMBOLS), dtype=np.uint8)


def initialize_symbols():
    hue_symbol_distance = 160.0 / NUM_SYMBOLS
    for s in range(NUM_SYMBOLS):
        SYMBOLS[s] = np.array([np.uint8(10 + hue_symbol_distance * s)])


initialize_symbols()
