import collections
from enum import Enum

import unireedsolomon

from State_Machine import *
from utils import Constants
from utils.Symbols import *

logging.basicConfig(format='%(module)15s # %(levelname)s: %(message)s', level=logging.INFO)


class State(Enum):
    IDLE = 'Idle'
    SCREEN_DETECTION = 'Screen detection'
    STAND_BY = 'Stand by'
    SYNC_CLOCK = 'Sync clock'
    CALIBRATE = 'Calibrate colors'
    SEND = 'Send'
    RECEIVE = 'Receive'
    WAIT_FOR_ACK = 'Wait'


class Transmitter(State_Machine):
    def __init__(self, file_name):
        State_Machine.__init__(self)
        self.state = State.SCREEN_DETECTION
        self.byte_sequence = collections.deque()
        self.packet_count = 0
        self.last_data_packet = None
        self.receiver_ack = True
        self.rs_coder = unireedsolomon.RSCoder(Constants.RS_codeword_size, Constants.RS_message_size)

        if Constants.SIMULATE:
            simulation_handler = Constants.SIMULATION_HANDLER
            self.cv_handler = simulation_handler.tmtr
            self.cap = simulation_handler.tmtr

        logging.info('Initialized snd at state ' + str(self.state))

        self._load_file(file_name)

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
            elif self.state == State.SEND:
                if len(self.byte_sequence) > 0:
                    self.do_send()
                else:
                    logging.info("Transmission finished")
                    self.state = State.IDLE
            elif self.state == State.RECEIVE:
                self.do_receive()
            elif self.state == State.WAIT_FOR_ACK:
                logging.info("Transmitter branched in wait for ack mode")
                self.do_get_ack()
            else:
                raise NotImplementedError('Undefined snd state')

    def do_idle(self):
        time.sleep(1)

    def do_find_screen(self):
        """
        Find the receiver screen. When the screen detection algorithm has converged, the receiver displays
        the ACK symbol and goes into clock sync state. When the transmitter side of the algorithm has converged, 
        its screen displays the ACK symbol also.
    
        :return: 
        """

        self.cv_handler.display_hsv_color(S_NO_ACK)
        State_Machine.compute_screen_boundaries(self, S_NO_ACK)
        self.cap.set_screen_boundaries(self.screen_boundaries)

        time.sleep(0.2)

        # Calibrate no acks
        self._calibrate_noacks()

        self.cv_handler.display_hsv_color(S_ACK)
        self.state = State.SYNC_CLOCK
        logging.info("Transmitter finished the Screen detection phase")
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

        self.receiver_ack = False

        while not self.receiver_ack:

            State_Machine._align_clock(self)
            ack_score, no_ack_score = State_Machine.get_ack_scores(self)

            logging.info("Ack score: " + str(ack_score) + " No ack score: " + str(no_ack_score))

            if ack_score < no_ack_score:
                logging.info("Got ack from receiver.")
                self._calibrate_acks()

                curr_time = time.time()
                self.clock_start = curr_time

                logging.info(
                    "Blacking out screen. Current time is: " + str(curr_time) + " Clock start is: " + str(
                        self.clock_start))
                self.receiver_ack = True

                # Screen goes black, meaning that at next epoch second, receiver clock fires up and get in sync
                self.cv_handler.black_out()
                self.state = State.CALIBRATE
                State_Machine.sleep_until_next_tick(self)
                logging.info("Transmitter finished the synchronization phase")
            else:
                logging.info("NO ACK")

    def do_send(self):
        data_packet = collections.deque()

        if self.receiver_ack:
            self.receiver_ack = False
            self.packet_count = self.packet_count + 1
            logging.info("Transmitting data packet: " + str(self.packet_count))
            for i in range(0, Constants.RS_message_size):
                next_byte = self.byte_sequence.popleft() if len(self.byte_sequence) > 0 else bytes([0])
                data_packet.append(next_byte[0])
        else:
            logging.warning("Retransmitting previous data packet")
            data_packet = self.last_data_packet

        self.last_data_packet = data_packet.copy()
        self._send_packet(data_packet)
        self.state = State.WAIT_FOR_ACK

    def _send_packet(self, data: collections.deque):
        """
        Send one byte starting from the least significant bit
        
        :param data: 
        :return: 
        """

        # A data packet contains 8 bytes, and the RS message is 12 bytes long
        rs_encoded = self.rs_coder.encode(data, return_string=False)
        rs_encoded_cnt = 0

        num_bits_to_send = 0
        num_symbols = 8 * Constants.RS_codeword_size / 3
        processed_b = 0

        for i in range(0, int(np.ceil(num_symbols))):
            if num_bits_to_send < NUM_BITS:
                # We first shift the unsent bits to the left in order to leave 8 bits free, and we add the next
                # data byte to the right of processed_b

                # we only keep the num_bits_to_send digits, and we then shift processed_b to the left
                processed_b &= 2 ** num_bits_to_send - 1
                processed_b = (processed_b << 8) | int(rs_encoded[rs_encoded_cnt])
                rs_encoded_cnt += 1
                num_bits_to_send += 8

            symbol_index = (processed_b >> num_bits_to_send - NUM_BITS) & BIT_MASK
            symbol_to_send = SYMBOLS[symbol_index]
            num_bits_to_send -= NUM_BITS

            self.cv_handler.display_hsv_color(symbol_to_send)
            logging.info(str(symbol_index) + " at time " + str(time.time()))
            State_Machine.sleep_until_next_tick(self)

    def do_calibrate(self):

        for i in range(0, NUM_SYMBOLS):
            for x in range(0, 3):
                self.cv_handler.display_hsv_color(SYMBOLS[i])
                State_Machine.sleep_until_next_tick(self)

        self.state = State.SEND

    def do_receive(self):
        pass

    def do_get_ack(self):

        self.cv_handler.black_out()
        current_time = time.time();
        logging.info("ack wait time is: " + str(current_time))

        # wait several tick for receiver ack to account for camera delay
        self.sleep_until_next_tick()
        self.sleep_until_next_tick()
        self.sleep_until_next_tick()
        time.sleep(State_Machine.TRANSMISSION_RATE / 2.0)

        current_time = time.time()
        logging.info("ack wait wakeup time is: " + str(current_time))

        ack_score, no_ack_score = State_Machine.get_ack_scores(self)

        logging.info("Ack score: " + str(ack_score) + " No ack score: " + str(no_ack_score))

        if (ack_score < no_ack_score):
            logging.info("Got ACK")
            self.receiver_ack = True
            self.state = State.SEND
        else:
            self.receiver_ack = False
            logging.info("NO ACK")

        # If no ack then retransmit byte
        # If ack transmit next byte
        self.state = State.SEND
        State_Machine.sleep_until_next_tick(self)

    def _calibrate_noacks(self):
        hue_mean = 0.0

        for x in range(0, 3):
            hue_mean += State_Machine.get_hue_mean(self)
            time.sleep(0.2)

        hue_mean = np.round(hue_mean / 3.0)
        logging.info("hue mean for no ack calibration was: " + str(hue_mean))
        S_NO_ACK = np.round(hue_mean)

    def _calibrate_acks(self):
        hue_mean = 0.0

        for x in range(0, 3):
            hue_mean += State_Machine.get_hue_mean(self)
            time.sleep(0.2)

        hue_mean = np.round(hue_mean / 3.0)
        logging.info("hue mean for ack calibration was: " + str(hue_mean))
        S_ACK = np.round(hue_mean)

    def _load_file(self, file_name):

        with open(file_name, "rb") as f:
            byte = f.read(1)
            while byte:
                self.byte_sequence.append(byte)
                byte = f.read(1)


def main():
    r = Transmitter("../data/dummyText1.txt")
    # r.state = State.SEND
    r.run()
    # r.do_sync()


if __name__ == "__main__":
    main()
