#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 13:19:40 2018

@author: cu-pwfa
"""

import libtiff 

fileName = 'IMAGES/year_2018/month_04/day_20/1804200001/Cam04_1804200001_0001'

imgData = libtiff.TIFF.open(fileName+'.tiff', mode='r')
img = imgData.read_image()
imgData.close()

print(img.dtype)