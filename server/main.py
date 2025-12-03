import time
import requests
import cv2
from picamera2 import Picamera2


cam = Picamera2()
cam.resolution = (1024, 768)
cam.framerate = 30
cam.start()

while True:
    frame = cam.capture_array()
    cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()