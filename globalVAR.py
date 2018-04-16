#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 14:09:21 2018

@author: cu-pwfa
"""

import PyCapture2 as pc2
import datetime as dt
from time import sleep
import base64
import subprocess
import libtiff

def stringTIME(timeUNIT, powOfTen=1):
    if timeUNIT != 0:
        zeroSTRG = ''
        while powOfTen >= 0:
            if timeUNIT<10**powOfTen:
                zeroSTRG+='0'
            else:
                return zeroSTRG+str(timeUNIT)
            powOfTen-=1
    else:
        return '0'*(powOfTen+1)    

def writeNewDataSetNum():
    now = dt.datetime.now()
    year = str(now.year-2000)
    month = stringTIME(now.month)
    day = stringTIME(now.day)
    cnt = '0001'
    return int(year+month+day+cnt)
    

def getDataSetNum():
    ### This function reads the DataSetNumber from Meta/last_DataSet.txt 
    ### and compares it to today's date.  The function returns the relevant
    ### DataSetNumber, determined by either the .txt file or the date.
    with open('META/last_DataSet.txt','r') as file:
        data = file.readlines()    
    dataSetPrev = data[5]
    
    lastYEAR = int('20'+dataSetPrev[0:2])
    lastMONTH = int(dataSetPrev[2:4])
    lastDAY = int(dataSetPrev[4:6])
    
    now = dt.datetime.now()
    if lastYEAR==now.year:
        if lastMONTH==now.month:
            if lastDAY==now.day:
                dataSetNum = int(dataSetPrev)+1
            else:
                dataSetNum = writeNewDataSetNum()
        else:
            dataSetNum = writeNewDataSetNum()
    else:
        dataSetNum = writeNewDataSetNum()
        
    return dataSetNum

def advDataSetNum(dataSetNum):
    ### This function writes dataSetNum as the new DataSetNumber
    ### in Meta/last_DataSet.txt
    with open('META/last_DataSet.txt','r') as file:
        data = file.readlines()   
    
    data[5] = str(dataSetNum)
    
    with open('META/last_DataSet.txt','w') as file:
        file.writelines(data)

def promptREPEAT():
    SET = True
    while SET:
        ans = input('\nDo you want to take more photos? (y/n): ')
        if (ans=='y') or (ans=='Y') or (ans=='yes') or (ans=='Yes') or (ans=='YES'):
            return True
        elif (ans=='n') or (ans=='N') or (ans=='no') or (ans=='No') or (ans=='NO'):
            return False
        else:
            print('\nInvalid Response')
            continue

def writeTimeStamp(date):
    year = date.year
    month = stringTIME(date.month)
    day = stringTIME(date.day)
    hour = stringTIME(date.hour)
    minute = stringTIME(date.minute)
    sec = stringTIME(date.second)
    musec = stringTIME(date.microsecond, 5)
    TS = str(year)+'/'+month+'/'+day+'/'+hour+'/'+minute+'/'+sec+'/'+musec
    
    return TS
        
def writeMetaData(camName, dataSET, dateNOW, shotNUM, imageDESC):
    Dict = {}
    Dict['CamName'] = camName
    Dict['DatasetID'] = dataSET
    Dict['TimeStamp'] = writeTimeStamp(dateNOW)
    Dict['ShotNum'] = shotNUM
    Dict['Description'] = imageDESC
    
    return Dict

def writeMetaDataTxt(dataSetNum, imageDESC, serialNUM, succRATE, timeSTAMP):
    now = dt.datetime.now()
    year = now.year
    month = stringTIME(now.month)
    day = stringTIME(now.day)
    fileNAME = 'META/year_{}/month_{}/day_{}/meta_{}.txt'.format(year, month, day, dataSetNum)
    
    file = open(fileNAME, 'w')
    file.write('# Description of Data Set\n'
               ''+imageDESC+'\n\n'
               '# Camera(s) Used (Name: Serial Number)\n')
    for i in range(len(serialNUM)):
        file.write(camNAME[serialNUM[i]]+': '+serialNUM[i]+'\n')
    file.write('\n# Number of Successful Shots\n'
               '{} of {} successful shots\n\n'.format(succRATE[0]-succRATE[1], succRATE[0]))
    file.write('# Time Stamp of Each Image (year/month/day/hour/minute/second/microsecond)\n')
    for j in range(len(timeSTAMP)):
        if timeSTAMP[j]:
            TS = writeTimeStamp(timeSTAMP[j])
            file.write('shot {}: {}\n'.format(j+1, TS))
        else:
            file.write('shot {}: FAIL\n'.format(j+1))
    file.close()
        
def takePHOTO(cam):   
    setDESC = input('\nData Set Description: ')
    
    now = dt.datetime.now()
    year = stringTIME(now.year)
    month = stringTIME(now.month)
    day = now.day
    
    dataSetNum = getDataSetNum()
    
    camInfo = cam.getCameraInfo()
    serialNum = str(camInfo.serialNumber)
    camName = camNAME[serialNum]
    
    shotNumInt = 0
    shotFail = 0
    
    metaDATA = []
    dateSET = []
    SET = True  
    cam.startCapture()
    while SET:
        shotNumInt+=1
        shotNum = stringTIME(shotNumInt, 3)
        input('\nPress ENTER to take photo...')
        try:
            dateBFOR = dt.datetime.now()
            image = cam.retrieveBuffer()
            dateAFTR = dt.datetime.now()
            date = dateBFOR + 0.5*(dateAFTR-dateBFOR)
            dateSET.append(date)
            image.save(('IMAGES/year_%s/month_%s/day_%s/%s/%s_%s_%s.tiff' % (year, month, day, dataSetNum, camName, dataSetNum, shotNum)).encode("utf-8"), pc2.IMAGE_FILE_FORMAT.TIFF)    
            
            metaDATA.append(writeMetaData(camName, dataSetNum, date, shotNumInt, setDESC))
            
            SET = promptREPEAT()    
        except pc2.Fc2error as fc2Err:
            shotFail+=1
            dateSET.append(False)
            metaDATA.append(False)
            print('\nError retrieving buffer : ', fc2Err)
            SET = promptREPEAT()
    cam.stopCapture()
    
    for s in range(shotNumInt):
        if metaDATA[s]:
            shotNum = stringTIME(s+1, 3)
            dataDICT = metaDATA[s]
            dataBYTE = str(dataDICT).encode()
            dataBASE = str(base64.b64encode(dataBYTE), 'ascii')
            subprocess.call('tiffset -s 270 '+dataBASE+' IMAGES/year_{}/month_{}/day_{}/{}/{}_{}_{}.tiff'.format(year, month, day, dataSetNum, camName, dataSetNum, shotNum), shell=True)
    
    writeMetaDataTxt(dataSetNum, setDESC, [serialNum], [shotNumInt, shotFail], dateSET)
    
    advDataSetNum(dataSetNum)
    

def takePhotoSet(cam, numPHOTO, imageDESC, camEXPO=0.1, camFREQ=10):
    delay = 0.05#1./camFREQ
    
    timeSET = []
            
    camInfo = cam.getCameraInfo()
    serialNum = str(camInfo.serialNumber)
    camName = camNAME[serialNum]
    
    dataSetNum = getDataSetNum()
    dataSetStr = str(dataSetNum)
    
    now = dt.datetime.now()
    Year = str(now.year)
    Month = stringTIME(now.month)
    Day = stringTIME(now.day)
    
    input('\nPress ENTER to take {} photos...'.format(numPHOTO))
    cam.startCapture()
    for i in range(numPHOTO):
        shotNum = stringTIME(i+1, 3)
        try:
            timeBFOR = dt.datetime.now()
            image = cam.retrieveBuffer()
            timeAFTR = dt.datetime.now()
            timeSET.append(timeBFOR+0.5*(timeAFTR-timeBFOR))
            image.save(('IMAGES/year_%s/month_%s/day_%s/%s/%s_%s_%s.tiff' % (Year, Month, Day, dataSetStr, camName, dataSetStr, shotNum)).encode("utf-8"), pc2.IMAGE_FILE_FORMAT.TIFF) 
        except pc2.Fc2error as fc2Err:
            timeSET.append(False)
            print('\nError retrieving buffer : ', fc2Err) 
        sleep(delay)
    cam.stopCapture()
    
    shotFAIL = 0
    metaDATA = []
    for j in range(numPHOTO):
        if timeSET[j]:
            meta = writeMetaData(camName, dataSetNum, timeSET[j], j+1, imageDESC)
            metaDATA.append(meta)
        else:
            shotFAIL+=1
            metaDATA.append(False)
      
    for k in range(numPHOTO):
        if metaDATA[k]:
            shotNum = stringTIME(k+1, 3)
            
            dataDICT = metaDATA[k]
            dataBYTE = str(dataDICT).encode()
            dataBASE = str(base64.b64encode(dataBYTE), 'ascii')
            
            subprocess.call('tiffset -s 270 '+dataBASE+' IMAGES/year_{}/month_{}/day_{}/{}/{}_{}_{}.tiff'.format(Year, Month, Day, dataSetNum, camName, dataSetNum, shotNum), shell=True)
            
    writeMetaDataTxt(dataSetNum, imageDESC, [serialNum], [numPHOTO, shotFAIL], timeSET)
            
    advDataSetNum(dataSetNum)
            
camNAME = {'17529184':'Cam01', '17570564':'Cam02', '17571186':'Cam03', '17583372':'Cam04'}       

