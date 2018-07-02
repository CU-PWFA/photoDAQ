#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 28 13:34:57 2018

@author: cu-pwfa
"""

class HR4000():
    
    def __init__(self, port=0):
        self.connectSP(port)
        
    def connectSP(self, port):
        """ Connect to the oscilloscope and verify the connection. 
        
        Parameters
        ----------
        port : int
            The port the device is connected to.
        """
        # TODO figure out how to tell which port the device is on
        sp = visa.ResourceManager('@py')
        # I'm not sure where the port comes in, I think it is USBX
        try:
            self.SP = rm.open_resource('USB0::2457::1012::C046401::0::INSTR')
        except:
            print("USB error: Could not connect to the spectrometer.")
        self.ID = self.get_ID()
        self.serialNum = self.ID.split(',')[2]
        print('Spectrometer ID:', self.ID)
        
    # Request spectrometer parameters
    #--------------------------------------------------------------------------
        
    def get_pixel(self):
        return self.SP.pixels()
    
    def get_wavelength(self):
        """get the spectrum wavelengths
        """
        return self.SP.wavelengths()
    
    def get_intensity(self):
        """get the spectrum intensities
        """
        return self.SP.intensities()
    
    def get_spectrum(self):
        """get the spectrum
        """
        return spectrum()
    
    def set_integration_time(self):
        return self.SP.integration_time_micros()
    
    def set_triggermode(self):
        return self.SP.trigger_mode()
    
    def scans_to_average(self):
        return self.SP.scans_to_average()
            
        