#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 17:21:21 2019

@author: robert
"""

import serial
import time

class FS304():
    """ Class to control the TwissTorr 304FS turbomolecular pump. """
    def __init__(self, address):
        """ Create the serial object for the turbo pump. """
        self.connect(address)
        self.setup()
    
    def connect(self, address):
        """ Connect to the turbo pump and verfy the connection. 
        
        Parameters
        ----------
        address : string
            The port the device is connected to, "/dev/<address>" is the 
            device name sent to pyserial.
        """
        try:
            self.TMP = serial.Serial(address,
                                    baudrate=9600,
                                    bytesize=8,
                                    parity='N',
                                    stopbits=1,
                                    timeout=2)
        except:
            print("USB error: Could not connect to the turbomolecular pump.")    
        self.ID = address
        # No way to get a serial number - address should be unique
        self.serialNum = address
        print('Turbopump ID:', address)
        
    def setup(self):
        """ Set pump parameters to their correct values. """
        self.set_water_cooling(False)
        
    # Request pump parameters
    #--------------------------------------------------------------------------
    def write(self, window, data=None):
        """ Create a command for the pump. 
        
        Parameters
        ----------
        window : string
            The 3 numbers corresponding to the command, see controller manual for
            window-command correspondence.
        data : string
            The value to send to the pump.
        """
        window_b = window.encode('utf-8')
        if data is None:
            # Set the command byte of the serial string
            command = b'\x30'
            data = b''
        else:
            command = b'\x31'
            data = data.encode('utf-8')
        message = b'\x80' + window_b + command + data + b'\x03'
        # The CRC is just a single byte, which can be written as a hex
        # The hex can be written as two ascii characters, which can be encoded into two bytes
        crc = 0
        for c in message:
            crc = crc^c
        
        message = b'\x02' + message + hex(crc)[2:].encode('utf-8')
        self.TMP.write(message)
    
    def read(self):
        """ Read the response from the pump and strip extraneous characters. 
        
        Returns
        -------
        rsp : string
            The response from the pump as a string.
        """
        try:
            rsp = self.TMP.read_until(b'\x03')
            self.TMP.read(2) # Read the crc bytes from the buffer
            rsp = rsp[5:-1] # Strip the boilerplate characters
            return rsp.decode('utf-8')
        except:
            print('Read failure, turbo pump did not respond correctly.')
            return None
        
    def acknowledge(self):
        """ Recieve the acknowledgment from the pump. 
        
        Returns
        -------
        ack : bool
            Whether the command was successful or not. 
        """
        try:
            rsp = self.TMP.read_until(b'\x03')
            self.TMP.read(2)
            if rsp[2] == b'\x06':
                return True
            else:
                return False
        except:
            print('Read failure, turpo pump did not acknowledge correctly.')
            return False
    
    def get_status(self):
        """ Get the status of the pump and return it as a string. 
        
        Returns
        -------
        status : string
            The status of the pump.
        """
        self.write('205')
        try:
            rsp = int(self.read())
        except:
            print('Invalid status returned')
            rsp = 10
        if rsp == 0: status = 'Stop'
        elif rsp == 1: status = 'Interlock'
        elif rsp == 2: status = 'Starting'
        elif rsp == 3: status = 'Auto-tuning'
        elif rsp == 4: status = 'Braking'
        elif rsp == 5: status = 'Normal'
        elif rsp == 6: status = 'Fail'
        else: status = 'Unknown'
        return status
    
    def get_power(self):
        """ Get the pump power in watts. 
        
        Returns
        -------
        power : int
            The pump power in watts.
        """
        self.write('202')
        rsp = self.read()
        power = 0.0
        if rsp is not None:
            power = int(rsp)
        return power
    
    def get_current(self):
        """ Get the pump current in mA. 
        
        Returns
        -------
        current : int
            The pump current in mA.
        """
        self.write('200')
        rsp = self.read()
        current = 0.0
        if rsp is not None:
            current = int(rsp)
        return current
    
    def get_voltage(self):
        """ Get the pump voltage in V. 
        
        Returns
        -------
        voltage : int
            The pump voltage in V.
        """
        self.write('201')
        rsp = self.read()
        voltage = 0.0
        if rsp is not None:
            voltage = int(rsp)
        return voltage
    
    def get_driving_frequency(self):
        """ Get the pump driving frequency in Hz. 
        
        Returns
        -------
        frequency : int
            The pump driving frequency in Hz.
        """
        self.write('203')
        rsp = self.read()
        frequency = 0.0
        if rsp is not None:
            frequency = int(rsp)
        return frequency
    
    def get_temperature(self):
        """ Get the pump temperature in deg C. 
        
        Returns
        -------
        temperature : int
            The pump temperature in deg C.
        """
        self.write('204')
        rsp = self.read()
        temperature = 0.0
        if rsp is not None:
            temperature = int(rsp)
        return temperature
    
    def get_error(self):
        """ Read any errors from the pump. 
        
        Returns
        -------
        error : string
            The error reported by the pump.
        """
        # The errors should be parsed from the response but the response format is unclear
        # I assume we convert to an int and use a bit mask
        self.write('206')
        try:
            rsp = int(self.read())
        except:
            print('Invalid error returned')
            rsp = 0
        if rsp == 0: error = 'None'
        elif rsp & 1: error = 'No connection'
        elif rsp & 2: error = 'Pump overtemp'
        elif rsp & 4: error = 'controller overtemp'
        elif rsp & 8: error = 'Power fail'
        elif rsp & 16: error = 'Aux fail'
        elif rsp & 32: error = 'Overvoltage'
        elif rsp & 64: error = 'Short circuit'
        elif rsp & 128: error = 'Too high load'
        return error
    
    def get_pump_life(self):
        """ Get the pump life in hours. 
        
        Returns
        -------
        life : int
            The pump life in hours.
        """
        self.write('302')
        life = int(self.read())
        return life
    
    def get_soft_start(self):
        """ Get whether soft start is turned on or not. 
        
        Returns
        -------
        soft : bool
            True if soft start is on.
        """
        self.write('100')
        soft = int(self.read())
        return bool(soft)
    
    def get_water_cooling(self):
        """ Get whether the pump is set to water cooling or not. 
        
        Returns
        -------
        water : bool
            True if water colling is turned on.
        """
        self.write('106')
        water = int(self.read())
        return bool(water)
    
    # Control the pump
    #--------------------------------------------------------------------------
    def turn_on(self):
        """ Turn the turbo pump on. """
        self.write('000', '1')
        time.sleep(0.05)
        self.acknowledge()
        
    def turn_off(self):
        """ Turn the turbo pump off. """
        self.write('000', '0')
        time.sleep(0.05)
        self.acknowledge()
        
    def set_soft_start(self, soft):
        """ Set soft start on or off. 
        
        Parameters
        ----------
        soft : bool
            True to turn soft start on.
        """
        if soft: self.write('100', '1')
        else: self.write('100', '0')
        self.acknowledge()
        
    def set_water_cooling(self, water):
        """ Set whether the pump is water cooled or not. 
        
        Parameters
        ----------
        water : bool
            True if water cooling is being used.
        """
        if water: self.write('106', '1')
        else: self.write('106', '0')
        self.acknowledge()
        
    def close(self):
        """ Close method, doesn't do anything for a serial instrument. """
        self.TMP.close()