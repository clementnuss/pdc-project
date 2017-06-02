from random import randrange

import numpy as np

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Duplicate of the constants in CV_GUI_Handler !
WIDTH = 800
HEIGHT = 600

DETECTION_PROPORTION = 4.0

END_OF_FILE_MARKER = 26

FAKE_MASK = False
MASK_PATTERN = randrange(0, 6)

DEBUG = False
SIMULATE = False
USE_MASK = False
USE_AKIMBO_SCREEN = True
WRITE_IMAGE = True
SCREEN_DETECTION_MARGIN = 4

SIMULATION_HANDLER = None

PIXEL_MARGIN = 7
PIXEL_MARGIN_PER_QUADRANT = 0

NUM_QUADRANTS = 2

SPEED = 2
if SPEED == 0:
    RS_codeword_size = 72
    # with this setup we can correct for 10 missed frames
    RS_message_size = 49

    NUM_HORIZONTAL_CELLS = 1
    NUM_VERTICAL_CELLS = 1

if SPEED == 1:
    RS_codeword_size = 72
    # with this setup we can correct for 10 missed frames
    RS_message_size = 49

    NUM_HORIZONTAL_CELLS = 2
    NUM_VERTICAL_CELLS = 1
elif SPEED == 2:
    RS_codeword_size = 144
    # with this setup we can correct for 10 missed frames
    RS_message_size = 98

    NUM_HORIZONTAL_CELLS = 3
    NUM_VERTICAL_CELLS = 2

NUM_CELLS_PER_QUADRANT = NUM_HORIZONTAL_CELLS * NUM_VERTICAL_CELLS
NUM_BITS_PER_COLOR = 3
NUM_BITS_PER_QUADRANT = NUM_BITS_PER_COLOR * NUM_CELLS_PER_QUADRANT
NUM_BITS_PER_SYMBOL = NUM_QUADRANTS * NUM_BITS_PER_QUADRANT

NUM_SYMBOLS_PER_DATA_PACKET = int(np.ceil(8 * RS_codeword_size / NUM_BITS_PER_SYMBOL))

QUADRANT_WIDTH = int(WIDTH / 2)
QUADRANT_HEIGHT = int(HEIGHT / 2)
CELL_WIDTH = int((QUADRANT_WIDTH - 2 * PIXEL_MARGIN_PER_QUADRANT) / NUM_HORIZONTAL_CELLS)
CELL_HEIGHT = int((QUADRANT_HEIGHT - 2 * PIXEL_MARGIN_PER_QUADRANT) / NUM_VERTICAL_CELLS)
QUADRANT_HORIZONTAL_CELL_START = [PIXEL_MARGIN_PER_QUADRANT + CELL_WIDTH * i for i in range(0, NUM_HORIZONTAL_CELLS)]
QUADRANT_VERTICAL_CELL_START = [PIXEL_MARGIN_PER_QUADRANT + CELL_HEIGHT * i for i in range(0, NUM_VERTICAL_CELLS)]
