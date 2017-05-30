import collections
import sys
from enum import Enum

import unireedsolomon
from unireedsolomon import RSCodecError

from State_Machine import *
from cv.ImageProcessing import *
from utils import Constants
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
    WRITE_TO_FILE = 'Write to file'


class Receiver(State_Machine):
    # At distance ~3.20m, np.sum of the thresholded image gives ~510000 (because values are 255)
    # The threshold then needs to be around 500000

    DUMMY_MASK = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    DUMMY_MASK[200:300, 200:400] = np.uint8(1)
    DUMMY_MASK = np.dstack([DUMMY_MASK] * 3)

    def __init__(self):
        State_Machine.__init__(self)

        self.state = State.SCREEN_DETECTION
        self.data_packet = np.array
        self.decoded_packet_count = 0
        self.decoded_sequence = collections.deque()
        self.bitCount = 0
        self.screen_mask = None
        self.rs_coder = unireedsolomon.RSCoder(Constants.RS_codeword_size, Constants.RS_message_size)

        if Constants.SIMULATE:
            simulation_handler = Constants.SIMULATION_HANDLER
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
            elif self.state == State.WRITE_TO_FILE:
                self.do_write_to_file()
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
        State_Machine.compute_screen_boundaries(self, S_ACK)
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
        # logging.info("value mean: " + str(value_mean))
        if value_mean < 80:
            current_time = time.time()
            self.clock_start = current_time + State_Machine.SAMPLING_OFFSET

            self.state = State.CALIBRATE
            self.cv_handler.black_out()
            logging.info("Clock start is: " + str(self.clock_start) + " Time is " + str(current_time))
            logging.info("Receiver finished the synchronization phase")
            State_Machine.sleep_until_next_tick(self)

    def do_calibrate(self):

        for i in range(0, NUM_SYMBOLS):
            hue_mean = 0.0

            for x in range(0, 3):
                # hue_mean += State_Machine.get_hue_mean(self)
                hue_mean += State_Machine.get_cyclic_hue_mean_to_reference(self, SYMBOLS[i])

                State_Machine.sleep_until_next_tick(self)

            hue_mean = np.round(hue_mean / 3.0)
            logging.info("hue mean : " + str(hue_mean))
            SYMBOLS[i] = np.round(hue_mean)

        for i in range(0, NUM_SYMBOLS):
            logging.info("symbol " + str(i) + " : " + str(SYMBOLS[i]))

        self.state = State.RECEIVE

    def do_receive(self):

        logging.info("Decoding packet number " + str(self.decoded_packet_count))

        processed_b = 0
        num_unset_bits = 8
        byte_idx = 0
        self.data_packet = np.empty(12, np.uint8)
        self.cv_handler.display_hsv_color(140)

        for i in range(0, Constants.num_symbols_per_data_packet):
            # hue_mean = State_Machine.get_hue_mean(self)
            # logging.info("hue mean : " + str(hue_mean))

            ret, frame = self.cap.readHSVFrame()

            detected_symbol = np.array(
                [np.abs(self.compute_cyclic_hue_mean_to_reference(frame, ref) - ref) for ref in SYMBOLS]).argmin()

            logging.info("detected symbol: " + str(detected_symbol))

            if i == 31:
                self.cv_handler.display_hsv_color(60)
            if i == 30:
                self.cv_handler.display_hsv_color(90)
            if i == 29:
                self.cv_handler.display_hsv_color(160)

            if i == 28:
                self.cv_handler.display_hsv_color(30)
            if i == 29:
                self.cv_handler.display_hsv_color(55)
            if i == 30:
                self.cv_handler.display_hsv_color(0)

            if num_unset_bits >= NUM_BITS:
                processed_b |= detected_symbol << num_unset_bits - NUM_BITS
                num_unset_bits -= NUM_BITS
            else:
                bit_shift = NUM_BITS - num_unset_bits
                processed_b |= detected_symbol >> bit_shift
                self.data_packet[byte_idx] = processed_b
                byte_idx += 1
                processed_b = (detected_symbol & (2 ** bit_shift - 1)) << 8 - bit_shift
                num_unset_bits = 8 - (NUM_BITS - num_unset_bits)

            if not i == Constants.num_symbols_per_data_packet - 1:
                State_Machine.sleep_until_next_tick(self)

        self.data_packet[byte_idx] = processed_b
        self.state = State.VALIDATE_DATA

    def do_check(self):
        pass

    def do_validate_data(self):
        global msg
        try:
            msg, ecc = self.rs_coder.decode(self.data_packet, return_string=False)
            data_is_valid = all(b < 128 for b in msg)
        except RSCodecError:
            data_is_valid = False

        if data_is_valid:
            self.decoded_packet_count = self.decoded_packet_count + 1
            self.cv_handler.display_hsv_color(S_ACK)
            for b in msg:
                if b == Constants.END_OF_FILE_MARKER:
                    self.state = State.WRITE_TO_FILE
                    logging.info("Received end of file marker. Transmission terminated.")
                    return
                else:
                    self.decoded_sequence.append(b)
            logging.info("Received message : " + ''.join([chr(b) for b in msg]))
            logging.info("Sent ACK to transmitter")
        else:
            self.cv_handler.display_hsv_color(S_NO_ACK)
            logging.info("Sent NO ACK to transmitter")

        State_Machine.sleep_until_next_tick(self)
        State_Machine.sleep_until_next_tick(self)
        State_Machine.sleep_until_next_tick(self)
        State_Machine.sleep_until_next_tick(self)
        State_Machine.sleep_until_next_tick(self)
        self.state = State.RECEIVE

        if self.decoded_packet_count % 5 == 0:
            logging.info("So far, received: " + ''.join([chr(b) for b in self.decoded_sequence]))

    def do_write_to_file(self):

        with open("../decoded.txt", "wb") as f:
            for byte in self.decoded_sequence:
                f.write(byte)

        logging.info("Wrote file")
        self.cv_handler.kill()
        sys.exit(0)


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
