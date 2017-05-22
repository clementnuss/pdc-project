from enum import Enum

import rcvr.screen_decoder


class State(Enum):
    IDLE = 'Idle'
    SYNC = 'Sync'
    RECEIVE = 'Receive'
    CHECK = 'Check'
    WAIT = 'Wait'


class Receiver(object):
    def __init__(self):
        self.state = State.IDLE

        print('Initialized rcvr at state ' + str(self.state))

    def run(self):
        if self.state == State.IDLE:
            self.doIdle()
        elif self.state == State.SYNC:
            self.doSync()
        elif self.state == State.RECEIVE:
            self.doReceive()
        elif self.state == State.CHECK:
            self.doCheck()
        elif self.state == State.WAIT:
            self.doWait()
        else:
            raise NotImplementedError('Undefined receiver state')

    def doIdle(self):
        pass

    def doSync(self):
        # HSV values for filtering H: 64-130 S: 126-255 V: 111-255
        pass

    def doReceive(self):
        pass

    def doCheck(self):
        pass

    def doWait(self):
        pass


def main():
    r = Receiver()
    print("hi")
    ret, frame = rcvr.screen_decoder.getCameraSnapshot()

    rcvr.screen_decoder.displayFrame(frame)


if __name__ == "__main__":
    main()
    input("Press enter to exit")
