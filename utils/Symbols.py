from utils.Constants import WIDTH, HEIGHT
from utils.HSVBounds import *

S_VOID = np.array([[[np.uint8(0), np.uint8(0), np.uint8(0)]]])
S_ZERO = np.array([[[np.uint8(15), np.uint8(255), np.uint8(255)]]])
S_ONE = np.array([[[np.uint8(105), np.uint8(255), np.uint8(255)]]])

S_SYNC = S_ZERO

S_ACK = S_ONE
S_NO_ACK = S_ZERO

SYMBOL_ONE_REF = np.full((HEIGHT, WIDTH, 3), fill_value=S_ONE, dtype=np.uint8)
SYMBOL_ACK_REF = np.full((HEIGHT, WIDTH, 3), fill_value=S_ACK, dtype=np.uint8)
SYMBOL_ZERO_REF = np.full((HEIGHT, WIDTH, 3), fill_value=S_ZERO, dtype=np.uint8)
SYMBOL_NO_ACK_REF = np.full((HEIGHT, WIDTH, 3), fill_value=S_NO_ACK, dtype=np.uint8)
SYMBOL_VOID_REF = np.full((HEIGHT, WIDTH, 3), fill_value=S_VOID, dtype=np.uint8)

ZERO_RANGE = HSVBounds(np.uint8(0), np.uint8(30), np.uint8(150), np.uint8(255), np.uint8(140), np.uint8(255))
ONE_RANGE = HSVBounds(np.uint8(90), np.uint8(120), np.uint8(200), np.uint8(255), np.uint8(120), np.uint8(255))
ZERO_RANGE_NIGHT = HSVBounds(np.uint8(0), np.uint8(30), np.uint8(80), np.uint8(255), np.uint8(200), np.uint8(255))
ONE_RANGE_NIGHT = HSVBounds(np.uint8(90), np.uint8(120), np.uint8(200), np.uint8(255), np.uint8(200), np.uint8(255))

NUM_BITS = 4
NUM_SYMBOLS = np.power(2, NUM_BITS)

SYMBOLS = np.zeros((NUM_SYMBOLS, 3), dtype=np.uint8)


def initialize_symbols():
    hue_symbol_distance = 180.0 / NUM_SYMBOLS
    for i in range(NUM_SYMBOLS):
        SYMBOLS[i] = np.array([[[hue_symbol_distance * i, np.uint8(255), np.uint8(255)]]])


initialize_symbols()
