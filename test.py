#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 13 16:32:45 2018

@author: robert
"""
import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)

from devices.device import Device
import PySpin

print(PySpin.System.GetInstance())
