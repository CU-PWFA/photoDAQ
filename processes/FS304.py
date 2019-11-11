#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 15:24:24 2019

@author: robert
"""

from processes.streamProcess import StreamProcess
import time
import daq

class FS304(StreamProcess):
    """ Process class for the 304 FS TMP. """
    def __init__(self, instr):
        """ For parameters see the parent method. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        self.sampleDelay = 0.2
        super().__init__(instr)
        self.delay = 0.05
        
    def capture_thread(self, r_queue):
        """ Continually quieres the turbo molecular pump for power. 
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place the pressure in.
        """
        while self.streaming:
            raw = {}
            raw['status'] = self.device.get_status()
            raw['power'] = self.device.get_power()
            raw['frequency'] = self.device.get_driving_frequency()
            raw['temperature'] = self.device.get_temperature()
            raw['error'] = self.device.get_error()
            meta = self.create_meta()
            if self.save: response = 'save'
            else: response = 'output'
            rsp = daq.Rsp(response, info=raw, meta=meta)
            self.r_queue.put(rsp)
            
            self.shot += 1
            if self.shot == self.numShots:
                self.save = False
            time.sleep(self.sampleDelay)
    
    def set_sample_delay(self, delay):
        """ Set the sample delay. 
        
        Parameters
        ----------
        delay : double
            The sample delay in ms.
        """
        self.sampleDelay = delay/1000.
    
    def get_datatype(self):
        """ Return the type of data. """
        return "SET"
    
    def get_type(self):
        """ Return the instrument type. """
        return "FS304"