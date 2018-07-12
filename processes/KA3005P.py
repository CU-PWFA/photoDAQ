#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:02:27 2018

@author: robert
"""

from processes.process import Process

class KA3005P(Process):
    """ Process class for the KA3005P power supply. """
    def get_datatype(self):
        """ Return the type of data. """
        return "SET"
    
    def get_type(self):
        """ Return the instrument type. """
        return "KA3005P"

