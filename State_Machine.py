import logging
import math
import time

import numpy as np


class State_Machine(object):
    TRANSMISSION_RATE = 1.0 / 10.0
    SAMPLING_OFFSET = TRANSMISSION_RATE / 2.0

    def __init__(self):
        self.clock_start = -1
        self.tick_count = 0

    def _align_clock(self):
        curr_time = time.time()

        # Delay clock towards a whole time to increase sleep relative precision
        while curr_time - np.fix(curr_time) > 0.3:
            curr_time = time.time()

        # Align clock on whole time
        to_sleep = math.floor(curr_time + 1.0) - curr_time
        logging.info(curr_time)
        time.sleep(to_sleep)
        self.clock_start = time.time()
        logging.info("Clock start is at: " + str(self.clock_start))

    def sleep_until_next_tick(self):
        self.tick_count = self.tick_count + 1

        current_time = time.time()
        sleep_amount = (self.tick_count * State_Machine.TRANSMISSION_RATE + self.clock_start) - current_time

        if sleep_amount < 0:
            logging.warning("Skipping sleep time !")
            return

        time.sleep(sleep_amount)
