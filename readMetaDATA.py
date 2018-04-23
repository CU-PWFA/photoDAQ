#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 29 21:50:46 2018

@author: cu-pwfa
"""

#########################################################################
#                                                                       #
#   This code prints the metadata stored in a single .tiff image.       #
#   To find the image, the user must know the date the file was         #
#   taken, the last four digist of the data set number, the camera      #
#   name and the shot number of the image.  The metadata is coded       #
#   in base64.                                                          #
#                                                                       #
#########################################################################

from PIL import Image
import ast
import base64
import globalVAR as Gvar
import os

while True:
    while True:
        date = input('\nDate of File (yyyy/mm/dd): ')
        year = date[0:4]
        month = date[5:7]
        day = date[8:10]
        try:
            yearINT=int(year)
            int(month)
            int(day)
            break
        except:
            print('\nInvalide Response')
            
    while True:
        SetNum = input('\nData Set Number (0000): ')
        Yr = str(yearINT-2000)
        dataSetNum = Yr+month+day+SetNum
        try:
            int(dataSetNum)
            break
        except:
            print('\nInvalide Response')
            
    cam = input('\nCamera Name: ')
    
    while True:
        try:
            shotNUM = int(input('\nShot Number: '))
            shotNUM = Gvar.stringTIME(shotNUM, 3)
            break
        except:
            print('\nInvalid Response')

    fileNAME = 'IMAGES/year_'+year+'/month_'+month+'/day_'+day+'/'+dataSetNum+'/'+cam+'_'+dataSetNum+'_'+shotNUM+'.tiff'
    if os.path.exists(fileNAME):
        break
    else:
        print('\nFile Not Found')

im = Image.open(fileNAME)
metaDATA = im.tag[270][0]

### Parse TIFF tag into working dictionary ###
metaDATA = base64.b64decode(metaDATA) 
metaDATA = ast.literal_eval(str(metaDATA, 'ascii'))

print()
print(metaDATA)
print()
