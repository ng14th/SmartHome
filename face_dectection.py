import numpy as np

import os
import cv2
import serial
import time
s = serial.Serial('COM2',9600)


cv2_base_dir = os.path.dirname(os.path.abspath(cv2.__file__))
haar_model = os.path.join(cv2_base_dir, 'data/haarcascade_frontalface_default.xml')
# import faces CascadeClassifier
face_cascade = cv2.CascadeClassifier(haar_model)


def distance_to_camera(knownWidth,focalLength,perWidth):
  return (knownWidth * focalLength) / perWidth

def face_region(image):
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  faces = face_cascade.detectMultiScale(gray,
                                        scaleFactor = 1.1,
                                        minNeighbors = 5,
                                        minSize = (30,30),
                                        flags = cv2.CASCADE_SCALE_IMAGE)
  return faces


# Initialize the known parameters
KNOWN_DISTANCE = 35.0
KNOWN_WIDTH = 10.0
IMAGE_PATHS = ["1.jpg"]
image = cv2.imread(IMAGE_PATHS[0])
face = face_region(image)
focalLength = (face[0][2] * KNOWN_DISTANCE) / KNOWN_WIDTH

# run camera
cap = cv2.VideoCapture(0)
cap.read()

while True:
  s.flushInput()  # flush input buffer, discarding all its contents
  s.flushOutput()
  ret,image = cap.read()
  #get image from camera
  faces = face_region(image)

  if faces == ():
      print("No Deteced")
      s.write(b'0')
      time.sleep(5)
  #mark the region with rectangle
  for (x,y,w,h) in faces:
    s.write(b'1')
    print("Deteced")
    time.sleep(5)
    cv2.rectangle(image,(x,y),(x+w,y+h),(255,0,0),2)
    distance = distance_to_camera(KNOWN_WIDTH,focalLength,w)

    cv2.putText(image, "%.2fcm" % (distance),
    (image.shape[1] - 400, image.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
    2.0, (0, 255, 0), 2)

  cv2.imshow("image", image)

  if cv2.waitKey(5)%0x100 == 27:
    break
cap.release()
cv2.destroyAllWindows()