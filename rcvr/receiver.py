import collections
import sys
from enum import Enum

import unireedsolomon
from unireedsolomon import RSCodecError

from State_Machine import *
from cv.ImageProcessing import *
from utils import Constants
from utils.Constants import NUM_HORIZONTAL_CELLS
from utils.Symbols import *

logging.basicConfig(format='%(module)15s # %(levelname)s: %(message)s', level=logging.INFO)


class State(Enum):
    IDLE = 'Idle'
    SCREEN_DETECTION = 'Screen detection'
    QUADRANT_FEEDBACK = 'Quadrant feedback'
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

    DUMMY_MASK = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH), dtype=np.uint8)
    DUMMY_MASK[200:300, 200:400] = np.uint8(1)
    DUMMY_MASK = np.dstack([DUMMY_MASK] * 3)

    def __init__(self):
        State_Machine.__init__(self)
        self.name = 'Receiver'
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
            elif self.state == State.QUADRANT_FEEDBACK:
                self.do_quadrant_feedback()
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

        if Constants.USE_AKIMBO_SCREEN:
            State_Machine.compute_akimbo_screen_boundaries(self, S_ACK)
            self.cap.set_akimbo_screen_boundaries(self.screen_boundaries1, self.screen_boundaries2)
        else:
            State_Machine.compute_screen_boundaries(self, S_ACK)
            self.cap.set_screen_boundaries(self.screen_boundaries)

        time.sleep(1)
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

        frame1, frame2 = self.cap.readHSVFrame_akimbo()

        ack_mean = np.array([self.compute_cyclic_hue_mean_to_reference(frame1, S_ACK),
                             self.compute_cyclic_hue_mean_to_reference(frame2, S_ACK)]).mean()
        no_ack_mean = np.array([self.compute_cyclic_hue_mean_to_reference(frame1, S_NO_ACK),
                                self.compute_cyclic_hue_mean_to_reference(frame2, S_NO_ACK)]).mean()

        ack_score = np.abs(ack_mean - S_ACK)
        no_ack_score = np.abs(no_ack_mean - S_NO_ACK)

        logging.info("Ack score: " + str(ack_score) + " No ack score: " + str(no_ack_score))
        received_no_ack = False

        if (ack_score > no_ack_score):
            received_no_ack = True

        if received_no_ack:
            # logging.info("Value mean was: " + str(value_mean))
            current_time = time.time()
            self.clock_start = current_time + State_Machine.SAMPLING_OFFSET

            self.state = State.QUADRANT_FEEDBACK
            self.cv_handler.black_out()
            logging.info("Clock start is: " + str(self.clock_start) + " Time is " + str(current_time))
            logging.info("Receiver finished the synchronization phase")
            State_Machine.sleep_until_next_tick(self)

    def do_calibrate(self):

        for i in range(0, NUM_SYMBOLS):
            hue_mean = 0.0

            for x in range(0, 3):
                # hue_mean += State_Machine.get_hue_mean(self)
                tmp_hue = State_Machine.get_cyclic_hue_mean_to_reference(self, SYMBOLS[i])
                hue_mean += tmp_hue
                self.cv_handler.display_hsv_color(tmp_hue)
                logging.info("hue mean : " + str(tmp_hue))
                State_Machine.sleep_until_next_tick(self)

            hue_mean = np.round(hue_mean / 3.0)
            logging.info("hue mean after 3 iterations : " + str(hue_mean))
            SYMBOLS[i] = np.round(hue_mean)

        for i in range(0, NUM_SYMBOLS):
            logging.info("symbol " + str(i) + " : " + str(SYMBOLS[i]))

        self.state = State.RECEIVE

    def do_quadrant_feedback(self):
        """
        NOACK   NOACK   = Horizontal    -> deuxieme passe
        NOACK   ACK     = Vertical      -> deuxième passe
        ACK     NOACK   = Ascendant     -> ok
        ACK     ACK     = Descendant    -> ok
        
        Deuxième passe:
        
        Horizontal: ACK partie supérieure, NOACK partie inférieure
        Vertical:   ACK partie gauche, NOACK partie droite
        
        :return: 
        """

        # Wait 5 ticks to account for transmitter camera delay:
        #
        #   calibration
        # T .--.--.--.
        # R           _._._._._

        logging.info("Receiver entered quadrant feedback mode")

        self.state = State.CALIBRATE

        # First pass
        if self.screen_orientation == 'horizontal':
            self.cv_handler.display_binary_hsv_color_vertical(S_NO_ACK, S_NO_ACK)
            logging.info("Receiver sent feedback, is horizontal")
            self.sleep_n_ticks(5)
        elif self.screen_orientation == 'vertical':
            self.cv_handler.display_binary_hsv_color_vertical(S_NO_ACK, S_ACK)
            logging.info("Receiver sent feedback, is vertical")
            self.sleep_n_ticks(5)
        elif self.screen_orientation == 'ascendant':
            self.cv_handler.display_binary_hsv_color_vertical(S_ACK, S_NO_ACK)
            logging.info("Receiver sent feedback, is ascendant")
            self.sleep_n_ticks(4)
            return
        elif self.screen_orientation == 'descendant':
            self.cv_handler.display_binary_hsv_color_vertical(S_ACK, S_ACK)
            logging.info("Receiver sent feedback, is descendant")
            self.sleep_n_ticks(4)
            return

        # Second pass
        frame = self.cap.readHSVFrame()
        ack_received = (
            np.abs(self.compute_cyclic_hue_mean_to_reference(frame,S_ACK) - S_ACK)
            <
            np.abs(self.compute_cyclic_hue_mean_to_reference(frame,S_NO_ACK) - S_NO_ACK))

        # Display the captured color so the transmitter knows which screen portion is available
        self.cv_handler.display_hsv_color(S_ACK if ack_received else S_NO_ACK)
        logging.info("Receiver told transmitter: " + str(ack_received))
        self.sleep_n_ticks(6)

    def do_receive(self):

        logging.info("Decoding packet number " + str(self.decoded_packet_count))
        self.cv_handler.display_hsv_color(140)

        bits_array = np.zeros(Constants.NUM_SYMBOLS_PER_DATA_PACKET * Constants.NUM_BITS_PER_SYMBOL, dtype=np.bool)
        # Added a wait to account for the generation of the first symbol on the transmitter side
        self.sleep_until_next_tick()
        self.cv_handler.display_hsv_color(0)

        for i in range(0, Constants.NUM_SYMBOLS_PER_DATA_PACKET):
            # hue_mean = State_Machine.get_hue_mean(self)
            # logging.info("hue mean : " + str(hue_mean))

            if Constants.USE_AKIMBO_SCREEN:
                frame1, frame2 = self.cap.readHSVFrame_akimbo(write=Constants.WRITE_IMAGE, caller=self.name)
                start_idx = i * Constants.NUM_BITS_PER_SYMBOL
                bits_array[start_idx: start_idx + Constants.NUM_BITS_PER_QUADRANT] = self._read_quadrant_symbols(frame1)
                bits_array[
                start_idx + Constants.NUM_BITS_PER_QUADRANT: start_idx + Constants.NUM_BITS_PER_SYMBOL] = self._read_quadrant_symbols(
                    frame2)
                # logging.info("detected symbol: " + str(bits_array[start_idx:start_idx + Constants.NUM_BITS_PER_SYMBOL]))

            else:
                frame = self.cap.readHSVFrame()
                detected_symbol = np.array(
                    [np.abs(self.compute_cyclic_hue_mean_to_reference(frame, ref) - ref) for ref in SYMBOLS]).argmin()
                logging.info("detected symbol: " + str(detected_symbol))
                """Old code used to parse binary symbols
                if num_unset_bits >= NUM_BITS_PER_COLOR:
                    processed_b |= detected_symbol << num_unset_bits - NUM_BITS_PER_COLOR
                    num_unset_bits -= NUM_BITS_PER_COLOR
                else:
                    bit_shift = NUM_BITS_PER_COLOR - num_unset_bits
                    processed_b |= detected_symbol >> bit_shift
                    self.data_packet[byte_idx] = processed_b
                    byte_idx += 1
                    processed_b = (detected_symbol & (2 ** bit_shift - 1)) << 8 - bit_shift
                    num_unset_bits = 8 - (NUM_BITS_PER_COLOR - num_unset_bits)
                """

            if i == Constants.NUM_SYMBOLS_PER_DATA_PACKET - 3:
                self.cv_handler.display_hsv_color(30)
            if i == Constants.NUM_SYMBOLS_PER_DATA_PACKET - 2:
                self.cv_handler.display_hsv_color(55)
            if i == Constants.NUM_SYMBOLS_PER_DATA_PACKET - 1:
                self.cv_handler.display_hsv_color(0)

            if not i == Constants.NUM_SYMBOLS_PER_DATA_PACKET - 1:
                State_Machine.sleep_until_next_tick(self)

        self.data_packet = np.packbits(bits_array)
        self.state = State.VALIDATE_DATA

    def _read_quadrant_symbols(self, quadrant_frame: np.ndarray):
        cell_height = quadrant_frame.shape[0] / Constants.NUM_VERTICAL_CELLS
        cell_width = quadrant_frame.shape[1] / Constants.NUM_HORIZONTAL_CELLS
        bits_array = np.zeros(Constants.NUM_BITS_PER_QUADRANT, dtype=np.bool)

        logging_res = np.zeros(Constants.NUM_CELLS_PER_QUADRANT, dtype=np.uint8)
        for i in range(0, Constants.NUM_CELLS_PER_QUADRANT):
            cell_start_y = int(int(i / NUM_HORIZONTAL_CELLS) * cell_height)
            cell_start_x = int(int(i % NUM_HORIZONTAL_CELLS) * cell_width)
            cell_margin = 3
            subcell = quadrant_frame[cell_margin + cell_start_y:int(cell_start_y + cell_height - cell_margin),
                      cell_margin + cell_start_x:int(cell_start_x + cell_width - cell_margin), :].copy()

            detected_symbol = np.uint8(np.array(
                [np.abs(self.compute_cyclic_hue_mean_to_reference(subcell, ref) - ref) for ref in SYMBOLS]).argmin())
            logging_res[i] = detected_symbol
            bits_array[NUM_BITS_PER_COLOR * i: NUM_BITS_PER_COLOR * (i + 1)] = \
                np.unpackbits(detected_symbol)[8 - NUM_BITS_PER_COLOR:]

        logging.info("Detected cells for quadrant :" + str(logging_res))

        return bits_array

    def do_validate_data(self):
        global msg
        try:
            msg, ecc = self.rs_coder.decode(self.data_packet, return_string=False)
            data_is_valid = all(b < 128 for b in msg)
        except RSCodecError:
            logging.info("Unable to correct RS errors")
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
                f.write(np.uint8(byte))

        logging.info("Wrote file")
        self.cv_handler.kill()
        sys.exit(0)


def main():
    r = Receiver()
    # frame = rcvr.screen_decoder.getCameraSnapshot()
    # rcvr.screen_decoder.displayFrame(frame)
    # r._compute_screen_mask()
    # r.do_receive()
    # r.do_validate_data()
    r.run()


if __name__ == "__main__":
    main()
    input("")
