#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 28 13:34:57 2018

@author: cu-pwfa
"""

import seabreeze.spectrometers as sb

class HR4000():
    """ Notes about the spectrometer:
        If it doesn't connect almost immediatly, it probably won't return data.
        If it is disconnected while streaming data, it will break.
    """
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
        # Default integration time is set to 100ms
        self.set_integration_time(100000.)
        
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
        """ Get the number of pixels in the spectrometer. 
        
        Returns
        -------
        pixel : int
            The number of pixels in the spectrometer.
        """
        return self.SP.pixels()
    
    def get_wavelength(self):
        """Get the wavelengths of the spectrum for each pixel. 
        
        Returns
        -------
        wavelength : array-like
            An array of wavelengths corresponding to each pixel.
        """
        return self.SP.wavelengths()
    
    def get_intensity(self):
        """Get the spectrum intensities. 
        
        Returns
        -------
        intensity : array-like
            The intensity of the light at each wavelength.
        """
        return self.SP.intensities()
    
    def get_spectrum(self):
        """ Get the spectrum, wavelengths and intensities. 
        
        Returns
        -------
        spectrum : array-like
            The first element [0, :] is the wavelengths, the second is intensities [1, :].
        """
        return self.SP.spectrum()
    
    def set_integration_time(self, time):
        """ Set the spectrometer integration time. 
        
        Parameters
        ----------
        time : int
            Integration time in microseconds.
        """
        self.SP.integration_time_micros(time)
    
    def set_triggermode(self, mode):
        """ Set the trigger mode of the spectrometer. 
        
        Parameters
        ----------
        mode : string
            Need to find documentation on this, what are the options? Is it a string?
        """
        self.SP.trigger_mode()
    
    def close(self):
        """ Disconnect the spectrometer. """
        self.SP.close()
            
        