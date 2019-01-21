#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:03:07 2018

@author: robert
"""

from processes.srtreamProcess import StreamProcess

class HR4000(StreamProcess):
    """ Process class for the HR4000 spectrometer. """       
    def capture_thread(self, r_queue, streaming):
        """ Continually quieres the spectrometer for new spectra. 
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place spectrums in.
        streaming : bool
            Thread exit flag, exits if False.
        """
        while self.streaming:
            raw = self.device.get_spectrum()
            meta = self.create_meta()
            
            data = {'lambda' : raw[0, :],
                    'I' : raw[1, :],
                    'meta' : meta,
                    'save' : self.save}
            self.shot += 1
            self.r_queue.put(data)
            if self.shot == self.numShots:
                self.save = False
        
    def save_spectrum(self):
        """ Save the current spectrum to disk. """
        w, a = self.device.get_spectrum()
        meta = self.create_meta()
        data = {'save' : True,
                'meta' : meta,
                't' : w,
                'y' : a}
        self.shot += 1
        self.r_queue.put(data)
        
    
    def get_datatype(self):
        """ Return the type of data. """
        return "TRACE"
    
    def get_type(self):
        """ Return the instrument type. """
        return "HR4000"

