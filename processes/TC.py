#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 14:33:21 2019

@author: robert
"""

from processes.streamProcess import StreamProcess
import time
import daq

class TC(StreamProcess):
    """ Process class for the timing controller. """
    def __init__(self, instr):
        """ For parameters see the parent method. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        self.sampleDelay = 0.05
        self.FR = False
        super().__init__(instr)
        
    def capture_thread(self, r_queue):
        """ Continually quieres the timing controller for the shot number. 
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place the shot number in.
        """
        while self.streaming:
            raw = self.device.get_shot()
            if raw is None:
                continue
            meta = self.create_meta()
            response = 'output'
            rsp = daq.Rsp(response, info=raw, meta=meta)
            self.r_queue.put(rsp)
            
            self.shot += 1
            if self.shot == self.numShots and raw == self.numShots:
                self.save = False
                self.stop_stream()
            time.sleep(self.sampleDelay)
    
    def get_datatype(self):
        """ Return the type of data. """
        return "SET"
    
    def get_type(self):
        """ Return the instrument type. """
        return "TC"
    
    def is_free_running(self):
        """ Check if the TC is free running. """
        if self.FR:
            meta = self.create_meta()
            response = 'output'
            rsp = daq.Rsp(response, info=raw, meta=meta)
            self.r_queue.put(rsp)

