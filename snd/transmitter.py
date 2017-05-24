import collections
from enum import Enum

import cv.CV_GUI_Handler
import cv.CV_Video_Capture_Handler
from State_Machine import *
from cv.ImageProcessing import *
from utils.Symbols import *

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

class State(Enum):
    IDLE = 'Idle'
    SCREEN_DETECTION = 'Screen detection'
    SYNC_CLOCK = 'Sync clock'
    SEND = 'Send'
    RECEIVE = 'Receive'
    WAIT_FOR_ACK = 'Wait'


class Transmitter(State_Machine):
    def __init__(self, file_name):
        State_Machine.__init__(self)
        self.state = State.SCREEN_DETECTION
        self.cv_handler = cv.CV_GUI_Handler.OpenCvHandler()
        self.cap = cv.CV_Video_Capture_Handler.CV_Video_Capture_Handler()
        self.byte_sequence = collections.deque()
        self.byte_count = 0
        self.last_byte_sent = None
        self.receiver_ack = True

        print('Initialized snd at state ' + str(self.state))

        self._load_file(file_name)

    def run(self):

        while True:
            if self.state == State.IDLE:
                self.do_idle()
            elif self.state == State.SCREEN_DETECTION:
                self.do_find_screen()
            elif self.state == State.SYNC_CLOCK:
                self.do_sync()
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
                self.do_wait_for_ack()
            else:
                raise NotImplementedError('Undefined snd state')

    def do_idle(self):
        time.sleep(1)

    def do_find_screen(self):
        """
        Find the transmitter screen. When the screen detection algorithm has converged, the receiver displays
        the ACK symbol and goes into clock sync state. When the transmitter side of the algorithm has converged, 
        its screen displays the ACK symbol also.
    
        :return: 
        """
        self._compute_screen_mask()
        self.cv_handler.display_hsv_color(S_ACK)
        self.state = State.SYNC_CLOCK
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

        State_Machine._align_clock(self)
        self.receiver_ack = False

        while not self.receiver_ack:
            ret, frame = self.cap.readHSVFrame()
            masked_frame = frame[:, :, 0] * self.screen_mask[:, :, 0]

            ack_score = compute_score(masked_frame, self.ACK_MASK)
            no_ack_score = compute_score(masked_frame, self.NO_ACK_MASK)

            logging.info("Ack score: " + str(ack_score) + " No ack score: " + str(no_ack_score))

            if (ack_score < no_ack_score):
                logging.info("Got ACK ")
                self.receiver_ack = True

                # Screen goes black, meaning that at next epoch second, receiver clock fires up and get in sync
                self.cv_handler.display_hsv_color(S_VOID)
                self.state = State.SEND
            else:
                logging.info("NO ACK")

            State_Machine.sleep_until_next_tick(self)

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
        for i in range(0, 8):
            bit_to_send = processed_b & 1
            processed_b = processed_b >> 1

            if bit_to_send:
                self.cv_handler.display_hsv_color(S_ONE)
                logging.info(1)
                State_Machine.sleep_until_next_tick(self)
            else:
                self.cv_handler.display_hsv_color(S_ZERO)
                logging.info(0)
                State_Machine.sleep_until_next_tick(self)

    def do_receive(self):
        pass

    def do_wait_for_ack(self):

        self.cv_handler.display_hsv_color(S_VOID)

        ret, frame = self.cap.readHSVFrame()
        masked_frame = frame[:, :, 0] * self.screen_mask[:, :, 0]

        ack_score = compute_score(masked_frame, self.ACK_MASK)
        no_ack_score = compute_score(masked_frame, self.NO_ACK_MASK)

        logging.info("Ack score: " + str(ack_score) + " No ack score: " + str(no_ack_score))

        if (ack_score < no_ack_score):
            logging.info("Got ACK ")
            self.receiver_ack = True
            self.state = State.SEND
        else:
            self.receiver_ack = False
            logging.info("NO ACK")

        # If no ack then retransmit byte
        # If ack transmit next byte
        self.state = State.SEND
        State_Machine.sleep_until_next_tick(self)

    def _compute_screen_mask(self):
        converged = False
        ret, frame = self.cap.readHSVFrame()
        prev_mask = getMask(frame)

        while not converged:
            ret, frame = self.cap.readHSVFrame()
            mask = getMask(frame)

            s = np.sum(mask)
            diff = np.sum(mask - prev_mask)
            print("Mask sum: ", s)
            print("Mask diff: ", diff)

            if diff < State_Machine.CONVERGENCE_THRESHOLD and s > State_Machine.BLACK_THRESHOLD:
                converged = True
                self.screen_mask = np.uint8(mask / np.uint8(255))[..., np.newaxis]
            else:
                prev_mask = mask

            self.cv_handler.send_new_frame(mask)
            time.sleep(0.2)

        print("Synchronization OK")
        self.SYMBOL_ZERO_MASK = (State_Machine.SYMBOL_ZERO_MASK * self.screen_mask)[:, :, 0]
        self.SYMBOL_ONE_MASK = (State_Machine.SYMBOL_ONE_MASK * self.screen_mask)[:, :, 0]
        self.ACK_MASK = (SYMBOL_ACK_MASK * self.screen_mask)[:, :, 0]
        self.NO_ACK_MASK = (SYMBOL_NO_ACK_MASK * self.screen_mask)[:, :, 0]

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
