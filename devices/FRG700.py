#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 17:19:27 2019

@author: robert
"""

import serial
import time

class FRG700():
    """ Class to control the arduino for the FRG700 vacuum gauge. """
    def __init__(self, address):
        """ Create the serial object for the gauge. """
        self.connectGauge(address)
        
    def connectGauge(self, address):
        """ Connect to the gauge and verify the connection. 
        
        Parameters
        ----------
        address : string
            The port the device is connected to, of the form "/dev/ttyACM2".
        """
        try:
            self.Gauge = serial.Serial(address,
                                    baudrate=9600,
                                    bytesize=8,
                                    parity='N',
                                    stopbits=1,
                                    timeout=2)
        except:
            print("USB error: Could not connect to the vacuum gauge.")
        self.ID = self.get_ID().decode("utf-8")
        # No way to get a serial number - address should be unique
        self.serialNum = address
        print('Vacuum gauge ID: ' + self.ID)
        # The gauge sends the id on start up and sometime get id catches that
        # This clears the get ID response
        time.sleep(2)
        self.Gauge.reset_input_buffer()
        
    # Request gauge parameters
    #--------------------------------------------------------------------------
    def get_ID(self):
        """ Get the gauge ID.
        
        Returns
        -------
        ID : bytes
            The 6 ID bytes of the gauge.
        """
        self.Gauge.write(b"*IDN?")
        return self.Gauge.readline(7).strip()
    
    def get_voltage(self):
        """ Get the output voltage of the gauge. 
        
        Returns
        -------
        voltage : int
            The integer read by the ADC.
        """
        self.Gauge.write(b"VOLTAGE?")
        return int.from_bytes(self.Gauge.read(1), byteorder='big')
    
    def get_pressure(self):
        """ Get the pressure reading of the gauge. 
        
        Returns
        -------
        pressure : double
            The pressure read by the gauge.
        """
        self.Gauge.write(b"PRESSURE?")
        # If the device list is refreshed, the arduino will reset and send an ID
        # This can't be parsed to a float and the device will fail
        try:
            return float(self.Gauge.readline())
        except ValueError:
            return 0.0
    
    def close(self):
        """ Close method, doesn't do anything for a serial instrument. """
        self.Gauge.close()

