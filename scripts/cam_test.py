#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 10:21:46 2018

@author: robert
"""

import time

devices = {}

def setup(instr):
    global devices
    devices = instr
    for name in instr:
        if instr[name].type == 'Camera':
            cam = instr[name]
            cam.start_capture()
    
def measure(i):
    ret = {}
    for name in devices:
        if devices[name].type == 'Camera':
            cam = devices[name]
            image = cam.retrieve_buffer()
            ret[name] = {
                        'meta'  : {},
                        'image' : image
                        }
    return ret
