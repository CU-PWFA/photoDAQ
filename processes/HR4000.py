#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:03:07 2018

@author: robert
"""

from processes.process import Process
import threading

class HR4000(Process):
    """ Process class for the HR4000 spectrometer. """
    def __init__(self, name, adr, c_queue, r_queue, o_queue):
        """ init method. """
        self.streaming = False
        self.shot = 0
        self.numShots = 0
        self.lock = threading.Lock()
        # Needs to ocur last, starts infinite queue loop
        super().__init__(name, adr, c_queue, r_queue, o_queue)
        
    def start_stream(self, save=False): 
        """ Start streaming spectra to the save process. 
        
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
        args = (self.r_queue, self.streaming)
        self.c_thread = threading.Thread(target=self.capture_thread, args=args)
        self.c_thread.setDaemon(True)
        self.c_thread.start()
        
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

