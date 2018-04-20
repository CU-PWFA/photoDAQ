#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 11:23:09 2018

@author: cu-pwfa
"""

#########################################################################
#                                                                       #
#   This code allows the user to take photos from a single camera.      #
#   The photos are automatically placed in the appropriate directories  #
#   and the photo ID number is updated accordingly.                     #
#                                                                       #
#########################################################################

import datetime as dt
import os
import globalVAR as Gvar
import Camera as C

# Initialize Camera
Cam = C.Camera(0)

if Cam.cam:
    # Identify photo ID number
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

    Cam.takePhoto()
    
    Cam.disconnect()