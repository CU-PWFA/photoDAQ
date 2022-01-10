#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 14:21:57 2019

@author: robert
"""

from devices.device import Device
import serial
import time

class TC(Device):
    """ Class to control the arduino for the FRG700 vacuum gauge. """
    def __init__(self, address):
        """ Create the serial object for the gauge. """
        self.connectController(address)
        
    def connectController(self, address):
        """ Connect to the gauge and verify the connection. 
        
        Parameters
        ----------
        address : string
            The port the device is connected to, of the form "/dev/ttyACM2".
        """
        try:
            self.TC = serial.Serial(address,
                                    baudrate=9600,
                                    bytesize=8,
                                    parity='N',
                                    stopbits=1,
                                    timeout=2)
        except:
            print("USB error: Could not connect to the timing controller.")
            self.connection_error = True
            return
        self.ID = self.get_ID().decode("utf-8")
        # No way to get a serial number - address should be unique
        self.serialNum = address
        print('Timing controller ID: ' + self.ID)
        # The gauge sends the id on start up and sometime get id catches that
        # This clears the get ID response
        time.sleep(2)
        self.TC.reset_input_buffer()
        
    # Request controller parameters
    #--------------------------------------------------------------------------
    def get_ID(self):
        """ Get the gauge ID.
        
        Returns
        -------
        ID : bytes
            The 6 ID bytes of the gauge.
        """
        self.TC.write(b"*IDN?")
        return self.TC.readline(7).strip()
    
    # Control the controller
    #--------------------------------------------------------------------------
    def reset(self, shots):
        """ Reset the shot counter and the maximum shots. 
        
        Parameters
        ----------
        shots : int
            The number of shots to take for the dataset.
        """
        self.TC.write(b"R" + bytes(str(shots), "utf-8"))
        
    def start(self):
        """ Enable the delay generator and start taking data. """
        self.TC.write(b"ON")
        
    def stop(self):
        """ Disable the delay generator and stop taking data. """
        self.TC.write(b"OFF")
        
    # Read data from the controller
    #--------------------------------------------------------------------------
    def get_shot(self):
        """ Get the current shot from the controller. 
        
        Returns
        -------
        shot : int
            The current shot of the dataset
        """
        try:
            shot = int(self.TC.readline().decode("utf-8"))
        except:
            shot = None
        return shot
    
    def close(self):
        """ Close method, doesn't do anything for a serial instrument. """
        self.TC.close()
    
    
    def FreeRun(self):
        '''Enable the free run mode'''
        self.TC.write(b"FR")
        