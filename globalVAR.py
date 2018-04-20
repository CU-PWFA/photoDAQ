#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 14:09:21 2018

@author: cu-pwfa
"""

import datetime as dt
import base64
import subprocess

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
        
def writeMetaData(serialNum, dataSET, dateNOW, shotNUM, imageDESC):
    Dict = {}
    Dict['CamName'] = camNAME[serialNum]+': '+serialNum
    Dict['DatasetID'] = dataSET
    Dict['TimeStamp'] = writeTimeStamp(dateNOW)
    Dict['ShotNum'] = shotNUM
    Dict['Description'] = imageDESC
    
    return Dict

def saveMetaDATA(meta, fileNAME):
    fileNAME = fileNAME+'.tiff'
    metaBYTE = str(meta).encode()
    metaBASE = str(base64.b64encode(metaBYTE), 'ascii')
    subprocess.call('tiffset -s 270 '+metaBASE+' '+fileNAME, shell=True)

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
            
camNAME = {'17529184':'Cam01', '17570564':'Cam02', '17571186':'Cam03', '17583372':'Cam04'}       

