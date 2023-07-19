#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 12:23:14 2018

@author: cu-pwfa
"""

import daq
import time


DAQ = daq.Daq(desc='Test Descritpion')

DAQ.connect_instr('Camera', 17571186)

time.sleep(5)

DAQ.send_command(DAQ.command_queue[17571186], 'take_photo')

time.sleep(5)

DAQ.turn_off_daq()
