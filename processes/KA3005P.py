#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:02:27 2018

@author: robert
"""

from processes.process import Process

class KA3005P(Process):
    """ Process class for the KA3005P power supply. """
    def __init__(self, name, adr, c_queue, r_queue, o_queue):
        """ For parameters see the parent method. """
        self.delay = 0.05
        super().__init__(name, adr, c_queue, r_queue, o_queue)
    
    def get_datatype(self):
        """ Return the type of data. """
        return "SET"
    
    def get_type(self):
        """ Return the instrument type. """
        return "KA3005P"
    
    def set_record_voltage(self, v):
        """ Set the voltage and save the value. 
        
        Parameters
        ----------
        v : float
            The voltage to set the power supply to.
        """
        self.device.set_voltage(v)
        meta = self.create_meta()
        response = {'save' : True,
                    'meta' : meta,
                    'voltage' : v}
        self.shot += 1
        self.r_queue.put(response)
