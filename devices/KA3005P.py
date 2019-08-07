#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 29 16:31:09 2018

@author: robert
"""

from devices.device import Device
import serial

class KA3005P(Device):
    """ Class to control the Korad KA3005P power supply.
    
    Note, the power supply needs at least 0.05s between commands or else
    it will not execute all of the commands.
    """
    def __init__(self, address):
        """ Create the serial object for the power supply. """
        self.connectPS(address)
        
    def connectPS(self, address):
        """ Connect to the power supply and verify the connection. 
        
        Parameters
        ----------
        address : string
            The port the device is connected to, "<address>" is the 
            device name sent to pyserial.
        """
        try:
            self.PS = serial.Serial(address,
                                    baudrate=9600,
                                    bytesize=8,
                                    parity='N',
                                    stopbits=1,
                                    timeout=1)
        except:
            print("USB error: Could not connect to the power supply.")
            self.connection_error = True
            return
        self.ID = self.get_ID().decode("utf-8")
        # No way to get a serial number - address should be unique
        self.serialNum = address
        print('Power supply ID:', self.ID)
        
    def status(self):
        """ Print the power supply status in a readable form. """
        status = self.get_status()
        # Extract the individual bits in the response string
        status = int.from_bytes(status, byteorder='big')
        flag0 = status & 1
        flag6 = status & 64
        if flag0 == 0 : print("Constant current (C.C)")
        else : print("Constant voltage (C.V)")
        if flag6 == 0 : print("Power supply OFF")
        else : print("Power supply ON")
    
    # Request power supply parameters
    #--------------------------------------------------------------------------
    def get_ID(self):
        """ Get the power supply ID.
        
        Returns
        -------
        ID : bytes
            The 16 ID bytes of the power supply.
        """
        self.PS.write(b"*IDN?")
        return self.PS.read(16)
    
    def get_status(self):
        """ Get the power supply status.
        
        Returns
        -------
        status : bytes
            The 5 status bytes of the power supply.
        """
        self.PS.flushInput()
        self.PS.write(b"STATUS?")
        return self.PS.read(1)
    
    def get_voltage(self):
        """ Get the actual output voltage of the power supply.
        
        Returns
        -------
        voltage : double
            The actual output voltage of the power supply. 
        """
        self.PS.write(b"VOUT1?")
        try:
            return float(self.PS.read(5))
        except ValueError:
            return 0.0
    
    def get_current(self):
        """ Get the actual output current of the power supply.
        
        Returns
        -------
        current : double
            The actual output current of the power supply. 
        """
        self.PS.write(b"IOUT1?")
        try:
            return float(self.PS.read(5))
        except ValueError:
            return 0.0
    
    def get_set_voltage(self):
        """ Get the target voltage of the power supply.
        
        Returns
        -------
        voltage : double
            The target voltage of the power supply. 
        """
        self.PS.write(b"VSET1?")
        return float(self.PS.read(5))
    
    def get_set_current(self):
        """ Get the target current of the power supply.
        
        Returns
        -------
        current : double
            The target current of the power supply. 
        """
        self.PS.write(b"IOUT1?")
        return float(self.PS.read(5))
    
    # Set power supply parameters
    #--------------------------------------------------------------------------
    def set_voltage(self, v):
        """ Set the target power supply voltage. 
        
        Parameters
        ----------
        v : double
            The voltage (V) to set the power supply to, will round to 10mV.
        """
        maxV = 30.00
        if v > maxV: 
            v = maxV
        v = "%2.2f" % v
        self.PS.write(b"VSET1:" + bytes(v, "utf-8"))
        
    def set_current(self, i):
        """ Set the target power supply current. 
        
        Parameters
        ----------
        i : double
            The current (A) to set the power supply to, will round to 1mA.
        """
        maxi = 5.000
        if i > maxi: i = maxi
        i = "%1.3f" % i
        self.PS.write(b"ISET1:" + bytes(i, "utf-8"))
        
    def ovp_on(self):
        """ Turn over voltage protection on. """
        self.PS.write(b"OVP1")
        
    def ovp_off(self):
        """ Turn over voltage protection off. """
        self.PS.write(b"OVP0")
        
    def ocp_on(self):
        """ Turn over current protection on. """
        self.PS.write(b"OCP1")
        
    def ocp_off(self):
        """ Turn over current protection off. """
        self.PS.write(b"OCP0")
    
    # Control the power supply
    #--------------------------------------------------------------------------
    def turn_on(self):
        """ Turn the power supply on. """
        self.PS.write(b"OUT1")
    
    def turn_off(self):
        """ Turn the power supply off. """
        self.PS.write(b"OUT0")
        
    def close(self):
        """ Close the instrument (turn off, dont need to disconnect). """
        self.turn_off()
        
    