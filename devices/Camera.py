#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 13 16:32:45 2018

@author: robert
"""

from devices.device import Device
import PySpin

class Camera(Device):
    """ Class to control the FLIR cameras. """
    
    def __init__(self, serial):
        """ Create the pyCapture Camera object fo the camera. 
        
        Parameters
        ----------
        serial : str
            The serial number of the camera.
        """
        self.connectCam(serial)
        self.setupCam(serial)
    
    def connectCam(self, serial):
        """ Connect to the camera and verify the connection. 
        
        Parameters
        ----------
        serial : int
            The serial number of the camera.
        """
        self.system = PySpin.System.GetInstance()
        cam_list = self.system.GetCameras()
        numCams = cam_list.GetSize()
        
        if numCams == 0:
            print('Ethernet error: No Cameras Detected')
            self.cam = False
        else:
            self.cam = cam = cam_list.GetBySerial(serial)
            self.nodemap_tl = cam.GetTLDeviceNodeMap()
            cam.Init()
            self.nodemap = cam.GetNodeMap()
            
            self.serialNum = serial
            self.model = model = cam.TLDevice.DeviceModelName.ToString()
            self.fv = fv = cam.DeviceFirmwareVersion.ToString()
            self.ID = (model + ',' + serial + ',FV:' + fv)
            print('Camera ID:', self.ID)
    
    def setupCam(self, serial):
        """ Set settings required for correct image acquisition. """
        # Set all auto controlled parameters to off
        cam = self.cam
        if cam.ExposureMode.GetAccessMode() == PySpin.RW:
            cam.ExposureMode.SetValue(PySpin.ExposureMode_Timed)
        if cam.ExposureAuto.GetAccessMode() == PySpin.RW:
            cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        if cam.GainSelector.GetAccessMode() == PySpin.RW:
            cam.GainSelector.SetValue(PySpin.GainSelector_All)
        if cam.GainAuto.GetAccessMode() == PySpin.RW:
            cam.GainAuto.SetValue(PySpin.GainAuto_Off)
        if cam.BlackLevelSelector.GetAccessMode() == PySpin.RW:
            cam.BlackLevelSelector.SetValue(PySpin.BlackLevelSelector_All)
        if cam.BlackLevelAuto.GetAccessMode() == PySpin.RW:
            cam.BlackLevelAuto.SetValue(PySpin.BlackLevelAuto_Off)
        if cam.BlackLevel.GetAccessMode() == PySpin.RW:
            value = cam.BlackLevel.GetMin()
            if value != 0.0:
                print('Warning, this camera has a nonzero black level.')
            cam.BlackLevel.SetValue(value)
        if cam.GammaEnable.GetAccessMode() == PySpin.RW:
            cam.GammaEnable.SetValue(False)
        if cam.SharpeningEnable.GetAccessMode() == PySpin.RW:
            cam.SharpeningEnable.SetValue(False)
        if cam.AdcBitDepth.GetAccessMode() == PySpin.RW:
            cam.AdcBitDepth.SetValue(PySpin.AdcBitDepth_Bit12)
        if cam.AcquisitionMode.GetAccessMode() == PySpin.RW:
            cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        if cam.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
            cam.AcquisitionFrameRateEnable.SetValue(True)
        # Disable sharpening
        if cam.SharpeningEnable.GetAccessMode() == PySpin.RW:
            cam.SharpeningEnable.SetValue(False)
        NodeSharpnessEnabled = PySpin.CBooleanPtr(self.nodemap.GetNode('SharpnessEnabled'))
        if PySpin.IsAvailable(NodeSharpnessEnabled) and PySpin.IsReadable(NodeSharpnessEnabled):
            NodeSharpnessEnabled.SetValue(False)
        # Set auto framerate to off
        NodeAutoFrameRate = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionFrameRateAuto'))
        if PySpin.IsAvailable(NodeAutoFrameRate) and PySpin.IsReadable(NodeAutoFrameRate):
            AutoFrameRate_Off = NodeAutoFrameRate.GetEntryByName('Off')
            NodeAutoFrameRate.SetIntValue(AutoFrameRate_Off.GetValue())
        # I Don't know exactly what this (it isn't in any documentation I could find)
        # so I'm turining it off, we want the raw data from the camera, no compensation
        NodeCompensation = PySpin.CEnumerationPtr(self.nodemap.GetNode('pgrExposureCompensationAuto'))
        if PySpin.IsAvailable(NodeCompensation) and PySpin.IsReadable(NodeCompensation):
            Compensation_Off = NodeCompensation.GetEntryByName('Off')
            NodeCompensation.SetIntValue(Compensation_Off.GetValue())
        
        # Chack the packet size is as large as possible
        max_packet = cam.DiscoverMaxPacketSize()
        if cam.GevSCPSPacketSize.GetAccessMode() == PySpin.RW:
            cam.GevSCPSPacketSize.SetValue(max_packet)
        current_packet = int(cam.GevSCPSPacketSize.ToString())
        if current_packet != max_packet:
            cam.GevSCPSPacketSize.SetValue(max_packet)
            current_packet = int(cam.GevSCPSPacketSize.ToString())
        if current_packet != max_packet:
            print('Camera is using a packet size of %i not the max of %i.' % (current_packet, max_packet))
        if max_packet != 9000:
            print('Max packet size is only %i, increase to 9000 for best performance.' % max_packet)
            
        # Set the packet delay, will limit bandwidth. Size=9000 and delay=5900 is 25MB/s
        if cam.GevSCPD.GetAccessMode() == PySpin.RW:
            cam.GevSCPD.SetValue(5900)
        
        self.set_pixel_format('Mono12Packed')
        self.set_trigger_settings(False)
        
    # Request camera parameters
    #--------------------------------------------------------------------------
    def get_sensor_height(self):
        """ Return the height of the sensor in pixels. """
        return self.cam.SensorHeight.GetValue()
    
    def get_sensor_width(self):
        """ Return the width of the sensor in pixels. """
        return self.cam.SensorWidth.GetValue()
    
    def get_max_height(self):
        """ Get the maximum height based on the current offset. """
        return self.cam.Height.GetMax()
    
    def get_max_width(self):
        """ Get the maximum width based on the current offset. """
        return self.cam.Width.GetMax()
    
    def get_max_offsetX(self):
        """ Get the maximum X offset based on the current width. """
        return self.cam.OffsetX.GetMax()
    
    def get_max_offsetY(self):
        """ Get the maximum X offset based on the current width. """
        return self.cam.OffsetY.GetMax()
    
    def get_min_gain(self):
        """ Get the minimum gain setting. """
        return self.cam.Gain.GetMin()
    
    def get_max_gain(self):
        """ Get the maximum gain setting. """
        return self.cam.Gain.GetMax()
    
    def get_min_shutter(self):
        """ Get the minimum shutter setting. """
        return self.cam.ExposureTime.GetMin()
    
    def get_max_shutter(self):
        """ Get the maximum shutter setting. """
        return self.cam.ExposureTime.GetMax()
    
    def get_min_framerate(self):
        """ Get the minimum framerate setting. """
        return self.cam.AcquisitionFrameRate.GetMin()
    
    def get_max_framerate(self):
        """ Get the maximum framerate setting. """
        return self.cam.AcquisitionFrameRate.GetMax()
    
    def get_height(self):
        """ Get the height of the image. """
        return self.cam.Height.GetValue()
        
    def get_width(self):
        """ Get the width of the image. """
        return self.cam.Width.GetValue()
    
    def get_offsetX(self):
        """ Get the ROI offset in X. """
        return self.cam.OffsetX.GetValue()
        
    def get_offsetY(self):
        """ Get the ROI offset in Y. """
        return self.cam.OffsetY.GetValue()
    
    def get_shutter(self):
        """ Get the current shutter setting in ms. """
        return self.cam.ExposureTime.GetValue()*1e-3
    
    def get_gain(self):
        """ Get the current gain settings. """
        return self.cam.Gain.GetValue()
    
    def get_framerate(self):
        """ Get the current framerate setting. """
        return self.cam.AcquisitionFrameRate.GetValue()
    
    # Set camera parameters
    #--------------------------------------------------------------------------   
    def set_pixel_format(self, pixelFormat):
        """ Set the pixel format of the camera. 
        
        Parameters
        ----------
        pixelFormat : string
            Pixel format as a string.
        """
        if pixelFormat == 'Mono8':
            self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
        elif pixelFormat == 'Mono12Packed':
            self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono12Packed)
        elif pixelFormat == 'Mono16':
            self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono16)
        else:
            print('%s is not a valid pixel format.' % pixelFormat)
        
    def set_gain(self, gain):
        """ Set the gain of the camera. 
        
        Parameters
        ----------
        gain : float
            The gain of the camera's ADC in dB.
        """
        gain_min = self.get_min_gain()
        gain_max = self.get_max_gain()
        if gain > gain_max:
            print('Gain outside of range, setting to maximum value of %0.2f' % gain_max)
            gain = gain_max
        if gain < gain_min:
            print('Gain outside of range, setting to minimum value of %0.2f' % gain_min)
            gain = gain_min
        self.cam.Gain.SetValue(gain)
    
    def set_shutter(self, shutter):
        """  Set the shutter time of the camera
        
        Parameters
        ----------
        shutter : float
            The shutter time in ms.
        """
        shutter *= 1e3
        exposure_min = self.get_min_shutter()
        exposure_max = self.get_max_shutter()
        if shutter > exposure_max:
            print('Shutter outside of range, setting to maximum value of %0.2f' % (exposure_max*1e-3))
            shutter = exposure_max
        if shutter < exposure_min:
            print('Shutter outside of range, setting to minimum value of %0.2f' % (exposure_min*1e-3))
            shutter = exposure_min
        self.cam.ExposureTime.SetValue(shutter)
        
    def set_frame_rate(self, frame_rate):
        """ Set the frame rate to operate at without a trigger.
        
        Parameters
        ----------
        frame_rate : float
            The frame rate in Hz.
        """
        framerate_min = self.get_min_framerate()
        framerate_max = self.get_max_framerate()
        if frame_rate > framerate_max:
            print('Frame rate outside of range, setting to maximum value of %0.2f' % framerate_max)
            frame_rate = framerate_max
        if frame_rate < framerate_min:
            print('Frame rate outside of range, setting to minimum value of %0.2f' % framerate_min)
            frame_rate = framerate_min
        if self.cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
                self.cam.AcquisitionFrameRate.SetValue(frame_rate)
        else:
            # TODO add the reason why it isn't writable or fix the setting
            # AcquisitionFrameRateEnable needs to be set to True - I already do this at the start
            print('Frame rate is not currently writable.')
        
    def set_test_pattern(self, pattern):
        """ Set the camera to output a test pattern.
        
        Parameters
        ----------
        pattern : string
            'Off' turns the test pattenr off.
            'Increment' increments each pixel value by 1 for testing bit depth.
            'Sensor' uses a test pattern generated by the image sensor.
        """
        if pattern == 'Off':
            self.cam.TestPattern.SetValue(PySpin.TestPattern_Off)
        elif pattern == 'Increment':
            self.cam.TestPattern.SetValue(PySpin.TestPattern_Increment)
        elif pattern == 'Sensor':
            self.cam.TestPattern.SetValue(PySpin.TestPattern_SensorTestPattern)
        else:
            print("\s is not a valid test pattern." % pattern)
    
    def set_trigger_settings(self, enable):
        """ Set the trigger mode of the camera.
        
        Parameters
        ----------
        enable : bool
            Enable or disable the trigger.
        """
        cam = self.cam
        if enable == True:
            cam.TriggerSource.SetValue(PySpin.TriggerSource_Line0)
            cam.TriggerActivation.SetValue(PySpin.TriggerActivation_RisingEdge)
            cam.TriggerDelay.SetValue(0)
            cam.TriggerSelector.SetValue(PySpin.TriggerSelector_FrameStart)
            if cam.TriggerOverlap.GetAccessMode() == PySpin.RW:
                cam.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
            
            cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
        if enable == False:
            cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
            
    def set_offsetX(self, offsetX):
        """ Set the X offset for the ROI.
        
        Parameters
        ----------
        offsetX : int
            The horizontal offset in pixels of the ROI.
        """
        offset_max = self.get_max_offsetX()
        if offsetX > offset_max:
            print('Offset outside of range, setting to maximum value of %i' % offset_max)
            offsetX = offset_max
        if offsetX < 0:
            print('Negative framerates are not allowed, setting to 0.')
            offsetX = 0
        self.cam.OffsetX.SetValue(offsetX)
        
    def set_offsetY(self, offsetY):
        """ Set the Y offset for the ROI.
        
        Parameters
        ----------
        offsetY : int
            The vertical offset in pixels of the ROI.
        """
        offset_max = self.get_max_offsetY()
        if offsetY > offset_max:
            print('Offset outside of range, setting to maximum value of %i' % offset_max)
            offsetY = offset_max
        if offsetY < 0:
            print('Negative offsets are not allowed, setting to 0.')
            offsetY = 0
        self.cam.OffsetY.SetValue(offsetY)
        
    def set_height(self, height):
        """ Set the height of the ROI.
        
        Parameters
        ----------
        height : int
            The height of the ROI in pixels.
        """
        height_max = self.get_max_height()
        if height > height_max:
            print('Height outside of range, setting to maximum value of %i' % height_max)
            height = height_max
        if height < 1:
            print('Negative and zero heights are not allowed, setting to 1.')
            height = 1
        if self.cam.Height.GetAccessMode() == PySpin.RW:
            self.cam.Height.SetValue(height)
        else:
            print('Height is not currently writable.')
        
    def set_width(self, width):
        """ Set the width of the ROI.
        
        Parameters
        ----------
        width : int
            The width of the ROI in pixels.
        """
        width_max = self.get_max_width()
        if width > width_max:
            print('Width outside of range, setting to maximum value of %i' % width_max)
            width = width_max
        if width < 1:
            print('Negative and zero widths are not allowed, setting to 1.')
            width = 1
        if self.cam.Width.GetAccessMode() == PySpin.RW:
            self.cam.Width.SetValue(width)
        else:
            print('Width is not currently writable.')
    
    # Control the camera
    #--------------------------------------------------------------------------
    def start_capture(self):
        """ Tell the camera to capture images and place them in the buffer. """
        self.cam.BeginAcquisition()
    
    def stop_capture(self):
        """ Tell the camera to stop capturing images. """
        self.cam.EndAcquisition()
        
    def retrieve_buffer(self):
        """ Attempt to retrieve an image from the buffer. 
        
        Returns
        -------
        image : obj
            A PySpin.Image object which includes the image data.
        """
        try:
            image = self.cam.GetNextImage()
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            image = None
        return image
        
    def close(self):
        """ Disconnect the camera. """
        self.cam.DeInit()
        del self.cam
        self.system.ReleaseInstance()
    
    # Camera data managment
    #--------------------------------------------------------------------------
    def take_photo(self):
        """ Start capturing and retrieve an image from the buffer.
        
        Returns
        -------
        image : obj
            A PyCapture2.Image object which includes the image data.
        """
        cam = self.cam
        if cam.AcquisitionMode.GetAccessMode() == PySpin.RW:
            cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)
        cam.BeginAcquisition()
        try:
            image = cam.GetNextImage()
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            image = None
        if image.IsIncomplete():
            print('Image incomplete with image status %d ...' % image.GetImageStatus())
        cam.EndAcquisition()
        if cam.AcquisitionMode.GetAccessMode() == PySpin.RW:
            cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        return image
        