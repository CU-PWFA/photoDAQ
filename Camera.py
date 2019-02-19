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

from PIL import Image
import io
import pathlib
import math
import scipy

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from scipy.optimize import leastsq

class Camera():
    def __init__(self, camIND, camPIXEL=16, camPixMONO=True, camGAIN=0, camSHUTTER=50):
        self.connectCam(camIND)
        if self.cam:
            self.prepareSettings(camPIXEL, camPixMONO, camGAIN, camSHUTTER)
    
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
            
    def prepareSettings(self, camPIXEL, camPixMONO, camGAIN, camSHUTTER):
        if not camPixMONO:
            if camPIXEL == 8:
                self.dtype = np.uint8
                pixelFormat = pc2.PIXEL_FORMAT.RAW8
            elif camPIXEL == 16:
                self.dtype = np.uint16
                pixelFormat = pc2.PIXEL_FORMAT.RAW16
            else:
                pixelFormat = False
                print('\nError: Unsupported Pixel Format')
        elif camPixMONO:
            if camPIXEL == 8:
                self.dtype = np.uint8
                pixelFormat = pc2.PIXEL_FORMAT.MONO8
            elif camPIXEL == 16:
                self.dtype = np.uint16
                pixelFormat = pc2.PIXEL_FORMAT.MONO16
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
        
        shutPROP = pc2.PROPERTY_TYPE.SHUTTER
        shut = self.cam.getProperty(shutPROP)
        shut.autoManualMode = False
        shut.absValue = camSHUTTER
        self.cam.setProperty(shut)
        
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
    
    def retrieveBuffer(self, verbose=True):
        try:
            image = self.cam.retrieveBuffer()
            return image
        except pc2.Fc2error as fc2Err:
            if verbose:
                print('\nError retrieving buffer : ', fc2Err)
            return False
        
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
                
                ### Post Analysis (begin) ###
                check = input('\nRun post analysis? (y/n)')
                if (check=='y') or (check=='Y') or (check=='yes') or (check=='Yes') or (check=='YES'):
                    Check = True
                elif (check=='n') or (check=='N') or (check=='no') or (check=='No') or (check=='NO'):
                    Check = False
                
                if Check:
                    #Load image, change mode
                    #
                    path_image = fileName+'.tiff'
                    #"/Users/Shayla/Documents/Python_Imaging/image4_2_27_18.tiff"
                    #"/Users/Shayla/Desktop/2018-04-12_Test_Data/1804120001/Cam01_1804120001_0001.tiff"
                    # 4_5_18_thinfilament1_withfiltercopy.tiff"
                    
                    
                    im = Image.open(path_image)
                    print("Opened", im.filename)
                    print(" ")
                    
                    size = im.size
                    print("Image size: (width,hight)", size)
                    print("Image format: ", im.format)
                    
                    mode = im.mode
                    if mode == "I":
                    	print("Mode already I")
                    else: 
                    	imBW = im.convert('I')
                    	print("Mode changed to", imBW.mode)	
                    print(" ")	
                    
                    imBWnumpy = np.array(imBW)
                    px = imBW.load()
                    
                    
                    # Colormap
                    #
                    cdict2 = {'red':   ((0.0, 0.0, 0.0),
                    				   (0.4, 0.0, 0.0),
                                       (0.48, 1.0, 1.0),
                                       (0.52, 1.0, 1.0),
                                       (1.0, 0.0, 0.0)),
                    
                             'green': ((0.0, 0.0, 0.0),
                                       (0.24, 0.0, 0.0),
                             		   (0.48, 1.0, 1.0),
                                       (0.52, 1.0, 0.0),
                                       (1.0, 0.0, 0.0)),
                    
                             'blue':  ((0.0, 0.0, 0.0),
                                       (0.48, 1.0, 1.0),
                                       (0.52, 1.0, 0.0),
                                       (1.0, 0.0, 0.0))
                            }
                    #Register colormap
                    blue_red2 = LinearSegmentedColormap('BlueRed2', cdict2)
                    plt.register_cmap(cmap=blue_red2)
                    cmap = plt.get_cmap('BlueRed2')
                    
                    
                    
                    # Function for Cropping Images
                    # box = (left - xmin, upper - ymax, right - xmax, lower - ymin)	
                    def createImage( image, box, colormap, boxStrip, draw):
                    	"Crops and creates image for a specific box size"
                    	Crop = image.crop(box) #this is the data of the now cropped data
                    
                    	fig, axs = plt.subplots(figsize=(7, 7))
                    	extent = (box[0],box[2],box[3],box[1])
                    	imCrop = plt.imshow(np.array(Crop), cmap=colormap, extent = extent)
                    	
                    	fig.colorbar(imCrop)
                    	fig.suptitle('Cropped to ' + str(box), fontsize=16)
                    	#ax = fig.add_subplot(1, 1, 1)
                    	if draw == True:
                    		rect = plt.Rectangle(
                    		(boxStrip[0], boxStrip[3]), 
                    		(boxStrip[2]-boxStrip[0]) , (boxStrip[1]-boxStrip[3]), 
                    		fill=False, edgecolor = "white")
                    		plt.gca().add_patch(rect)	
                    	plt.show()	
                    	return
                    
                    
                    
                    #Printing Images for Various crop sizes
                    #	box = 			(left, upper, right, lower)	
                    boxFull =			(0, 0, size[0], size[1])	
                    box2 = 				(1150,900,1350,1100)	#23 Group View
                    box1 = 				(800, 600,1550,1300)	#10 Group View
                    box3 = 				(1200,990,1380,1180)	#45 Group View
                    boxColorBlack = 	(1200,380, 1300, 450)	#Black area to average
                    boxColorWhite = 	(1200,700, 1300, 800) 	#White area to average
                    
                    
                    boxStripView = box3
                    
                    createImage(imBW, boxFull, 'jet', boxColorWhite, True)
                    createImage(imBW, boxFull, 'jet', boxColorBlack, True)
                    
                    
                    #Creating Strip
                    #Includes adjusting pixels to highest contrast pxNew =(px-blackavg)*ratio of needed to current ranges
                    def stripValues(boxStrip, addedWidth, px, contrastRatio, lowestValue):
                    	"gets pixel values along given strip"
                    
                    	addedWidth = addedWidth
                    	stripX = boxStrip[0]+.5 - (addedWidth/2) 	#initial X starting 3 pixels from edge given in strip
                    	stripY = boxStrip[1]+.5						#initial Y
                    	stripWidth = boxStrip[2] - boxStrip[0] + addedWidth
                    	stripHeight = boxStrip[3] - boxStrip[1]
                    	print('Width:  ' + str(stripWidth - addedWidth))
                    	print('Height: ' + str(stripHeight))
                    	print('Initial X: ' + str(stripX -.5 +(addedWidth/2)))
                    	print('Initial Y: ' + str(stripY))
                    	print("")
                    
                    	pxValuesStrip = []  #pixel values across strip selected by boxTight
                    	#[None]*stripHeight
                    	pxValuesStripj = []
                    
                    	i=1
                    	while i <= stripHeight:
                    		stripX = boxStrip[0]+.5 - (addedWidth/2) 	#initial X starting 3 pixels from edge given in strip
                    		j=1
                    		pxValuesStripj = []
                    		while j <= stripWidth:
                    			pxValue = contrastRatio*(px[stripX,stripY]-lowestValue)
                    			pxValuesStripj.append(pxValue)
                    			stripX += 1
                    			j += 1
                    		pxValuesStrip.append(pxValuesStripj)
                    		stripY+=1
                    		i+=1	
                    	
                    	pxValuesStrip = np.mean(pxValuesStrip, axis=0)
                    	pxX = np.linspace(stripX,(stripX+stripWidth), (stripWidth))
                    	pxY = np.array(pxValuesStrip)
                    	return (pxValuesStrip, pxX, pxY, stripX, stripWidth)
                    	
                    
                    #Getting averaged white and black
                    #
                    #print('White Area:' +str(boxColorWhite))
                    pxValuesWhite, pxXWhite, pxYWhite, stripXWhite, stripWidthWhite = stripValues(boxColorWhite, 0, px, 1, 0)
                    whiteAvg = np.mean(pxValuesWhite)
                    print('Average White Pixel Value: '+str(whiteAvg))
                    print('')
                    #print('Black Area:' +str(boxColorBlack))
                    pxValuesBlack, pxXBlack, pxYBlack, stripXBlack, stripWidthBlack = stripValues(boxColorBlack, 0, px, 1, 0)
                    blackAvg = np.mean(pxValuesBlack)
                    print('Average Black Pixel Value: '+str(blackAvg))
                    
                    colordepthRealImage = whiteAvg - blackAvg
                    colordepthMode = pow(2,8)
                    colorRatio = (colordepthMode/colordepthRealImage)
                    print('')
                    print('Real color depth: ' + str(colordepthRealImage))
                    print('Mode color depth: ' + str(colordepthMode))
                    print('Color ratio: ' + str(colorRatio))
                    print('')
                    print('')
                    
                    
                    
                    #Getting Strip
                    #
                    #createImage(imBW, boxStripView, cmap, boxStrip, False)
                    
                    def createBox():
                    	box = []
                    	left = input("Left: ")
                    	box.append(int(left))
                    	upper = input("Upper: ")
                    	box.append(int(upper))	
                    	right = input("Right: ")
                    	box.append(int(right))
                    	lower = input("Lower: ")
                    	box.append(int(lower))
                    	return (box)
                    def getBox():
                    	boxStrip = createBox()
                    	createImage(imBW, boxStripView, cmap, boxStrip, True)
                    	
                    	good = input("If the box is good, enter Yes ")
                    	while good != "Yes":
                    		boxStripNew = createBox() 
                    		boxStrip = boxStripNew
                    		createImage(imBW, boxStripView, 'jet', boxStripNew, True)
                    		good = input("If the box is good, enter Yes: ")
                    	
                    	print("Box used: " +str(boxStrip))	
                    	return (boxStrip)
                    
                    #createImage(imBW, boxStripView, cmap, boxStripView, False)
                    boxStrip = getBox()
                    boxStripView = box3  #can change to get larger or smaller zoomed area
                    
                    
                    ratio = 1
                    ratioValues = []
                    bestRatio = "nope"
                    while bestRatio != "Yes":
                    	pxValues, pxX, pxY, stripX, stripWidth = stripValues(boxStrip, 0, px, colorRatio, blackAvg)
                    	minimum = min(pxValues)
                    	maximum = max(pxValues)
                    	ratio = minimum/maximum
                    	ratioValues.append(ratio)
                    	print("Ratio of min to max:", str(ratio))
                    	print("Ratio Values of groups entered:", str(ratioValues))
                    	
                    	bestRatio = input("If this is the best ratio, enter Yes: ")
                    	if bestRatio == "Yes":
                    		break
                    	print("Select new group and element")
                    	createImage(imBW, boxStripView, 'jet', boxStrip, True)
                    	boxStrip = getBox()
                    	
                    print("")
                    print("Box Used:", str(boxStrip))	
                    print("Final Ratio:", str(ratio))
                    
                    width = int(input("Input width of best ratio group and element: "))
                    pointSpreadFunction = width/1.96
                    
                    print("Point Spread Function:", str(pointSpreadFunction))	
                    	
                    	
                    	
                    	
                    
                    	
                    	
                    	
                    """
                    # Plotting Pixel Values
                    #
                    fig, axs = plt.subplots(figsize=(7, 7))
                    plt.plot(pxX, pxY, 'bo', label='Pixel Values')
                    
                    
                    #Fit
                    #
                    N = 500
                    pxValuesFit = np.polyfit(pxX, pxY, 5)
                    p = np.poly1d(pxValuesFit)
                    pxXNew = np.linspace(pxX[0],pxX[-1], N)
                    pxYNew = p(pxXNew)
                    
                    plt.plot(pxXNew, pxYNew, 'r.:', label='Fit')
                    
                    plt.axis([stripX, stripWidth+stripX, minimum-5, maximum+5])
                    fig.suptitle('Pixel Values', fontsize=16)
                    plt.legend()
                    
                    plt.show()
                    """
                    
                    #Effective Pixel
                    #
                    """
                    insert px location of two highest and width of Read
                    widthImage = locationA - locationB
                    pEffective = widthReal/widthImage
                    """
                    
                    #Point Spread Function
                    #
                    """
                    take best ratio
                    get width of line
                    pointSpread = W/1.96
                    """
                    
                    
                    #Resolution
                    #
                    """
                    resolution = (pEffective^2 + pointSpread^2)^(1/2)
                    """
                    
                    
                    #To Do:
                    #get bit depth corrected
                    #px resolution - use fit
                    #Averaging multiple photos
                ### Post Analysis (end) ###
                
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

