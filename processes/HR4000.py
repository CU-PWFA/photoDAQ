#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:03:07 2018

@author: robert
"""

from processes.streamProcess import StreamProcess
import time
import daq
import numpy as np

class HR4000(StreamProcess):
    """ Process class for the HR4000 spectrometer. """       
    def capture_thread(self, r_queue):
        """ Continually quieres the spectrometer for new spectra. 
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place spectrums in.
        """
        while self.streaming:
            raw = self.device.get_spectrum()  
            meta = self.create_meta()
            data = {'lambda' : raw[0, :],
                    'I' : raw[1, :]}
            if self.save:
                response = 'save'
            else: 
                response = 'output'
            rsp = daq.Rsp(response, info=data, meta=meta)  
            self.r_queue.put(rsp)
            
            self.shot += 1
            if self.shot == self.numShots:
                self.save = False        
    
    def get_datatype(self):
        """ Return the type of data. """
        return "SPEC"
    
    def get_type(self):
        """ Return the instrument type. """
        return "HR4000"
    
    def close(self):
        """ Close the instrument, ensure that the data stream stops first. """
        self.stop_stream()
        # XXX this might still break if the integration time is long
        time.sleep(0.1)
        super().close()
