#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 15:33:16 2018

@author: robert
"""

from processes.process import Process
import PyCapture2 as pc2
import time

class Camera(Process):
    """ Process class for a camera. """
    def save_stream(self):
        """ Save images from the camera as they come in. """
        cam = self.device
        cam.start_capture(self.save_image)
        
    def save_image(self, image, args):
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
        raw = image.getData()
        meta = self.create_meta()
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
