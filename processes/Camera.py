#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 15:33:16 2018

@author: robert
"""

from processes.process import Process
import PyCapture2 as pc2
import datetime
import numpy as np
import cv2
import cv2
import numpy as np

class Camera(Process):
    """ Process class for a camera. """
    def save_stream(self, numShots=None):
        """ Save images from the camera as they come in. """        
        cam = self.device
        cam.start_capture(self.save_image, numShots)
        
    def live_stream(self):
        """Stream images from the camera in a live feed."""
        cam = self.device
        width, height = self.device.imageINFO.maxWidth, self.device.imageINFO.maxHeight
        cam.start_capture()
        while True:
            image = cam.retrieve_buffer()
            if image:
                cv_image = np.frombuffer(bytes(image.getData()), dtype=np.uint16).reshape( (height, width) )
                cv2.imshow('frame',cv_image)
                c = cv2.waitKey(1)
                #dynamic Range Printout (adjusting factor from 16 to 12bit)
                minpixel=np.amin(cv_image)*(1/16)
                maxpixel=np.amax(cv_image)*(1/16)
                pixelrange=maxpixel-minpixel
                self.o_queue.put(pixelrange)
                if c == 13:
                    self.save_image(image)
                elif c == 27:
                    cam.stop_capture()
                    cam.close()
                    break
                else:
                    continue
            else:
                continue
    '''
    def live_stream(self, dr_option=False,):
        """sets up a livestream with dynamic range printout (T/F)"""
        cam = self.device
        cam.start_capture()
        while True:
            try:
                image = cam.retrieve_buffer()
            except:
                image = False
            if image:
                cv_image = np.frombuffer(bytes(image.getData()), dtype=np.uint16)
                cv_image = cv_image.reshape( (cam.imageINFO.maxHeight, cam.imageINFO.maxWidth) )
                cv2.imshow('frame',cv_image)
                cv2.waitKey(1)
                #dynamic Range Printout (adjusting factor from 16 to 12bit)
                if dr_option==True:
                    minpixel=np.amin(cv_image)*(1/16)
                    maxpixel=np.amax(cv_image)*(1/16)
                    pixelrange=maxpixel-minpixel
                    print(pixelrange)
            else:
                continue
    '''
        
    def take_photo(self):
        """ Start capturing and retrieve an image from the buffer.
        
        Returns
        -------
        image : obj
            A PyCapture2.Image object which includes the image data.
        """
        cam = self.device
        image = cam.take_photo()
        self.save_image(image, [])
        
    def save_image(self, image, args=[]):
        """ Callback from start_capture, saves the image.  
        
        Parameters
        ----------
        image : pc2.image
            The image object.
        args : tuple
            This is just here because pc2 will pass it into the callback.
        """
        # XXX for some reason the image object doesn't like being passed through
        # a queue so we have to save it directly here
        if args:
            if self.shot < args:
                
                meta = self.create_meta()
                raw = image.getData()
                
                data = {'raw' : raw,
                        'meta' : meta,
                        'save' : True}
                self.shot += 1
                self.r_queue.put(data)                
            else:
                while True:
                    if self.r_queue.qsize() == 0:
                        print('\nStream Finished')
                        self.device.stop_capture()   
                        break
        else:
            meta = self.create_meta()
            raw = image.getData()
            
            data = {'raw' : raw,
                    'meta' : meta,
                    'save' : True}
            self.shot += 1
            self.r_queue.put(data)   
            
        # Note we have the option to directly save the image here using 
        # image.save and it runs at 10 Hz but only on an ssd

    def get_datatype(self):
        """ Return the type of data. """
        return "IMAGE"
    
    def get_type(self):
        """ Return the instrument type. """
        return "Camera"

    def create_meta(self):
        meta = super(Camera, self).create_meta()
        meta['pixel'] = [self.device.imageINFO.maxWidth, self.device.imageINFO.maxHeight]
        return meta