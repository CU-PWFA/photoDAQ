#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 16:26:49 2018

@author: cu-pwfa
"""

import instruments as ik
import quantities as pq

class SRSDG645():
    """ Class to control Signal Delay Generator. """
    
    def __init__(self, serial, set_default=True):
        """ Create the object for the signal delay generator. """
        self.channels = {'0' : 'T0',
                         '1' : 'T1',
                         '2' : 'A',
                         '3' : 'B',
                         '4' : 'C',
                         '5' : 'D',
                         '6' : 'E',
                         '7' : 'F',
                         '8' : 'G',
                         '9' : 'H'}
        
        self.outputs = {'0' : 'T0',
                        '1' : 'AB',
                        '2' : 'CD',
                        '3' : 'EF',
                        '4' : 'GH'}
        
        self.connectSRSDG(serial)
        
    def connectSRSDG(self, serial):
        """Connect to the Signal Delay Generator.
        
        Parameters
        ----------
        serial : int
            the ethernet port number the SDG is connected to
        """
        try:
            self.srs = ik.srs.SRSDG645.open_tcpip('169.254.248.180', serial)
            self.serialNum = serial
            self.ID = self.srs.query('*IDN?')
        except:
            print('Ethernet error: could not connect to Signal Delay Generator.')
            
    def set_trigger_threshold(self, threshold):
        """Set the trigger threshold for SDG.
        
        Parameters
        ----------
        threshold : float
            voltage at which the trigger threshold will be set
        """
        self.srs.sendcmd('TLVL{}'.format(threshold))
        
    def set_trigger_source(self, i):
        """ Sets the source of the SDG trigger system.
        
        Parameters
        ----------
        i : int
            0 : internal
            1 : External rising edges
            2 : External falling edges
            3 : Single shot external rising edges
            4 : Single shot external falling edges
            5 : Single shot
            6 : Line
        """
        self.srs.sendcmd('TSRC{}'.format(i))
            
    def set_delay(self, settings):
        """ Set the delay between channels.
        
        Parameters
        ----------
        settings : list
            [ref_chan, set_chan, delay]
        ref_chan : str
            the channel which the delay is set from
        set_chan : str
            the channel whose delay is being set
        delay : int
            the time delay between channels in sec.
        """
        ref_chan, set_chan, delay = settings
        self.srs.channel[set_chan].delay = (self.srs.channel[ref_chan], pq.Quantity(delay, 's'))
        
    def set_output(self, settings, pol=None):
        """Set the output channel signal in volts.
        
        Parameters
        ----------
        settings : list
            [output, level]
        output : str
            the output channels to be set
        level : int
            output value in volts, must be between 0.5 and 5
        pol : int
            polarity of output, 0 in negative 1 is positive (default is 1).
        """
        output, level = settings
        self.srs.output[output].level_amplitude = pq.Quantity(level, 'V')
        if pol is not None:
            self.srs.output[output].polarity = self.srs.LevelPolarity(pol)
            
    def save_settings_SDG(self, i):
        """Save instrument settings on SDG.
        
        Parameters
        ----------
        i : int
            location on SDG where settings are saved (1 to 9)
        """
        self.srs.sendcmd('*SAV{}'.format(i))
        
    def recall_settings_SDG(self, i):
        """Recall instrument settings from SDG.
        
        Parameters
        ----------
        i : int
            location of SDG where settings to be recalled are stored (1 to 9)
        """
        self.srs.sendcmd('*RCL{}'.format(i))
        
    def recall_default_settings_SDG(self):
        """Recall default instrument settings."""
        self.srs.sendcomd('*RST')
        
    def get_status(self):
        """ Queries the SDG for its current status."""
        resp = self.srs.query('INSR?')
        return resp
        
    def send_comd(self, code):
        """Send a command directly to SRSDG645. 
        
        Parameters
        ----------
        code : str
            ASCII code for the command.  Found in Operation Manuel (pg. 48-59).
        """
        self.srs.sendcomd(code)
        
    def send_query(self, code):
        """Send a query directly to SRSDG645.
        
        Parameters
        ----------
        code : str
            ASCII code for the query. Found in Operation Manuel (pg. 48-59).
        """
        resp = self.query(code) 
        print(resp)