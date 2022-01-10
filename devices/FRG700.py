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
    def __init__(self, address, gaugeTypes=["FRG700", "FRG700", "CDG500T1000", "CDG500T1000"]):
        """ Create the serial object for the gauge. """
        self.gaugeTypes = gaugeTypes
        self.connectGauge(address)
        
    def connectGauge(self, address):
        """ Connect to the arduino and verify the connection. 
        
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
            print("USB error: Could not connect to the vacuum gauge controller.")
            self.connection_error = True
            return
        self.ID = self.get_ID().decode("utf-8")
        # No way to get a serial number - address should be unique
        self.serialNum = address
        print('Vacuum gauge controller ID: ' + self.ID)
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
        return self.Gauge.readline(4).strip()
    
    def get_voltage(self):
        """ Get the output voltage of the gauge. 
        
        Returns
        -------
        voltage : int array
            The integer read by the ADC.
        """
        try:
            self.Gauge.write(b"VOLTAGE?")
            # Get a digital value from 0 to 4096 representing voltage
            v0 = int(self.Gauge.readline())
            v1 = int(self.Gauge.readline())
            v2 = int(self.Gauge.readline())
            v3 = int(self.Gauge.readline())
            return [v0, v1, v2, v3]
        except ValueError:
            print("Vacuum gauge controller voltage read error, returning all voltages as 0.")
            self.Gauge.reset_input_buffer()
            return [0, 0, 0, 0]

    # Manually convert voltage to pressure
    # -------------------------------------------------------------------------
    def voltage_to_pressure(self):
        """ Get the voltage reading of the arduino and manually convert to pressure. 
        This assumes the gas is air/nitrogen- value needs to be corrected for other gases.
        
        Returns
        -------
        pressure : double array
            The pressure converted from voltage for each channel.
            Channel 0 must be the FRG700.
            Channel 3 must be the CDG500.
        """
        try:
            self.Gauge.write(b"VOLTAGE?")
            # Get a digital value from 0 to 4096 representing voltage
            v0 = int(self.Gauge.readline()) 
            v1 = int(self.Gauge.readline())
            v2 = int(self.Gauge.readline())
            v3 = int(self.Gauge.readline())
        except ValueError:
            print("Vacuum gauge controller voltage read error, returning all voltages as 0.")
            self.Gauge.reset_input_buffer()
            return [0.0, 0.0, 0.0, 0.0]

        # Convert back to volts. The Arduino is 12 bits. Operating in GAIN_TWOTHIRDS,
        # the total range is +-6.144. 
        v0_V = float(v0*0.003001) 
        v1_V = float(v1*0.003001)
        v2_V = float(v2*0.003001)
        v3_V = float(v3*0.003001)
        v = [v0_V, v1_V, v2_V, v3_V]

        # Conversion for FRG-700:
        #        p[mbar] = 10**(1.667U-d), d = 11.33
        #        U = c + 0.6*log_10(p), c = 6.8
        # Conversion for CDG-500 T1000:
        #        p = (U/10)*p(F.S.), p(F.S.) = 1333 mbar for 1000Torr gauge
        # Note: voltage measured by arduino is half of the gauge voltage, so U = 2*vx_V.
        p = [0.0, 0.0, 0.0, 0.0]
        for i in range(4):
            if self.gaugeTypes[i] == "FRG700":
                p[i] = float(10**(2*1.667*v[i]-11.33))
            elif self.gaugeTypes[i] == "CDG500T1000":
                p[i] = float(2*v[i]/10*1333.22)
            elif self.gaugeTypes[i] == "CDG500T0100":
                p[i] = float(2*v[i]/10*133.322)
            elif self.gaugeTypes[i] == "CDG500T0010":
                p[i] = float(2*v[i]/10*13.3322)
            elif self.gaugeTypes[i] == "CDG500T0001":
                p[i] = float(2*v[i]/10*1.33322)
            else:
                print("Gauge type {:s} is not recognized.".format(self.gaugeTypes[i]))
        return p
    
    def close(self):
        """ Close method, doesn't do anything for a serial instrument. """
        self.Gauge.close()

