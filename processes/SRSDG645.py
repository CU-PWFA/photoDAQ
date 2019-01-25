#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 16:45:39 2018

@author: cu-pwfa
"""

from processes.process import Process

class SRSDG645(Process):
    def __init__(self, name, adr, c_queue, r_queue, o_queue):
        """ Setup the conversion array. """
        self.channels = ['T0', 'T1', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        self.index = {'T0':0, 'T1':1, 'A':2, 'B':3, 'C':4, 'D':5, 'E':6, 'F':7,
                      'G':8, 'H':9}
        self.save = False
        super().__init__(name, adr, c_queue, r_queue, o_queue)
        
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
        data = {'save' : self.save,
                'meta' : meta,
                'data' : settings }
        self.r_queue.put(data)
        
    def save_settings(self):
        """ Set save to true and place the settings in the response queue. """
        self.save = True
        self.get_settings()
        self.save = False
        
    def set_settings(self, settings, save=False):
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
            data = {'save' : True,
                    'meta' : meta,
                    'data' : settings } 
            self.r_queue.put(data)
               
    def get_datatype(self):
        """Return the type of data. """
        return "SET"
            
    def get_type(self):
        """ Return the instrument type. """
        return "SRSDG645"