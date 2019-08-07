#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:01:02 2018

@author: robert
"""

from processes.process import Process
import daq

class TDS2024C(Process):
    """ Process class for the TDS2024C. """
    def get_datatype(self):
        """ Return the type of data. """
        return "TRACE"
    
    def get_type(self):
        """ Return the device type. """
        return "TDS2024C"
    
    def save_waveform(self, chan=None):
        """ Save the current waveform to disk. """
        t, y, pre = self.device.retrieve_current_waveform()
        meta = self.create_meta()
        if chan != None:
            meta['Channel'] = chan
        for name in pre:
            meta[name] = pre[name]
        data = {'meta' : meta,
                't' : t,
                'y' : y}
        rsp = daq.Rsp('save', data, meta)
        self.shot += 1
        self.r_queue.put(rsp)