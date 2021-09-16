#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 12:23:14 2018

@author: cu-pwfa
"""

import sys
sys.path.append('../')
import daq
import file
import globalVAR as Gvar
import visa
import numpy as np
import time
from random import randint
import PyCapture2 as pc2


DAQ = daq.Daq(desc='Test Descritpion')

DAQ.connect_instr('Camera', 17571186)

time.sleep(5)

DAQ.send_command(DAQ.command_queue[17571186], 'take_photo')

time.sleep(5)

DAQ.turn_off_daq()
