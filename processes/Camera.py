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
import threading

class Camera(Process):
    """ Process class for a camera. """
    def __init__(self, name, adr, c_queue, r_queue, o_queue):
        """ init method. """
        self.streaming = False
        self.shot = 0
        self.numShots = 0
        self.lock = threading.Lock()
        # Needs to ocur last, starts infinite queue loop
        super().__init__(name, adr, c_queue, r_queue, o_queue)
    
    def start_stream(self, save=False):
        """ Start streaming images into the save and post process. 
        
        Parameters
        ----------
        save : bool, optional
            Set if the stream should be saved or not, defaults to False.
        """
        cam = self.device
        if not self.streaming:
            self.save = save
            cam.start_capture(self.save_image)
            self.streaming = True
            #self.create_capture_thread()
        
    def stop_stream(self):
        """ Stop streaming images into the save and post process. """
        cam = self.device
        if self.streaming:
            self.lock.acquire()
            cam.stop_capture()
            self.streaming = False
            self.lock.release()
    
    def save_stream(self, numShots):
        """ Save the specified number of shots from the stream. 
        
        Parameters
        ----------
        numShots : int
            The number of shots to save. 
        """
        self.shot = 0
        self.numShots = numShots
        if self.streaming:
            self.save = True
        else:
            self.start_stream(True)    
        
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
        self.lock.acquire()
        meta = self.create_meta()
        raw = image.getData()
            
        data = {'raw' : raw,
                'meta' : meta,
                'save' : self.save}
        self.shot += 1
        self.r_queue.put(data)
        if self.shot == self.numShots:
            self.save = False
        self.lock.release()
            
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