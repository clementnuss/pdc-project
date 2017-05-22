from enum import Enum


class State(Enum):
    IDLE = 'Idle'
    SYNC = 'Sync'
    RECEIVE = 'Receive'
    WAIT = 'Wait'


class Transmitter(object):
    def __init__(self):
        self.state = State.IDLE

        print('Initialized snd at state ' + str(self.state))

    def run(self):
        if self.state == State.IDLE:
            self.doIdle()
        elif self.state == State.SYNC:
            self.doSync()
        elif self.state == State.RECEIVE:
            self.doReceive()
        elif self.state == State.WAIT:
            self.doWait()
        else:
            raise NotImplementedError('Undefined snd state')

    def doIdle(self):
        pass

    def doSync(self):
        pass

    def doReceive(self):
        pass

    def doWait(self):
        pass


def main():
    r = Transmitter()


if __name__ == "__main__":
    main()
