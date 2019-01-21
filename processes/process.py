#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 14:48:25 2018

@author: robert
"""

import importlib
import time
import threading
import queue
import file
import globalVAR as Gvar

class Process():
    """ A class that handles the main loop for an instrument. """
    def __init__(self, name, adr, c_queue, r_queue, o_queue):
        """ Initialize the instrument and start the main loop. 
        
        Parameters
        ----------
        name : string
            The name of the instrument, must be a key in INSTR.
        adr : string
            The address of the instrument, will be passed to the constructor.
        c_queue : mp.Queue
            The command queue to place commands in.
        r_queue : mp.Queue
            The response queue to place responses in.
        o_queue : mp.Queue
            The queue to place messages in.
        """
        self.delay = 0.0
        self.c_queue = c_queue
        self.r_queue = r_queue
        self.o_queue = o_queue
        self.connect_instr(name, adr)
        # Internal shot tracker
        self.shot = 0
        self.command_loop()
    
    def connect_instr(self, name, adr):
        """ Create the instrument class and connect to the instrument. 
        
        Parameters
        ----------
        name : string
            The name of the instrument, must be a key in INSTR.
        adr : string
            The address of the instrument, will be passed to the constructor.
        """
        module = importlib.import_module('devices.' + name)
        instr_class = getattr(module, name)
        device = instr_class(adr)
        device.type = name
        self.device = device
        self.r_queue.put([device.serialNum, self.get_type()])
        
    def command_loop(self):
        """ Check the queue for commands and execute them. """
        while True:
            com = self.c_queue.get()
            # Always check process class first to allow overrides to be placed there
            if hasattr(self, com['command']):
                func = getattr(self, com['command'])
                func(*com['args'], **com['kwargs'])
            elif hasattr(self.device, com['command']):
                func = getattr(self.device, com['command'])
                func(*com['args'], **com['kwargs'])
            self.c_queue.task_done()
            time.sleep(self.delay)
            if com['command'] == 'close':
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
        
    def close(self):
        """" Close the device and send an exit code to the response queue. """
        self.device.close()
        self.r_queue.put('__exit__')
        