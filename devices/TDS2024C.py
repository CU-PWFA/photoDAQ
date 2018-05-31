#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 30 09:54:58 2018

@author: robert
"""

import visa
import numpy as np

class TDS2024C():
    """ Class to control the Tektronix TDS2024C oscilloscope. 
    
    The oscilloscope must be set to Rear USB Port - Computer for this code to
    connect to it, this is found in Utility->Options.
    """
    def __init__(self, port=0):
        """ Create the serial object for the oscilloscope. """
        self.connectOS(port)
        self.setupOS()
    
    def connectOS(self, port):
        """ Connect to the oscilloscope and verify the connection. 
        
        Parameters
        ----------
        port : int
            The port the device is connected to.
        """
        # TODO figure out how to tell which port the device is on
        rm = visa.ResourceManager('@py')
        # I'm not sure where the port comes in, I think it is USBX
        try:
            self.OS = rm.open_resource('USB0::1689::934::C046401::0::INSTR')
        except:
            print("USB error: Could not connect to the oscilloscope.")
        self.ID = self.get_ID()
        print('Oscilloscope ID:', self.ID)
    
    def setupOS(self):
        """ Set settings required for correct waveform acquisition. """
        self.set_encoding("RIBinary")   # Binary, signed integer, big-endian
        self.set_bytes(1)               # Send data as a single byte
        self.set_data_start(1)          # Transfer the entire waveform
        self.set_data_stop(2500)
        
    # Request oscilloscope parameters
    #--------------------------------------------------------------------------
    def get_ID(self):
        """ Get the oscilloscope ID.
        
        Returns
        -------
        ID : string
            The make, model, serial number, and firmware version.
        """
        return self.OS.query("*IDN?")
    
    def get_horizontal(self):
        """ Get the settings of the horizontal commands. 
        
        Returns
        -------
        horizontal : string
            All the horizontal settings in one big string.
        """
        return self.OS.query("HORizontal?")
    
    def get_vertical(self, channel):
        """ Get the settings of the vertical commands for the passed channel.
        
        Parameters
        ----------
        channel : int
            The channel to return the vertical settings for.
        
        Returns
        -------
        vertical : string
            All the verticalsettings of the channel in one big string.
        """
        return self.OS.query("CH" + str(channel) + "?")
    
    def get_preamble(self):
        """ Returns the transmission and formatting settings for the waveform.
        
        The settings scorrespond to the waveform specified by DATa:SOUrce,
        the waveform must be on the oscilloscope screen to be transmitted.
        
        Returns
        -------
        preamble : string
            A string containing the fromatting and transmission settings.
        """
        return self.OS.query("WFMPre?")
    
    def get_curve(self):
        """ Get the data for the current waveform. 
        
        Note, the results will only be correct if the transmission format is
        correct, see setupOS.
        
        Returns
        -------
        curve : array
            Returns a python array of integers representing the waveform.
        """
        return self.OS.query_binary_values('CURVe?', 
                                           datatype='b', 
                                           is_big_endian=True)
    
    # Set oscilloscope parameters
    #--------------------------------------------------------------------------
    def set_encoding(self, encoding):
        """ Set the waveform encoding of the oscilloscope.
        
        Parameters
        ----------
        encoding : string
            See the Tektronix programming manual DATa:ENCdg for options.
        """
        self.OS.write("DATa:ENCdg " + encoding)
    
    def set_bytes(self, byteN):
        """ Set the number of bytes per waveform data point. 
        
        The scope only has precision of 1 byte per data point, setting this any
        higher than 1 is pointless and will set the rest of the bits to 0.
        
        Parameters
        ----------
        byteN : int
            The number of bytes per waveform data point, should be set to 1.
        """
        self.OS.write("DATa:WIDth " + str(byteN))
    
    def set_data_start(self, start):
        """ Set the first data point that will be transferred in a waveform.
        
        Transferring smaller waveforms does not significantly decrease the
        transfer time. 2500 takes 1.19s and 10 takes 1.07s, might as well
        transfer the entire dataset so leave this at 1.
        
        Parameters
        ----------
        start : int
            The first data point to transfer, from 1 to 2500.
        """
        self.OS.write("DATa:STARt " + str(start))
        
    def set_data_stop(self, stop):
        """ Set the last data point that will be transferred in a waveform.
        
        Transferring smaller waveforms does not significantly decrease the
        transfer time. 2500 takes 1.19s and 10 takes 1.07s, might as well
        transfer the entire dataset so leave this at 2500.
        
        Parameters
        ----------
        start : int
            The last data point to transfer, from 1 to 2500.
        """
        self.OS.write("DATa:STOP " + str(stop))
        
    def set_data_source(self, source):
        """ Set the source for data transfer. 
        
        Parameters
        ----------
        source : string
            The data source, either CH<X>, MATH, or REF<X>.
        """
        self.OS.write("DATa:SOUrce " + source)
    
    # Oscilloscope data managment
    #--------------------------------------------------------------------------
    def 
    