from enum import Enum


class State(Enum):
    IDLE = 'Idle'
    SYNC = 'Sync'
    RECEIVE = 'Receive'
    CHECK = 'Check'
    WAIT = 'Wait'


class Receiver(object):
    def __init__(self):
        self.state = State.IDLE

        print('Initialized receiver at state ' + str(self.state))


def main():
    r = Receiver()


if __name__ == "__main__":
    main()
