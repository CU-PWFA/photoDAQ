#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 15:33:16 2018

@author: robert
"""

from processes.process import Process
import PyCapture2 as pc2
import datetime

class Camera(Process):
    """ Process class for a camera. """
    def save_stream(self, numShots=None):
        """ Save images from the camera as they come in. """        
        cam = self.device
        cam.start_capture(self.save_image, numShots)
        
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
        if args:
            if self.shot < args:

                ts = image.getTimeStamp()
                # ts is not currently being used for the time stamp meta data,
                # though it is a more accurate time stamp than the one being 
                # used in the create_meta() function
                
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