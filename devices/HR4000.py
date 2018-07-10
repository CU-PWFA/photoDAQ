#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 28 13:34:57 2018

@author: cu-pwfa
"""

import seabreeze.spectrometers as sb

class HR4000():
    
    def __init__(self, serial):
        self.connectSP(serial)
        
    def connectSP(self, serial):
        """ Connect to the spectrometer and verify the connection. 
        
        Parameters
        ----------
        serial : int
            The serial number of the spectrometer.
        """
        try:
            self.SP = sb.Spectrometer.from_serial_number(serial)
        except:
            print("USB error: Could not connect to the spectrometer.")
        self.ID = self.get_ID()
        self.serialNum = self.SP.serial_number
        print('Spectrometer ID:', self.ID)
        
    # Request spectrometer parameters
    #--------------------------------------------------------------------------
    def get_ID(self):
        """ Get the spectrometer ID.
        
        Returns
        -------
        ID : string
            The make, model, serial number, and firmware version.
        """
        SP = self.SP
        return SP.model + ',' + str(self.SP.serial_number)
    
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
        return self.PS.spectrum()
    
    def set_integration_time(self):
        return self.SP.integration_time_micros()
    
    def set_triggermode(self):
        return self.SP.trigger_mode()
    
    def scans_to_average(self):
        return self.SP.scans_to_average()
    
    def close(self):
        """ Disconnect the spectrometer. """
        self.SP.close()
            
        