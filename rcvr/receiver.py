import collections
from enum import Enum

from State_Machine import *
from cv.ImageProcessing import *
from utils.Symbols import *


class State(Enum):
    IDLE = 'Idle'
    SCREEN_DETECTION = 'Screen detection'
    SCREEN_STAND_BY = 'Stand by'
    SYNC_CLOCK = 'Sync clock'
    FIND_SCREEN = 'Find screen'
    RECEIVE = 'Receive'
    CHECK = 'Check'
    VALIDATE_DATA = 'Validate data'


class Receiver(State_Machine):
    # At distance ~3.20m, np.sum of the thresholded image gives ~510000 (because values are 255)
    # The threshold then needs to be around 500000

    DUMMY_MASK = np.zeros((WIDTH, HEIGHT), dtype=np.uint8)
    DUMMY_MASK[200:300, 200:400] = np.uint8(1)
    DUMMY_MASK = np.dstack([DUMMY_MASK] * 3)

    def __init__(self):
        State_Machine.__init__(self)

        self.state = State.SCREEN_DETECTION
        self.decoded_byte = 0
        self.decoded_sequence = collections.deque
        self.bitCount = 0
        self.screen_mask = None

        print('Initialized rcvr at state ' + str(self.state))
        time.sleep(1)

    def run(self):
        while True:
            if self.state == State.IDLE:
                self.do_idle()
            elif self.state == State.SCREEN_DETECTION:
                self.do_show_screen()
            elif self.state == State.STAND_BY:
                self.do_find_screen()
            elif self.state == State.SYNC_CLOCK:
                self.do_sync()
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
        State_Machine.compute_screen_mask(self, ONE_RANGE)
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

        void_score, ack_score = State_Machine.get_symbols_scores(self, self.VOID_MASK, self.ACK_MASK)

        # Transmitter screen has blacked out
        if void_score < ack_score:
            current_time = time.time()
            State_Machine.clock_start = np.fix(current_time + 1.0) + State_Machine.SAMPLING_OFFSET
            self.state = State.RECEIVE
            logging.info("Clocks firing up in less than a second !")
            time.sleep(State_Machine.clock_start - current_time)

    def do_receive(self):
        symbol_count = 0
        self.decoded_byte = 0
        for i in range(0, 8):
            ret, frame = self.cap.readHSVFrame()
            masked_frame = frame * self.screen_mask
            #self.cv_handler.send_new_frame(masked_frame)
            zero_score = compute_score(masked_frame, self.SYMBOL_ZERO_MASK)
            one_score = compute_score(masked_frame, self.SYMBOL_ONE_MASK)
            if (zero_score > one_score):
                print("0")
                self.decoded_byte = (self.decoded_byte << 1) | 1
            else:
                print("1")
                self.decoded_byte = self.decoded_byte << 1
            symbol_count = symbol_count + 1
            State_Machine.sleep_until_next_tick(self)

        self.state = State.VALIDATE_DATA

    def do_check(self):
        pass

    def do_validate_data(self):
        data_is_valid = True

        if data_is_valid:
            self.cv_handler.display_hsv_color(S_ACK)
        else:
            self.cv_handler.display_hsv_color(S_NO_ACK)

        self.decoded_sequence.append(self.decoded_byte)
        State_Machine.sleep_until_next_tick(self)
        self.cv_handler.display_hsv_color(S_VOID)
        self.state = State.RECEIVE

    def _compute_checksum(self):
        return True


def main():
    r = Receiver()
    # ret, frame = rcvr.screen_decoder.getCameraSnapshot()
    # rcvr.screen_decoder.displayFrame(frame)
    #r._compute_screen_mask()
    #r.do_receive()
    #r.do_validate_data()
    r.run()


if __name__ == "__main__":
    main()
    input("")
