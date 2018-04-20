#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 15:07:54 2018

@author: cu-pwfa
"""

import globalVAR as Gvar
import Camera as C
import datetime as dt
import os

# Initialize Camera
Cam = C.Camera(0)

SET = Cam.cam
while SET:
    
    # Identify DataSetNumber
    dataSetNum = Gvar.getDataSetNum()
    
    # Determine Date and Make Necessary Directories
    date = dt.datetime.now()
    YEAR = date.year
    MONTH = Gvar.stringTIME(date.month)
    DAY = Gvar.stringTIME(date.day)
    
    if not os.path.exists('IMAGES/year_{}'.format(YEAR)):
        os.makedirs('IMAGES/year_{}'.format(YEAR))
        os.makedirs('META/year_{}'.format(YEAR))
    if not os.path.exists('IMAGES/year_{}/month_{}'.format(YEAR, MONTH)):
        os.makedirs('IMAGES/year_{}/month_{}'.format(YEAR, MONTH))
        os.makedirs('META/year_{}/month_{}'.format(YEAR, MONTH))
    if not os.path.exists('IMAGES/year_{}/month_{}/day_{}'.format(YEAR, MONTH, DAY)):
        os.makedirs('IMAGES/year_{}/month_{}/day_{}'.format(YEAR, MONTH, DAY))
        os.makedirs('META/year_{}/month_{}/day_{}'.format(YEAR, MONTH, DAY))
    if not os.path.exists('IMAGES/year_{}/month_{}/day_{}/{}'.format(YEAR, MONTH, DAY, dataSetNum)):
        os.makedirs('IMAGES/year_{}/month_{}/day_{}/{}'.format(YEAR, MONTH, DAY, dataSetNum))
    
    Cam.takePhotoSet()
    
    SET = Gvar.promptREPEAT()

if Cam.cam:    
    Cam.disconnect()
