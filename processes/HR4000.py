#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:03:07 2018

@author: robert
"""

from processes.process import Process

class HR4000(Process):
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

