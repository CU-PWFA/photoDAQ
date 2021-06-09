#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 11:32:44 2021

@author: jamie

Source module: https://github.com/pyepics/newportxps
"""

from processes.streamProcess import StreamProcess
import time
import daq


class XPS(StreamProcess):
    """ Process class for the XPS controller. """
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
        
    def get_settings(self):
        """ """
        settings = {}
        xps      = self.device
        current_position1 = xps.get_stage1_position()
        
        
        settings       = {"current_pos"          :current_position1, 
                          }  
        return settings
    
    def home_group1(self):
        xps = self.device
        xps.home_group1()
        self.update_position1()

    def home_group2(self):
        xps = self.device
        xps.home_group2()
        self.update_position2()
 
    def move_stage1_abs(self, pos):
        xps = self.device
        xps.move_stage1_abs(pos)
        self.update_position1()

    def move_stage1_rel(self, pos):
        xps = self.device
        xps.move_stage1_rel(pos)
        self.update_position1()

    def update_position1(self):
        xps = self.device
        pos_readback = xps.get_stage1_position()
        rsp = daq.Rsp('driver', info={'pos_readback': pos_readback})
        self.r_queue.put(rsp)

    def update_position2(self):
        xps = self.device
        pos_readback = xps.get_stage2_position()
        rsp = daq.Rsp('driver', info={'pos_readback': pos_readback})
        self.r_queue.put(rsp)
    
    def update_status1(self):
        xps = self.device
        status = xps.get_group1_status()
        rsp = daq.Rsp('driver', info={'status': status})
        self.r_queue.put(rsp)

    def update_status2(self):
        xps = self.device
        status = xps.get_group2_status()
        rsp = daq.Rsp('driver', info={'status': status})
        self.r_queue.put(rsp)
        
    def capture_thread(self, r_queue):
        """ Continually quieres the XPS controller for position. 
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place the position in.
        """
        while self.streaming:
            raw = self.get_settings()
            
            if self.save: response = 'save'
            else: response = 'driver'
            rsp = daq.Rsp(response, info=raw)
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
        return "XPS"