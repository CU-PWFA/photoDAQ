#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 15:33:16 2018

@author: robert
"""

from processes.process import Process
import PyCapture2 as pc2
import file
import time
import threading

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
        dirName = file.get_dirName('IMAGE', self.dataset)
        serial = self.device.serialNum
        fileName = file.get_fileName(serial, self.dataset, self.shot)
        name = dirName + fileName + '.tiff'
        start = time.clock()
        image.save(bytes('test.tiff', 'utf-8'), pc2.IMAGE_FILE_FORMAT.TIFF)
        # Getting the data is really fast, but it needs to be saved in a different process
        #data = image.getData()
        # Let the save thread handle adding metadata
        self.s_queue.put(name)
        self.shot += 1
        
        #image.getData()
        end = time.clock()
        print("Duration", end-start)
        
    def save_thread(self, s_queue, r_queue):
        """ Waits for data to be saved, should be overwritten in most cases. 
        
        Parameters
        ----------
        s_queue : queue.Queue
            Queue to recieve the save data in.
        r_queue : mp.Queue
            The response queue to place responses in.
        """
        while True:
            name = s_queue.get()
            meta = self.create_meta()
            #file.add_image_meta(name, meta)
            #self.r_queue.put(name)
            s_queue.task_done()
        
    def get_datatype(self):
        """ Return the type of data. """
        return "IMAGE"
    
    def get_type(self):
        """ Return the instrument type. """
        return "Camera"
