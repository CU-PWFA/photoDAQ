#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 17:19:27 2019

@author: robert
"""

from devices.device import Device
import serial
import time

class FRG700(Device):
    """ Class to control the arduino for the FRG700 and CDG500 vacuum gauges. """
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
            self.connection_error = True
            return
        self.ID = self.get_ID().decode("utf-8")
        # No way to get a serial number - address should be unique
        self.serialNum = address
        # Note: "IDN?" is programmed on the arduino to return 'FRG700'.
        # Currently bypassing the get_ID command and manually printing both
        # FRG700 and CDG500 instead of modifying the arduino code.
        print('Vacuum gauge IDs: FRG700 and CDG500') # + self.ID)
        
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
            The 6 ID bytes of the gauge (FRG700).
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

    # Manually convert voltage to pressure
    # -------------------------------------------------------------------------
    def voltage_to_pressure(self):
        """ Get the voltage reading of the arduino and manually convert to pressure. 
        
        Returns
        -------
        pressure : double array
            The pressure converted from voltage for each channel.
            Channel 0 must be the FRG700.
            Channel 3 must be the CDG500.
        """
        
        self.Gauge.write(b"VOLTAGE?")
        
        # Get a digital value from 0 to 4096 representing voltage
        v0 = int(self.Gauge.readline()) 
        v1 = int(self.Gauge.readline())
        v2 = int(self.Gauge.readline())
        v3 = int(self.Gauge.readline())

        # Convert back to volts. The Arduino is 12 bits. Operating in GAIN_TWOTHIRDS,
        # the total range is +-6.144. 
        v0_V = float(v0*0.003001) 
        v1_V = float(v1*0.003001)
        v2_V = float(v2*0.003001)
        v3_V = float(v3*0.003001)

        # Conversion for FRG-700:
        #        p[mbar] = 10**(1.667U-d), d = 11.33
        #        U = c + 0.6*log_10(p), c = 6.8
        # Conversion for CDG-500:
        #        p = (U/10)*p(F.S.), p(F.S.) = 1333 mbar
        # Note: voltage measured by arduino is half of the gauge voltage, so U = 2*vx_V.
        p0 = float(10**(2*1.667*v0_V-11.33))
        p1 = float(v1_V)
        p2 = float(v2_V)
        p3 = float(2*v3_V)
#        p3 = float(2*v3_V/10*1333)
        return [p0, p1, p2, p3]
    
    def close(self):
        """ Close method, doesn't do anything for a serial instrument. """
        self.Gauge.close()

