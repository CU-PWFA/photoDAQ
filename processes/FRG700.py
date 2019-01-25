#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 16 11:50:29 2019

@author: robert
"""

from processes.streamProcess import StreamProcess
import time

class FRG700(StreamProcess):
    """ Process class for the KA3005P power supply. """
    def __init__(self, name, adr, c_queue, r_queue, o_queue):
        """ For parameters see the parent method. """
        self.delay = 0.0
        self.sampleDelay = 0.05
        super().__init__(name, adr, c_queue, r_queue, o_queue)
        
    def capture_thread(self, r_queue, streaming):
        """ Continually quieres the pressure gauge for the pressure. 
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place the pressure in.
        streaming : bool
            Thread exit flag, exits if False.
        """
        while self.streaming:
            raw = self.device.get_pressure()
            meta = self.create_meta()
            
            data = {'pressure' : raw,
                    'meta' : meta,
                    'save' : self.save}
            self.shot += 1
            self.r_queue.put(data)
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
        return "FRG700"

