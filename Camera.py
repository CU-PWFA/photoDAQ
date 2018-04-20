# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import PyCapture2 as pc2
import numpy as np
import libtiff
import datetime as dt
import globalVAR as Gvar

class Camera():
    def __init__(self, camIND, camPIXEL=16, camGAIN=0):
        self.connectCam(camIND)
        if self.cam:
            self.prepareSettings(camPIXEL, camGAIN)
    
    def connectCam(self, camIND):
        self.bus = pc2.BusManager()
        numCams = self.bus.getNumOfCameras()
        
        if numCams == 0:
            print('\nNo Cameras Detected')
            self.cam = False
        elif camIND >= numCams:
            print('\nOnly {} Camera(s) Detected.'.format(numCams))
            self.cam = False
        else:
            self.cam = pc2.Camera()
            self.guid = self.bus.getCameraFromIndex(camIND)
            self.cam.connect(self.guid)
            self.camINFO = self.cam.getCameraInfo()
            self.serialNUM = str(self.camINFO.serialNumber)
            self.camNAME = Gvar.camNAME[str(self.serialNUM)]
            
    def prepareSettings(self, camPIXEL, camGAIN):
        if camPIXEL == 8:
            self.dtype = np.uint8
            pixelFormat = pc2.PIXEL_FORMAT.RAW8
        elif camPIXEL == 16:
            self.dtype = np.uint16
            pixelFormat = pc2.PIXEL_FORMAT.RAW16
        else:
            pixelFormat = False
            print('\nError: Unsupported Pixel Format')
        
        fmt7info = self.cam.getFormat7Info(0)[0]
        self.pixROW = fmt7info.maxHeight
        self.pixCOL = fmt7info.maxWidth
        fmt7imgSet = pc2.Format7ImageSettings(0, 0, 0, self.pixCOL, self.pixROW,
                                              pixelFormat)
        fmt7pktInf, isValid = self.cam.validateFormat7Settings(fmt7imgSet)
        if pixelFormat and isValid:
            self.cam.setFormat7ConfigurationPacket(fmt7pktInf.recommendedBytesPerPacket, fmt7imgSet)
        else:
            print('\nError: Format7 settings are not valid.')
        
        gainPROP = pc2.PROPERTY_TYPE.GAIN
        gain = self.cam.getProperty(gainPROP)
        gain.autoManualMode = False
        gain.absValue = camGAIN
        self.cam.setProperty(gain)
        
    def startCapture(self):
        self.cam.startCapture()
        
    def stopCapture(self):
        self.cam.stopCapture()
        
    def savePhotoTIFF(self, image, fileNAME):
        fileName = fileNAME+'.tiff'
        tiff = libtiff.TIFF.open(fileName, mode='w')
        tiff.write_image(image)
        tiff.close()
        
    def disconnect(self):
        self.cam.disconnect()
        
    def takePhoto(self):
        setDesc = input('\nData Set Description: ')
        
        dataSetNum = Gvar.getDataSetNum()
        dataSetStr = str(dataSetNum)
        
        now = dt.datetime.now()
        Year = str(now.year)
        Month = Gvar.stringTIME(now.month)
        Day = Gvar.stringTIME(now.day)
        fileNameBase = 'IMAGES/year_'+Year+'/month_'+Month+'/day_'+Day+'/'+dataSetStr+'/'+self.camNAME+'_'+dataSetStr
        
        shotCount = 0
        shotFail = 0
        
        timeSET = []
        SET = True
        self.startCapture()
        while SET:
            shotCount+=1
            shotNum = Gvar.stringTIME(shotCount, 3)
            fileName = fileNameBase+'_'+shotNum
            input('\nPress ENTER to take photo...')
            try:
                timeBFOR = dt.datetime.now()
                image = self.cam.retrieveBuffer()
                timeAFTR = dt.datetime.now()
                timeSET.append(timeBFOR+0.5*(timeAFTR-timeBFOR))
                
                imageArray = np.frombuffer(bytes(image.getData()), dtype=self.dtype).reshape( (self.pixROW, self.pixCOL) )
                self.savePhotoTIFF(imageArray, fileName)
            except pc2.Fc2error as fc2Err:
                shotFail+=1
                timeSET.append(False)
                print('\nError retrieving buffer : ', fc2Err) 
            SET = Gvar.promptREPEAT()
        self.stopCapture()
            
        for i in range(shotCount):
            if timeSET[i]:
                shotNum = Gvar.stringTIME(i+1, 3)
                fileName = fileNameBase+'_'+shotNum
                meta = Gvar.writeMetaData(self.serialNUM, dataSetNum, timeSET[i], i+1, setDesc)
                Gvar.saveMetaDATA(meta, fileName)
        
        Gvar.writeMetaDataTxt(dataSetNum, setDesc, [self.serialNUM], [shotCount, shotFail], timeSET)
        Gvar.advDataSetNum(dataSetNum)
            
    def takePhotoSet(self):
        while True:
            try:
                numOfPhotos = int(input('\nNumber of Photos: '))
                break
            except:
                print('\nInvalid Answer')
            
        setDesc = input('\nData Set Description: ')
        
        dataSetNum = Gvar.getDataSetNum()
        dataSetStr = str(dataSetNum)
        
        now = dt.datetime.now()
        Year = str(now.year)
        Month = Gvar.stringTIME(now.month)
        Day = Gvar.stringTIME(now.day)
        fileNameBase = 'IMAGES/year_'+Year+'/month_'+Month+'/day_'+Day+'/'+dataSetStr+'/'+self.camNAME+'_'+dataSetStr
        
        shotFAIL = 0
        timeSET = []
        
        input('\nPress ENTER to take {} photos...'.format(numOfPhotos))
        self.startCapture()
        for i in range(numOfPhotos):
            shotNum = Gvar.stringTIME(i+1, 3)
            fileNAME = fileNameBase+'_'+shotNum
            try:
                timeBFOR = dt.datetime.now()
                image = self.cam.retrieveBuffer()
                timeAFTR = dt.datetime.now()
                timeSET.append(timeBFOR+0.5*(timeAFTR-timeBFOR))
                
                imageArray = np.frombuffer(bytes(image.getData()), dtype=self.dtype).reshape( (self.pixROW, self.pixCOL) )
                self.savePhotoTIFF(imageArray, fileNAME)
            except pc2.Fc2error as fc2Err:
                shotFAIL+=1
                timeSET.append(False)
                print('\nError retrieving buffer : ', fc2Err) 
        self.stopCapture()
        
        for j in range(numOfPhotos):
            if timeSET[j]:
                shotNum = Gvar.stringTIME(j+1, 3)
                fileNAME = fileNameBase+'_'+shotNum
                meta = Gvar.writeMetaData(self.serialNUM, dataSetNum, timeSET[j], j+1, setDesc)            
                Gvar.saveMetaDATA(meta, fileNAME)
        
        Gvar.writeMetaDataTxt(dataSetNum, setDesc, [self.serialNUM], [numOfPhotos, shotFAIL], timeSET)
        Gvar.advDataSetNum(dataSetNum)

