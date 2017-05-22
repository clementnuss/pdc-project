from enum import Enum


class State(Enum):
    IDLE = 'Idle'
    SYNC = 'Sync'
    RECEIVE = 'Receive'
    WAIT = 'Wait'


class Transmitter(object):
    def __init__(self):
        self.state = State.IDLE

        print('Initialized transmitter at state ' + str(self.state))


def main():
    r = Transmitter()


if __name__ == "__main__":
    main()
