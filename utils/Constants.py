import numpy as np

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

DETECTION_PROPORTION = 4.0

END_OF_FILE_MARKER = 26

DEBUG = True
SIMULATE = False
USE_MASK = False
USE_AKIMBO_SCREEN = True
WRITE_IMAGE = True


NUM_CELLS_PER_QUADRANT = 6
NUM_BITS_PER_COLOR = 3
NUM_BITS_PER_QUADRANT = NUM_BITS_PER_COLOR * NUM_CELLS_PER_QUADRANT
NUM_BITS_PER_SYMBOL = 2 * NUM_BITS_PER_QUADRANT

RS_codeword_size = 144
# with this setup we can correct for 5 missed frames
RS_message_size = 98

NUM_SYMBOLS_PER_DATA_PACKET = int(np.ceil(8 * RS_codeword_size / NUM_BITS_PER_SYMBOL))

SIMULATION_HANDLER = None


