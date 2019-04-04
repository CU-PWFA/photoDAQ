#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:02:27 2018

@author: robert
"""

from processes.process import Process
import daq

class KA3005P(Process):
    """ Process class for the KA3005P power supply. """
    def __init__(self, instr):
        """ For parameters see the parent method. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        self.delay = 0.05
        super().__init__(instr)
    
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
        rsp = daq.Rsp('save', {'voltage': v}, meta)
        self.r_queue.put(rsp)
        self.shot += 1
        
