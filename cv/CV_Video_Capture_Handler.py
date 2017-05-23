import cv2


class CV_Video_Capture_Handler:
    class __CV_Video_Capture_Handler:
        def __init__(self):
            pass

        def __str__(self):
            return "OpenCV video capture handler singleton" + repr(self)

    instance = None

    def __init__(self):
        if not CV_Video_Capture_Handler.instance:
            CV_Video_Capture_Handler.instance = CV_Video_Capture_Handler.__CV_Video_Capture_Handler
            self.videocapture = cv2.VideoCapture(0)

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def readHSVFrame(self):
        ret, frame = self.videocapture.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return ret, frame
