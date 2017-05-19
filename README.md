# PDC project
Digital communication across computer screens

## Roadmap:

- implement screen detection (through HSV filtering and then masking the captured frames with the mask of the distant screen)
- implement transmitter/receiver synchronization
- send symbols using various colours (and HSV detection)
- implement error correction code

### Synchronization

Before beginning the transmission, the encoder screen can alternate quickly (f=2Hz) between 2 colours for x seconds

### Color detection:

1. filter each frame with the HSV range of a symbol
2. compute score for the filtered frame (that is, evaluate the portion of the image that is white)
3. choose symbol with highest area.

*Improvements*: select symbol if an area is greater than a threshold, instead of computing all areas and all filtered ranges.

*Calibration*: we need to count how many symbols can be reliably encoded/decoded. That is count how many colours we can use.

With 4 colours there shall not be any problem at all. 8 would be nice !

#### OpenCV Python tutorials

[around here](http://docs.opencv.org/3.2.0/d6/d00/tutorial_py_root.html)

#### Dependencies setup

Using [Python 3](https://www.python.org/downloads/release/python-361/), and Open CV.
To install OpenCV with Python 3, follow the instructions on [this link](https://www.solarianprogrammer.com/2016/09/17/install-opencv-3-with-python-3-on-windows/)
Basically, you need to install [Microsoft Visual C++ 2015 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=53587), and then to download and install compiled versions of numpy and opencv libraries for python, [on this webpage](http://www.lfd.uci.edu/~gohlke/pythonlibs/).

