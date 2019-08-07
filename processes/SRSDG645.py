#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 16:45:39 2018

@author: cu-pwfa
"""

from processes.process import Process
import daq

class SRSDG645(Process):
    def __init__(self, instr):
        """ Setup the conversion array. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        self.channels = ['T0', 'T1', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        self.index = {'T0':0, 'T1':1, 'A':2, 'B':3, 'C':4, 'D':5, 'E':6, 'F':7,
                      'G':8, 'H':9}
        self.save = False
        super().__init__(instr)
        
    def get_settings(self):
        """Place the current settings on the SDG into the response queue."""
        settings = {}
        sdg = self.device
        for i in range(10):
            # Output is only defined for T0, AB, BC, CD, EF, so set it the same for both
            ref, delay = sdg.get_delay(i)
            settings[self.channels[i]] = {
                    'delay' : delay,
                    'output' : sdg.get_output(int(i/2)),
                    'ref' : self.channels[ref],
                    'polarity' : sdg.get_polarity(int(i/2))
                    }
        meta = self.create_meta()
        if self.save: response = 'save'
        else: response = 'output'
        rsp = daq.Rsp(response, settings, meta)
        self.r_queue.put(rsp)
        
    def save_settings(self):
        """ Set save to true and place the settings in the response queue. """
        self.save = True
        self.get_settings()
        self.save = False
        
    def set_settings(self, settings, save=False):
        """ Set the delay settings for a one or more channels.
        
        Parameters
        ----------
        settings : dict
            The dictionary containing the settings.
        save : bool, optional
            Specify if the new settings should be saved to file.
        """
        sdg = self.device
        for key in settings:
            delay = settings[key]['delay']
            output = settings[key]['output']
            ref = settings[key]['ref']
            polarity = settings[key]['polarity']
            sdg.set_delay([ref, key, delay])
            if key == 'T0':
                sdg.set_output(['T0', output], pol=polarity)
            elif key == 'A':
                sdg.set_output(['AB', output], pol=polarity)
            elif key == 'C':
                sdg.set_output(['CD', output], pol=polarity)
            elif key == 'E':
                sdg.set_output(['EF', output], pol=polarity)
            elif key == 'G':
                sdg.set_output(['GH', output], pol=polarity)
        
        if save:
            meta = self.create_meta()
            rsp = daq.Rsp('save', settings, meta)
            self.r_queue.put(rsp)
            
    def set_chA_delay(self, delay):
        """ Set the delay for channel A keeping the same reference. 
        
        Parameters
        ----------
        delay : float
            The delay in seconds for the channel.
        """
        sdg = self.device
        ref, temp = sdg.get_delay(2)
        ref = self.channels[ref]
        sdg.set_delay([ref, 'A', delay])
        
    def set_chB_delay(self, delay):
        """ Set the delay for channel A keeping the same reference. 
        
        Parameters
        ----------
        delay : float
            The delay in seconds for the channel.
        """
        sdg = self.device
        ref, temp = sdg.get_delay(3)
        ref = self.channels[ref]
        sdg.set_delay([ref, 'B', delay])
        
    def set_chC_delay(self, delay):
        """ Set the delay for channel A keeping the same reference. 
        
        Parameters
        ----------
        delay : float
            The delay in seconds for the channel.
        """
        sdg = self.device
        ref, temp = sdg.get_delay(4)
        ref = self.channels[ref]
        sdg.set_delay([ref, 'C', delay])
               
    def get_datatype(self):
        """Return the type of data. """
        return "SET"
            
    def get_type(self):
        """ Return the instrument type. """
        return "SRSDG645"