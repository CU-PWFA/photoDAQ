#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 11:23:09 2018

@author: cu-pwfa
"""

import PyCapture2 as pc2
import datetime as dt
import os

def takePhoto(cam, path):
    yr, mth, day, cnt = path
    input('\nPress ENTER to take photo...')
    try:
        image = cam.retrieveBuffer()
        image.save(('IMAGES/year_%s/month_%s/day_%s/image_%s.tiff' % (yr, mth, day, cnt)).encode("utf-8"), pc2.IMAGE_FILE_FORMAT.TIFF)    
    except pc2.Fc2error as fc2Err:
        print('\nError retrieving buffer : ', fc2Err)    

# Detect Cameras
bus = pc2.BusManager()
numOfCam = bus.getNumOfCameras()
if not numOfCam:
    print('\nNo Cameras Detected.\n')
    exit()
 
# Connect to Cameras
c = pc2.Camera()
c.connect(bus.getCameraFromIndex(0))

# Determine Date and Make Necessary Directories
date = dt.datetime.now()
YEAR = date.year
MONTH = date.month
DAY = date.day

if not os.path.exists('IMAGES/year_{}'.format(YEAR)):
    os.makedirs('IMAGES/year_{}'.format(YEAR))
if not os.path.exists('IMAGES/year_{}/month_{}'.format(YEAR, MONTH)):
    os.makedirs('IMAGES/year_{}/month_{}'.format(YEAR, MONTH))
if not os.path.exists('IMAGES/year_{}/month_{}/day_{}'.format(YEAR, MONTH, DAY)):
    os.makedirs('IMAGES/year_{}/month_{}/day_{}'.format(YEAR, MONTH, DAY))
    
# Identify DataSetNumber
with open('Meta/last_DataSet.txt','r') as file:
    data = file.readlines()    
dataSetNum = data[5]

lastYEAR = int('20'+dataSetNum[0:2])
lastMONTH = int(dataSetNum[2:4])
lastDAY = int(dataSetNum[4:6])
lastDATA = int(dataSetNum[6:10])
            
# Prompt Photo Capture
if lastYEAR==YEAR:
    if lastMONTH==MONTH:
        if lastDAY==DAY:
            dataCNT=lastDATA+1
        else:
            dataCNT=0
    else:
        dataCNT=0
else:
    dataCNT=0
  
c.startCapture()
chk = True
while chk:
    path = [YEAR, MONTH, DAY, dataCNT]  
    takePhoto(c, path)
    while True:
        ans = input('\nDo you want to take another photo (y/n): ')
        if (ans=='y') or (ans=='Y') or (ans=='yes') or (ans=='Yes') or (ans=='YES'):
            dataCNT+=1
            break
        elif (ans=='n') or (ans=='N') or (ans=='no') or (ans=='No') or (ans=='NO'):
            chk=False
            break
        else:
            print('\nInvalid Response')
            continue
c.stopCapture()

# Advance Data Set Number
year = str(YEAR-2000)

if MONTH<10:
    month = '0'+str(MONTH)
else:
    month = str(MONTH)
    
if DAY<10:
    day = '0'+str(DAY)
else:
    day = str(DAY)
    

if dataCNT<1000:
    if dataCNT<100:
        if dataCNT<10:
            cnt = '000'+str(dataCNT)
        else:
            cnt = '00'+str(dataCNT)
    else:
        cnt = '0'+str(dataCNT)
else:
    cnt = str(dataCNT)
    
data[5] = year+month+day+cnt
with open('Meta/last_DataSet.txt','w') as file:
    file.writelines(data)
