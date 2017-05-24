import logging
import time


class State_Machine(object):
    TRANSMISSION_RATE = 1.0 / 100.0

    def __init__(self):
        self.clock_start = -1
        self.tick_count = 0

    def sleep_until_next_tick(self):
        self.tick_count = self.tick_count + 1

        current_time = time.time()
        sleep_amount = (self.tick_count * State_Machine.TRANSMISSION_RATE + self.clock_start) - current_time

        if sleep_amount < 0:
            logging.warning("Skipping sleep time !")
            return

        time.sleep(sleep_amount)
