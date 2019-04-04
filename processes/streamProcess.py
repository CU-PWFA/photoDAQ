#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 16 11:54:41 2019

@author: robert
"""

from processes.process import Process
import threading

class StreamProcess(Process):
    """ Process class for streaming devices. """
    def __init__(self, instr):
        """ init method. """
        self.streaming = False
        self.shot = 0
        self.numShots = 0
        # Needs to ocur last, starts infinite queue loop
        super().__init__(instr)
        
    def start_stream(self, save=False): 
        """ Start streaming data from the device. 
        
        Parameters
        ----------
        save : bool, optional
            Set if the stream should be saved or not, defaults to False.
        """
        if not self.streaming:
            self.save = save
            self.streaming = True
            self.create_capture_thread()
            
    def stop_stream(self):
        """ Stop streaming images into the save and post process. """
        self.streaming = False
        
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
            
    def create_capture_thread(self):
        """ Create a dedicated thread to handle data acquisition. """
        args = (self.r_queue, )
        self.c_thread = threading.Thread(target=self.capture_thread, args=args)
        self.c_thread.setDaemon(True)
        self.c_thread.start()
        
    def capture_thread(self, r_queue):
        """ Capture data loop, should be overwritten by child classes.
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place spectrums in.
        """
        pass
    
    def close(self):
        """ Streaming instruments need to stop streaming before they close. """
        self.stop_stream()
        super().close()