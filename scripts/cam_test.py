#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 10:21:46 2018

@author: robert
"""

import time

cam = {}

def setup(instr):
    global cam
    cam = instr['Camera']
    cam.start_capture()
    
def measure(i):
    image = cam.retrieve_buffer()
    ret = {
            'Camera' : {
                    'meta'  : {},
                    'image' : image
                    }
            }
    return ret
