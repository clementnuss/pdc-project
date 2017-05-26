import collections
from enum import Enum

from State_Machine import *
from cv.ImageProcessing import *
from utils.Symbols import *

logging.basicConfig(format='%(module)15s # %(levelname)s: %(message)s', level=logging.INFO)


class State(Enum):
    IDLE = 'Idle'
    SCREEN_DETECTION = 'Screen detection'
    STAND_BY = 'Stand by'
    SYNC_CLOCK = 'Sync clock'
    CALIBRATE = 'Calibrate colors'
    FIND_SCREEN = 'Find screen'
    RECEIVE = 'Receive'
    CHECK = 'Check'
    VALIDATE_DATA = 'Validate data'


class Receiver(State_Machine):
    # At distance ~3.20m, np.sum of the thresholded image gives ~510000 (because values are 255)
    # The threshold then needs to be around 500000

    DUMMY_MASK = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    DUMMY_MASK[200:300, 200:400] = np.uint8(1)
    DUMMY_MASK = np.dstack([DUMMY_MASK] * 3)

    def __init__(self):
        State_Machine.__init__(self)

        self.state = State.SCREEN_DETECTION
        self.decoded_byte = 0
        self.decoded_byte_count = 0
        self.decoded_sequence = collections.deque()
        self.bitCount = 0
        self.screen_mask = None

        if SIMULATE:
            simulation_handler = SIMULATION_HANDLER
            self.cv_handler = simulation_handler.rcvr
            self.cap = simulation_handler.rcvr

        print('Initialized rcvr at state ' + str(self.state))
        time.sleep(1)

    def run(self):
        while True:
            if self.state == State.IDLE:
                self.do_idle()
            elif self.state == State.SCREEN_DETECTION:
                self.do_find_screen()
            elif self.state == State.SYNC_CLOCK:
                self.do_sync()
            elif self.state == State.CALIBRATE:
                self.do_calibrate()
            elif self.state == State.RECEIVE:
                self.do_receive()
            elif self.state == State.CHECK:
                self.do_check()
            elif self.state == State.VALIDATE_DATA:
                self.do_validate_data()
            else:
                raise NotImplementedError('Undefined receiver state')

    def do_idle(self):
        pass

    def do_find_screen(self):
        """
        Find the transmitter screen. When the screen detection algorithm has converged, the receiver displays
        the ACK symbol and goes into clock sync state. When the transmitter side of the algorithm has converged, 
        its screen displays the ACK symbol also.
        
        :return: 
        """
        self.cv_handler.display_hsv_color(S_NO_ACK)
        State_Machine.compute_screen_boundaries(self, S_ACK[0, 0, 0])
        self.cap.set_screen_boundaries(self.screen_boundaries)

        self.cv_handler.display_hsv_color(S_ACK)
        self.state = State.SYNC_CLOCK
        logging.info("Receiver finished the Screen detection phase")
        return

    def do_sync(self):
        """
        Synchronize the receiver clock with the transmitter 
        
        # 1. Transmitter screen is ACK
        # 2. Transmitter screen blacks out -> data is going to be sent next second (epoch reference)
        # 3. Receiver sleeps until next epoch second + half the transmission rate
        # 4. Receiver wakes up and start sampling for data
        
        :return: 
        """

        # void_score, ack_score = State_Machine.get_symbols_scores(self, self.VOID_REF, self.ACK_REF)

        # Due to polling of camera, none means we do no yet have access to cropped frame

        # Transmitter screen has blacked out
        value_mean = self.get_value_mean()
        logging.info("value mean: " + str(value_mean))
        if value_mean < 80:
            current_time = time.time()
            self.clock_start = current_time + State_Machine.SAMPLING_OFFSET

            self.state = State.CALIBRATE
            self.cv_handler.display_hsv_color(S_VOID)
            logging.info("Clock start is: " + str(self.clock_start) + " Time is " + str(current_time))
            logging.info("Receiver finished the synchronization phase")
            State_Machine.sleep_until_next_tick(self)

    def do_calibrate(self):

        for i in range(0, NUM_SYMBOLS):
            hue_mean = 0.0

            for x in range(0,3):

                hue_mean += State_Machine.get_hue_mean(self)

                State_Machine.sleep_until_next_tick(self)

            hue_mean = np.round(hue_mean / 3.0)
            logging.info("hue mean : " + str(hue_mean))
            SYMBOLS[i, 0, 0, 0] = np.round(hue_mean)

        for i in range(0, NUM_SYMBOLS):
            logging.info("symbol " + str(i) + " : " + str(SYMBOLS[i]))

        self.state = State.RECEIVE

    def do_receive(self):

        self.decoded_byte_count = self.decoded_byte_count + 1

        logging.info("Decoding byte number " + str(self.decoded_byte_count))

        symbol_count = 0
        self.decoded_byte = 0

        for i in range(0, 4):
            # ret, frame = self.cap.readHSVFrame()
            # self.cv_handler.display_hsv_frame(superimpose(self.VOID_REF, frame))

            # zero_score, one_score = State_Machine.get_symbols_scores(self, self.SYMBOL_ZERO_REF, self.SYMBOL_ONE_REF)
            hue_mean = State_Machine.get_hue_mean(self)
            logging.info("hue mean : " + str(hue_mean))

            detected_symbol = (np.abs(SYMBOLS[:, 0, 0, 0] - hue_mean)).argmin()
            logging.info("detected symbol: " + str(detected_symbol))

            self.decoded_byte = (detected_symbol << NUM_BITS * i) | self.decoded_byte

            symbol_count = symbol_count + 1
            State_Machine.sleep_until_next_tick(self)

        self.state = State.VALIDATE_DATA

    def do_check(self):
        pass

    def do_validate_data(self):
        data_is_valid = True

        if data_is_valid:
            self.cv_handler.display_hsv_color(S_ACK)
            self.decoded_sequence.append(self.decoded_byte)
            logging.info("Received letter : " + chr(self.decoded_byte))
            logging.info("Sent ACK to transmitter")
        else:
            self.cv_handler.display_hsv_color(S_NO_ACK)
            logging.info("Sent NO ACK to transmitter")

        State_Machine.sleep_until_next_tick(self)
        self.cv_handler.display_hsv_color(S_VOID)
        self.state = State.RECEIVE

        if len(self.decoded_sequence) % 10 == 0:
            str = ""
            for b in self.decoded_sequence:
                str += chr(b)

            logging.info("So far, received: " + str)

        State_Machine.sleep_until_next_tick(self)

    def _compute_checksum(self):
        return True


def main():
    r = Receiver()
    # ret, frame = rcvr.screen_decoder.getCameraSnapshot()
    # rcvr.screen_decoder.displayFrame(frame)
    # r._compute_screen_mask()
    # r.do_receive()
    # r.do_validate_data()
    r.run()


if __name__ == "__main__":
    main()
    input("")
