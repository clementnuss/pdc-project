from utils.Constants import WIDTH, HEIGHT
from utils.HSVBounds import *

S_VOID = np.array([[[np.uint8(0), np.uint8(0), np.uint8(0)]]])
S_ZERO = np.array([[[np.uint8(15), np.uint8(255), np.uint8(255)]]])
S_ONE = np.array([[[np.uint8(105), np.uint8(255), np.uint8(255)]]])

S_SYNC = S_ZERO

S_ACK = S_ONE
S_NO_ACK = S_ZERO

SYMBOL_ACK_MASK = np.full((HEIGHT, WIDTH, 3), fill_value=S_ACK, dtype=np.uint8)
SYMBOL_NO_ACK_MASK = np.full((HEIGHT, WIDTH, 3), fill_value=S_NO_ACK, dtype=np.uint8)

ZERO_RANGE = HSVBounds(np.uint8(0), np.uint8(30), np.uint8(50), np.uint8(255), np.uint8(200), np.uint8(255))
ONE_RANGE = HSVBounds(np.uint8(90), np.uint8(120), np.uint8(100), np.uint8(255), np.uint8(200), np.uint8(255))
