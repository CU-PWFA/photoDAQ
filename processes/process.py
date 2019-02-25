#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 14:48:25 2018

@author: robert
"""

import time
import daq

class Process():
    """ A class that handles the main loop for an instrument. """
    def __init__(self, instr):
        """ Initialize the instrument and start the main loop. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        self.delay = 0.0
        self.instr = instr
        self.c_queue = instr.command_queue
        self.r_queue = instr.response_queue
        self.dataset = instr.dataset
        self.connect_instr()
        # Internal shot tracker
        self.shot = 0
        self.command_loop()
    
    def connect_instr(self):
        """ Create the instrument class and connect to the instrument. """
        instr = self.instr
        device = instr.device_cls(instr.address)
        device.type = instr.device_type
        self.device = device
        rsp = daq.Rsp('connected')
        self.r_queue.put(rsp)
        
    def command_loop(self):
        """ Check the queue for commands and execute them. """
        while True:
            cmd = self.c_queue.get()
            command = cmd.command
            # Always check process class first to allow overrides to be placed there
            if hasattr(self, command):
                func = getattr(self, command)
                func(*cmd.args, **cmd.kwargs)
            elif hasattr(self.device, command):
                func = getattr(self.device, command)
                func(*cmd.args, **cmd.kwargs)
            self.c_queue.task_done()
            time.sleep(self.delay)
            # End the process when the device disconnects
            if command == 'close':
                break
                
    def create_meta(self):
        """ Create the meta data object for the current shot. 
        
        """
        meta = {}
        meta['INSTR'] = self.get_type()
        meta['ID'] = self.device.ID
        meta['Serial number'] = self.device.serialNum
        #meta['Timestamp'] = Gvar.get_timestamp()
        meta['Data set'] = self.dataset
        meta['Shot number'] = self.shot
        meta['Data type'] = self.get_datatype()
        return meta
    
    def get_datatype(self):
        """ Return the type of data. """
        return "DATA"
    
    def get_type(self):
        """ Return the device type. """
        return "Generic"
    
    def set_dataset(self, dataset):
        """ Set the dataset number as an attribute. 
        
        Parameters
        ----------
        dataSet : int
            The data set number.
        """
        self.dataset = dataset
        self.shot = 0
        
    def save_stream(self):
        """ Base function to be overwritten by classes that need to save data. """
        pass
        
    def close(self):
        """" Close the device and send an exit code to the response queue. """
        self.device.close()
        rsp = daq.Rsp('exit')
        self.r_queue.put(rsp)
        