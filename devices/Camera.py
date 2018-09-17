#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 13 16:32:45 2018

@author: robert
"""

import PyCapture2 as pc2

class Camera():
    """ Class to control the FLIR cameras. """
    
    def __init__(self, serial):
        """ Create the pyCapture Camera object fo the camera. """
        self.connectCam(serial)
        self.setupCam()
    
    def connectCam(self, serial):
        """ Connect to the camera and verify the connection. 
        
        Parameters
        ----------
        serial : int
            The serial number of the camera.
        """
        self.bus = pc2.BusManager()
        numCams = self.bus.getNumOfCameras()
        
        if numCams == 0:
            print('Ethernet error: No Cameras Detected')
            self.cam = False
        else:
            self.cam = pc2.GigECamera()
            self.guid = self.bus.getCameraFromSerialNumber(serial)
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
    # TODO implement a get max height and width function
    
    # Set camera parameters
    #--------------------------------------------------------------------------   
    # TODO should print the range of possible values when someone inputs an incorrect one     
    def set_image_settings(self, width=None, height=None, pixelFormat=None):
        """ Set the image format on the camera.
        
        Parameters
        ----------
        width : int, optional
            The width of the image in pixels.
        height : int, optional
            The height of the image in pixels.
        pixelFormat : int, optional
            Pass an atrribute of pc2.PIXEL_FORMAT for a valid integer.
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
            gain.autoManualMode = auto
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
            shut.autoManualMode = auto
        if value is not None:
            if value > info.absMax or value < info.absMin:
                print('Invalid value for shutter.')
            else:
                shut.absValue = value
        self.cam.setProperty(shut)
    
    def set_frame_rate(self, frame_rate):
        """ Set the camera frame rate.
        
        Parameters
        ----------
        frame_rate : float
            The FPS for the camera to capture at.
        """
        framePROP = pc2.PROPERTY_TYPE.FRAME_RATE
        frame = self.cam.getProperty(framePROP)
        info = self.cam.getPropertyInfo(framePROP)
        if frame_rate > info.absMax or frame_rate < info.absMin:
            rang = (info.absMin, info.absMax)
            print('Invalid value for frame rate range: (%0.1f, %0.1f)'%rang)
        else:
            frame.absValue = frame_rate
        self.cam.setProperty(frame)
        
    def set_trigger_settings(self):
        """ Set the trigger mode of the camera.
        """
        # TODO implement triggering of the camera.
        pass
    
    # Control the camera
    #--------------------------------------------------------------------------
    def start_capture(self, callback=None, args=None):
        """ Tell the camera to capture images and place them in the buffer. 
        
        Capture data from the camera to image buffers. The callback is called
        when an  image is retrieved, otherwise images are retrieved manually
        with retrieve buffer (not recommended).
        
        Parameters
        ----------
        callback : func, optional
            A callback function for when an image is retrieved, must take an
            pc2 image object as the first argument. 
        *args : tuple
            Arguments to be passed to the callback.
        """
        self.cam.startCapture(callback, args)
    
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
        image = self.cam.retrieveBuffer()
        return image
        
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