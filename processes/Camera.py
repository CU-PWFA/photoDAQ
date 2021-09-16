#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 15:33:16 2018

@author: robert
"""

from processes.streamProcess import StreamProcess
import daq
import time
import PySpin

class Camera(StreamProcess):
    """ Process class for a camera. """
    def __init__(self, device):
        """ init method. """
        super().__init__(device)
        
    def connect_info(self):
        """ Gather data for the UI to use. """
        cam = self.device
        data = {'ShutterMin' : cam.get_min_shutter(),
                'GainMax' : cam.get_max_gain(),
                'SensorHeight' : cam.get_sensor_height(),
                'SensorWidth' : cam.get_sensor_width(),
                'Shutter' : cam.get_shutter(),
                'Gain' : cam.get_gain(),
                'Framerate' : cam.get_framerate(),
                'OffsetX' : cam.get_offsetX(),
                'OffsetY' : cam.get_offsetY(),
                'Height' : cam.get_height(),
                'Width' : cam.get_width()}
        return data
    
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
        while self.streaming:
            # This call blocks and does not release the GIL, no commands will
            # make it through until a buffer is retrieved
            # This is a problem with an external trigger, the save command
            # wont make it through until after the first shot
            #start = time.clock()
            meta = self.create_meta()
            image = self.device.retrieve_buffer()
            if image is None:
                print('Image dropped, shot %d' % self.shot)
                raw = None
            else:
                converted = image.Convert(PySpin.PixelFormat_Mono16)
                raw = converted.GetNDArray()
                if self.save:
                    response = 'save'
                else: 
                    response = 'output'
                #raw = np.random.randint(0, 256, size=(2000, 2000), dtype=np.uint16)
                rsp = daq.Rsp(response, raw, meta=meta)
                self.r_queue.put(rsp)
                
            #end = time.clock()
            #print("Start:", start, "End:", end, "Duration:", end-start)
            if image is not None:
                image.Release()
            
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
        meta['pixel'] = [self.device.get_width(), self.device.get_height()]
        return meta