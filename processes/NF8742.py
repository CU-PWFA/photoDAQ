#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 10:17:00 2019

@author: cu-pwfa
"""
from processes.streamProcess import StreamProcess
import daq
import time
class NF8742(StreamProcess):
    """ Process class for the KA3005P power supply. """
    def __init__(self, instr):
        """ For parameters see the parent method. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        super().__init__(instr)
        self.sampleDelay = 0.05
        self.slave = "1>"
        self.axes  = [1, 2]
        
    def set_slave_axis(self, axes, slave):
        self.axes  = axes
        self.slave = slave
    def get_datatype(self):
        """ Return the type of data. """
        return "SET"
    
    def get_type(self):
        """ Return the instrument type. """
        return "NF8742"
    
    def get_settings(self):
        """Place the current settings on the SDG into the response queue."""
        
        settings = {}
        nf       = self.device
        x_position     = nf.get_position(self.axes[0], self.slave)
        y_position     = nf.get_position(self.axes[1], self.slave)
        velocity       = nf.get_velocity(self.axes[0], self.slave)
        acceleration   = nf.get_acceleration(axes[0], self.slave)
        x_home         = nf.get_home(self.axes[0], self.slave)
        y_home         = nf.get_home(self.axes[1], self.slave)
        
        
        settings       = {"x"          : x_position, 
                          "y"          : y_position,
                        "velocity"     : velocity, 
                        "acceleration" : acceleration, 
                        "x_home"       : x_home, 
                        "y_home"       : y_home}  
        return settings
        
    def capture_thread(self, r_queue, axis, slave = ""):
        """ Continually quieres the pressure gauge for the pressure. 
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place the pressure in.
        """
        while self.streaming:
            raw = self.get_settings()
            response = 'driver'
            rsp = daq.Rsp(response, info=raw)
            self.r_queue.put(rsp)
            time.sleep(self.sampleDelay)