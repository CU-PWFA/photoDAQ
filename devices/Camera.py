#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 13 16:32:45 2018

@author: robert
"""

import PyCapture2 as pc2

class Camera():
    """ Class to control the FLIR cameras. """
    
    def __init__(self, ind=0):
        """ Create the pyCapture Camera object fo the camera. """
        self.connectCam(ind)
        self.setupCam()
    
    def connectCam(self, ind):
        """ Connect to the camera and verify the connection. 
        
        Parameters
        ----------
        ind : int
            The index of the camera in the bus manager.
        """
        self.bus = pc2.BusManager()
        numCams = self.bus.getNumOfCameras()
        
        if numCams == 0:
            print('Ethernet error: No Cameras Detected')
            self.cam = False
        else:
            self.cam = pc2.GigECamera()
            self.guid = self.bus.getCameraFromIndex(ind)
            try:
                self.cam.connect(self.guid)
            except:
                print('Ethernet error: Could not connect to camera.')
            self.camINFO = info = self.cam.getCameraInfo()
            self.imageINFO = self.cam.getGigEImageSettingsInfo()
            self.serialNum = info.serialNumber
            model = info.modelName.decode("utf-8")
            fv = info.firmwareVersion.decode("utf-8")
            self.ID = (model + ',' + str(self.serialNum) + ',FV:' + fv)
            print('Camera ID:', self.ID)
    
    def setupCam(self):
        """ Set settings required for correct image acquisition. """
        width = self.imageINFO.maxWidth
        height = self.imageINFO.maxHeight
        pixelFormat = pc2.PIXEL_FORMAT.RAW16
        self.set_image_settings(width, height, pixelFormat)
        self.set_gain_settings(False, 0)
        self.set_shutter_settings(False, 10)
        
    # Request camera parameters
    #--------------------------------------------------------------------------
    
    
    # Set camera parameters
    #--------------------------------------------------------------------------        
    def set_image_settings(self, width=None, height=None, pixelFormat=None):
        """ Set the image format on the camera.
        
        Parameters
        ----------
        width : int, optional
            The width of the image in pixels.
        height : int, optional
            The height of the image in pixels.
        pixelFormat : int, optional
            Pass a atrribute of pc2.PIXEL_FORMAT for a valid integer.
        """
        settings = self.cam.getGigEImageSettings()
        if pixelFormat is not None:
            if pixelFormat & self.imageINFO.pixelFormatBitField == 0:
                print('This pixel format is not supported by this camera.')
            else:
                settings.pixelFormat = pixelFormat
        elif width is not None:
            if width > self.imageINFO.maxWidth:
                print('Image width is greater than max width.')
            else:
                settings.width = width
        elif height is not None:
            if height > self.imageINFO.maxHeight:
                print('Image height is greater than max height.')
            else:
                settings.height = height
        #If none of the conditions are triggered this doesn't change the values
        self.cam.setGigEImageSettings(settings)
    
    def set_gain_settings(self, auto=None, value=None):
        """ Set the camera shutter settings. 
        
        Parameters
        ----------
        auto : bool, optional
            Whether auto gain is enabled or not.
        value : float, optional
            The value to set the gain to.
        """
        gainPROP = pc2.PROPERTY_TYPE.GAIN
        gain = self.cam.getProperty(gainPROP)
        info = self.cam.getPropertyInfo(gainPROP)
        if auto is not None:
            gain.autoManualMode = False
        if value is not None:
            if value > info.absMax or value < info.absMin:
                print('Invalid value for shutter.')
            else:
                gain.absValue = value
        self.cam.setProperty(gain)
    
    def set_shutter_settings(self, auto=None, value=None):
        """ Set the camera shutter settings. 
        
        Parameters
        ----------
        auto : bool, optional
            Whether auto shutter is enabled or not.
        value : float, optional
            The value to set the shutter to.
        """
        shutPROP = pc2.PROPERTY_TYPE.SHUTTER
        shut = self.cam.getProperty(shutPROP)
        info = self.cam.getPropertyInfo(shutPROP)
        if auto is not None:
            shut.autoManualMode = False
        if value is not None:
            if value > info.absMax or value < info.absMin:
                print('Invalid value for shutter.')
            else:
                shut.absValue = value
        self.cam.setProperty(shut)
    
    # Control the camera
    #--------------------------------------------------------------------------
    def start_capture(self):
        """ Tell the camera to capture images and place them in the buffer. """
        self.cam.startCapture()
    
    def stop_capture(self):
        """ Tell the camera to stop capturing images. """
        self.cam.stopCapture()
        
    def retrieve_buffer(self):
        """ Attempt to retrieve an image from the buffer. 
        
        Returns
        -------
        image : obj
            A PyCapture2.Image object which includes the image data.
        """
        try:
            image = self.cam.retrieveBuffer()
            return image
        except pc2.Fc2error as fc2Err:
            print('Error retrieving buffer: ', fc2Err)
            return False
        
    def close(self):
        """ Disconnect the camera. """
        self.cam.disconnect()
    
    # Camera data managment
    #--------------------------------------------------------------------------
    def take_photo(self):
        """ Start capturing and retrieve an image from the buffer.
        
        Returns
        -------
        image : obj
            A PyCapture2.Image object which includes the image data.
        """
        self.cam.startCapture()
        image = self.retrieve_buffer()
        self.cam.stopCapture()
        return image