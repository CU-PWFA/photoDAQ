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
    
    The oscilloscope must be set to Rear USB Port = "Computer" for this code to
    connect to it, this is found in Utility->Options. Auto will not work.
    """
    def __init__(self, port=0):
        """ Create the serial object for the oscilloscope. """
        self.connectOS(port)
        self.setupOS()
        self.OS.timeout = 25e4
        self.pre_fields = [
                "Byte number",      #BYT_Nr bytes per data point (byte width)
                "Bit number",       #BIT_Nr bits per data point (bit width)
                "Encoding",         #ENCdg encoding method (ASC or BIN)
                "Binary encoding",  #BN_Fmt signed or positive int (RI or RP)
                "Byte order",       #BYT_Or byte order (LSB or MSB)
                "Data points",      #NR_Pt number of points in the curve
                "Wavefront ID",     #WFId waveform identifier, lots of info
                "Point format",     #PT_Fmt (ENV or Y) Y is normal
                "Sampling interval",#XINcr time between samples
                "Trigger offset",   #PT_Off trigger offset always 0
                "Start time",       #XZEro time of the first data point
                "Horizontal unit",  #XUNit always "s"
                "Vertical scale",   #YMUlt YUNits per digitizer level
                "Conversion factor",#YZEro converts values to YUNits (offset)
                "Vertical position",#YOFf offsets units in digitizer levels
                "Vertical units"    #YUNit vertical units (can be a current)
                ]
        self.pre_format = ["int", "int", "str", "str", "str", "int", "str",
                           "str", "float", "float", "float", "str", "float",
                           "float", "float", "str"]
    
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
        
    def set_acquisition_mode(self, mode):
        """ Set the acquisition mode of the oscilloscope.
        
        Parameters
        ----------
        mode : string
            See the Tektronix programming manual ACQuire:MODe for options.
        """
        self.OS.write("ACQuire:MODe " + mode)
        
    def set_acquisition_stop(self, stop):
        """ Set whether the oscilliscope stops with the stop button or not.
        
        Parameters
        ----------
        stop : string
            RUNSTop means stop on button, SEQuence means stop after complete.
        """
        self.OS.write("ACQuire:STOPAfter " + stop)
        
    def set_average_num(self, num):
        """ Set the number of waveforms to acquire and average over. 
        
        The oscilliscope must be in acquisition mode AVErage to use this.
        
        Parameters
        ----------
        num : int
            The number of waveforms to average over, 4, 16, 64, or 128 allowed.
        """
        self.OS.write("ACQuire:NUMAVg " + str(num))
        
    # Control the oscilloscope
    #--------------------------------------------------------------------------    
    def acquire_on(self):
        """ Begin data aquisition. """
        self.OS.write("ACQuire:STATE ON")
        
    def acquire_off(self):
        """ Stop data aquisition. """
        self.OS.write("ACQuire:STATE OFF")
    
    def wait(self):
        """ Tells the oscilloscope to wait to finish the current command.
        
        The oscilliscope will wait to finish the current command (for example
        an acquisition) before it executes the next command.
        """
        self.OS.write("*WAI")
    
    def check_busy(self):
        """ Check if the oscilloscope has a pending command. """
        return self.OS.query("BUSY?")
    
    # Oscilloscope data managment
    #--------------------------------------------------------------------------
    def decode_preamble(self, pre):
        """ Decode the preamble into a more usable dictionary. 
        
        Parameters
        ----------
        pre : string
            Preamble string, the return of get_preamble.
        
        Returns
        -------
        preamble : dict
            A dictionary with all of the parts from the preamble.
        """
        preamble = {}
        pre = pre.strip("\n")   #Remove the newline from the end
        pre = pre.split(";")    #Brake the string into the different fields
        for i in range(len(pre)):
            if self.pre_format[i] == "int":
                preamble[self.pre_fields[i]] = int(pre[i])
            elif self.pre_format[i] == "float":
                preamble[self.pre_fields[i]] = float(pre[i])
            elif self.pre_format[i] == "str":
                preamble[self.pre_fields[i]] = pre[i].strip('"')
        return preamble
    
    def verify_format(self, pre):
        """ Verify the data format is correct for extraction. 
        
        Parameters
        ----------
        pre : dict
            The preamble dictionary, produced by decode_preamble.
        
        Returns
        -------
        verify : bool
            False if there is a format issue, true otherwise.
        """
        if len(pre) == 5:
            print("Scope error: only format, source not displayed.")
            return False
        elif pre["Byte number"] != 1:
            print("Scope error: Incorrect number of bytes per data point.")
            return False
        elif pre["Bit number"] != 8:
            print("Scope error: Incorrect number of bits per data point.")
            return False
        elif pre["Encoding"] != 'BIN':
            print("Scope error: Encoding is not binary.")
            return False
        elif pre["Binary encoding"] != 'RI':
            print("Scope error: Binary encoding is not signed.")
            return False
        elif pre["Byte order"] != 'MSB':
            print("Scope error: Most significant bit is not first.")
            return False
        else:
            return True
        
    def binary_to_volts(self, curve, pre):
        """ Convert the binary data from the scope into voltages. 
        
        Parameters
        ----------
        curve : array-like
            The binary waveform data from the scope (get_curve output).
        pre : dict
            The preamble dictionary, produced by decode_preamble.
            
        Returns
        -------
        y : array-like
            The waveform expressed in volts.
        """
        waveform = np.array(curve, dtype='int')
        y = ((waveform - pre["Vertical position"])*pre["Vertical scale"]
                + pre["Conversion factor"])
        return y
        
    def build_t(self, pre):
        """ Build the array of time values. 
        
        Parameters
        ----------
        pre : dict
            The preamble dictionary, produced by decode_preamble.
            
        Returns
        -------
        t : array-like
            The array of time values. 
        """
        end = pre["Start time"] + pre["Sampling interval"]*pre["Data points"]
        t = np.arange(pre["Start time"], end, pre["Sampling interval"])
        return t
        
    def retrieve_current_waveform(self):
        """ Retrieve the current waveform and convert it into useful units.
        
        The current waveform is specified by DATa:SOUrce, it must be displayed
        on the oscilloscope for this code to work. The transmission format is
        also verified.
        
        Returns
        -------
        x : array-like
            The array of time values for each sample point in seconds.
        y : array-like
            The array of sample values in volts.
        """
        pre = self.get_preamble()
        curve = self.get_curve()
        
        pre = self.decode_preamble(pre)
        if self.verify_format(pre) != True:
            return [], []
        y = self.binary_to_volts(curve, pre)
        t = self.build_t(pre)
        return t, y
    
    def acquire_waveform(self):
        """ The oscilloscope will acquire a waveform and transmit it.
        
        The oscilliscope will wait for a trigger signal, acquire the waveform,
        stop acquisition, and finally transmit the waveform. 
        
        Returns
        -------
        x : array-like
            The array of time values for each sample point in seconds.
        y : array-like
            The array of sample values in volts.
        """
        self.acquire_off()
        self.set_acquisition_mode("SAMple")
        self.set_acquisition_stop("SEQuence")
        self.acquire_on()
        # XXX The best way would be to use some kind of event listening to the scope
        esc = 0
        while True:
            if self.check_busy().strip('\n') == '0': 
                break
            if  esc > 25:
                print("Acquisition timed out")
                return [], []
            esc += 1
        return self.retrieve_current_waveform()
    
    def acquire_average_waveform(self, num):
        """ The oscilloscope will acquire and average several waveforms.
        
        The oscilliscope will wait for a trigger signal, acquire the waveform,
        repeat several times averaging the signals together, stop acquisition,
        and finally transmit the waveform. 
        
        Returns
        -------
        x : array-like
            The array of time values for each sample point in seconds.
        y : array-like
            The array of sample values in volts.
        """
        if num == 4 or num == 16 or num == 64 or num == 128:
            self.set_average_num(num)
        else:
            print("Scope error: Number to average must be 4, 16, 64, or 128.")
            return [], []
        self.acquire_off()
        self.set_acquisition_mode("AVErage")
        self.set_acquisition_stop("SEQuence")
        self.acquire_on()
        # XXX The best way would be to use some kind of event listening to the scope
        esc = 0
        while True:
            if self.check_busy().strip('\n') == '0': 
                break
            if  esc > 25:
                print("Acquisition timed out")
                return [], []
            esc += 1
        return self.retrieve_current_waveform()
        
    