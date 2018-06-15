#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 16:35:50 2018

@author: robert
"""

import numpy as np
import time

PS = {}
OS = {}
voltages = []

def setup(instr):
    global PS
    global OS
    global voltages
    PS = instr['KA3005P']
    OS = instr['TDS2024C']
    
    N = 160
    voltages = np.linspace(4.00, 30.00, N)

    PS.turn_on()
    OS.acquire_off()
    OS.set_acquisition_stop("SEQuence")
    OS.set_acquisition_mode("AVErage")
    OS.set_average_num(4)

def measure(i):
    PS.set_voltage(voltages[i])
    time.sleep(0.1) # Give the power supply enough time to set the voltage
    OS.acquire_on()
    time.sleep(1)
    t, y, pre = OS.retrieve_current_waveform()
    ret = {
            'KA3005P' : {
                    'meta'      : {},
                    'voltage'   : voltages[i]
                    },
            'TDS2024C' : {
                    't'         : t,
                    'y'         : y,
                    'meta'      : pre
                    }
            }
    return ret
  