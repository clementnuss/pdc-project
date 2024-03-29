import numpy as np

WIDTH = 640
HEIGHT = 480

DETECTION_PROPORTION = 4.0

END_OF_FILE_MARKER = 26

DEBUG = True
SIMULATE = False
USE_MASK = False

NUM_BITS = 3
RS_codeword_size = 12
RS_message_size = 8
num_symbols_per_data_packet = int(np.ceil(8 * RS_codeword_size / 3))

SIMULATION_HANDLER = None
