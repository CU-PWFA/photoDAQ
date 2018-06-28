

import devices.Camera
import cv2
import numpy as np
import PyCapture2 as pc2



def streamCam(cam, name): 
    cam.start_capture()
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(name, 600,600)
    camRow  = cam.cam.getGigEImageSettingsInfo().maxHeight
    camCol = cam.cam.getGigEImageSettingsInfo().maxWidth 
    while True:
        try:
            image = cam.retrieve_buffer()
        except pc2.Fc2error as fc2Err:
            print(name + ':')
            print(fc2Err)
            continue
        cv_image = np.frombuffer(bytes(image.getData()), dtype = np.uint16).reshape(\
        (camRow, camCol))
        cv2.imshow(name, cv_image)
        cv2.waitKey(1)
        if cv2.getWindowProperty(name,cv2.WND_PROP_VISIBLE) < 1:   
            break  

