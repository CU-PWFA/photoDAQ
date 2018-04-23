#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 12:44:44 2018

@author: cu-pwfa
"""

import Camera as C
import cv2
import numpy as np

cam = C.Camera(0)
cam.startCapture()

try:
    while True:
        image = cam.retrieveBuffer()
        cv_image = np.frombuffer(bytes(image.getData()), dtype=cam.dtype).reshape( (cam.pixROW, cam.pixCOL) )
        cv2.imshow('frame',cv_image)
        cv2.waitKey(1)
except KeyboardInterrupt:
    cam.stopCapture()
    cam.disconnect()
  