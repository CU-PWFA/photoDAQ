#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 15:33:16 2018

@author: robert
"""

from processes.streamProcess import StreamProcess
import numpy as np
import daq
import time

class Camera(StreamProcess):
    """ Process class for a camera. """
    def __init__(self, device):
        """ init method. """
        super().__init__(device)
    
    def start_stream(self, save=False):
        """ Start streaming images 
        
        Parameters
        ----------
        save : bool, optional
            Set if the stream should be saved or not, defaults to False.
        """
        if not self.streaming:
            self.device.start_capture()
            self.save = save
            self.streaming = True
            self.create_capture_thread()
            
    def stop_stream(self):
        """ Stop streaming from the camera. """
        if self.streaming:
            # stop_capture throws an error if the device isn't capturing
            self.device.stop_capture() 
        self.streaming = False
    
    def capture_thread(self, r_queue):
        """ Continually queries the camera for images.  
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place the pressure in.
        """
        # The image object doesn't like being passed through a queue
        # we have to process it here
        while self.streaming:
            # This call blocks and does not release the GIL, no commands will
            # make it through until a buffer is retrieved
            # This is a problem with an external trigger, the save command
            # wont make it through until after the first shot
            start = time.clock()
            meta = self.create_meta()
            image = self.device.retrieve_buffer()
            if image is None:
                print('Image dropped, shot %d' % self.shot)
                raw = None
            else:
                raw = bytes(image.getData())
                if self.save: response = 'save'
                else: response = 'output'
                #raw = np.random.randint(0, 256, size=(6000000), dtype=np.uint16)
                rsp = daq.Rsp(response, raw, meta)
            self.r_queue.put(rsp)
            end = time.clock()
            print("Start:", start, "End:", end, "Duration:", end-start)
            
            self.shot += 1
            if self.shot == self.numShots:
                self.save = False
                
                self.stop_stream() # For releasing the GIL
            time.sleep(0.01) # Guarantee the GIL is released
            
        # Note we have the option to directly save the image here using 
        # image.save and it runs at 10 Hz but only on an ssd

    def set_trigger_settings(self, enable):
        """ Override the device set trigger to stop streaming. """
        self.stop_stream()
        self.device.set_trigger_settings(enable)

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