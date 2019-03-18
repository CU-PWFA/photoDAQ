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
        voltage : int array
            The integer read by the ADC.
        """
        self.Gauge.write(b"VOLTAGE?")
        v0 = int(self.Gauge.readline())
        v1 = int(self.Gauge.readline())
        v2 = int(self.Gauge.readline())
        v3 = int(self.Gauge.readline())
        return [v0, v1, v2, v3]
    
    def get_pressure(self):
        """ Get the pressure reading of the gauge. 
        
        Returns
        -------
        pressure : double array
            The pressure read by the gauge for each channel.
        """
        self.Gauge.write(b"PRESSURE?")
        # If the device list is refreshed, the arduino will reset and send an ID
        # This can't be parsed to a float and the device will fail
        try:
            p = self.Gauge.readline().decode("utf-8")
            p.strip()
            p = p.split(',')
            p0 = float(p[0])
            p1 = float(p[1])
            p2 = float(p[2])
            p3 = float(p[3])
            return [p0, p1, p2, p3]
        except ValueError:
            return [0.0, 0.0, 0.0, 0.0]
    
    def close(self):
        """ Close method, doesn't do anything for a serial instrument. """
        self.Gauge.close()

