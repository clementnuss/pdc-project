import cv2
import numpy as np
import threading

ENCODER_WINDOW = 'encoder'
waiting_thread = None
# RESOLUTION = [1920,1080]

def initialize():
    global waiting_thread

    cv2.namedWindow(ENCODER_WINDOW)
    waiting_thread = threading.Thread(target=waitKeyFunction)
    waiting_thread.setDaemon(True)
    waiting_thread.start()

def waitKeyFunction():
    print("salut")
    while True:
        print("salut 2")
        if cv2.waitKey(0) & 0xFF == 27:
            break
    cv2.destroyAllWindows()
    exit(0)


def displayHSVColor(color):
    mat = np.full((600, 800, 3), color, dtype=np.uint8)
    cv2.imshow(ENCODER_WINDOW, mat)



def main():

    displayHSVColor((170, 255, 255))




if __name__ == '__main__':
    initialize()
    main()
    waiting_thread.join()
    cv2.destroyAllWindows()
