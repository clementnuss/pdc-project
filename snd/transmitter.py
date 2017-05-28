import collections
from enum import Enum

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
        self.byte_count = 0
        self.last_byte_sent = None
        self.receiver_ack = True

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
        byte_to_send = None

        if self.receiver_ack:
            self.receiver_ack = False
            self.byte_count = self.byte_count + 1
            logging.info("Transmitting byte: " + str(self.byte_count))
            byte_to_send = self.byte_sequence.popleft()
        else:
            logging.warning("Retransmitting previous data")
            byte_to_send = self.last_byte_sent

        self.last_byte_sent = byte_to_send
        self._send_byte(byte_to_send)
        self.state = State.WAIT_FOR_ACK

    def _send_byte(self, b):
        """
        Send one byte starting from the least significant bit
        
        :param b: 
        :return: 
        """
        processed_b = b[0]
        for i in range(0, 4):
            symbol_index = processed_b & BIT_MASK
            symbol_to_send = SYMBOLS[symbol_index]
            processed_b = processed_b >> NUM_BITS

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

        # wait one tick for receiver ack
        State_Machine.sleep_until_next_tick(self)

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
