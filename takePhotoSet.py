#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 15:07:54 2018

@author: cu-pwfa
"""

import PyCapture2 as pc2
import globalVAR as Gvar
import datetime as dt
import os

# Connect to Camera
bus = pc2.BusManager()
if not bus.getNumOfCameras():
    print('\nNo Cameras Detected.\n')
    exit()
    
cam = pc2.Camera()
cam.connect(bus.getCameraFromIndex(0))

SET = True
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
        
    while True:
        try:
            numOfPhotos = int(input('\nNumber of Photos: '))
            break
        except:
            print('\nInvalid Answer')
            
    dataSetDesc = input('\nData Set Description: ')

    Gvar.takePhotoSet(cam, numOfPhotos, dataSetDesc)
    
    SET = Gvar.promptREPEAT()
    
cam.disconnect()   
