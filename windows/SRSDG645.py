#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 13:51:25 2019

@author: robert
"""

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt4.QtGui import (QPixmap, QImage, QLabel)
import numpy as np
import threading
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "SRSDG645.ui")
Ui_DGWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class DGWindow(QtBaseClass, Ui_DGWindow):
    data_acquired = pyqtSignal(object)
    device_connected = pyqtSignal()
    
    def __init__(self, parent, DAQ, instr):
        """ Create the parent class and add event handlers. 
        
        Parameters
        ----------
        parent : QtClass
            The parent window that creates this window.
        DAQ : DAQ class
            The class representing the DAQ.
        serial : string or int
            The serial number or string of the device the window is for.
        instr : instr object
            Object for an instrument.
        """
        QtBaseClass.__init__(self)
        Ui_DGWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.data_acquired.connect(self.update_fields)
        self.device_connected.connect(self.setup_window)
        self.channelField.activated.connect(self.change_channel)
        self.referenceField.activated.connect(self.change_settings)
        self.polarityField.activated.connect(self.change_settings)
        self.sField.valueChanged.connect(self.change_settings)
        self.msField.valueChanged.connect(self.change_settings)
        self.usField.valueChanged.connect(self.change_settings)
        self.nsField.valueChanged.connect(self.change_settings)
        self.psField.valueChanged.connect(self.change_settings)
        self.sourceField.activated.connect(self.change_trigger)
        self.thresholdField.valueChanged.connect(self.change_threshold)
        self.saveButton.clicked.connect(self.save_settings)
        self.recallButton.clicked.connect(self.recall_settings)
        
        # Grab references for controlling the delay generator
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.updating = False
        self.connected = False
        
        # Define some useful enumerations
        self.channels = ['T0', 'T1', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        self.index = {'T0':0, 'T1':1, 'A':2, 'B':3, 'C':4, 'D':5, 'E':6, 'F':7,
                      'G':8, 'H':9}
        
        self.create_update_thread()
        self.setWindowTitle(self.serial)
        
    def create_update_thread(self):
        """ Create a thread to poll the response queue and update the fields. """
        args = (self.queue, self.data_acquired.emit, self.device_connected.emit)
        thread = threading.Thread(target=self.update_thread, args=args)
        thread.setDaemon(True)
        thread.start()
        
    def update_thread(self, queue, callback, setup):
        """ Wait for updated data to display. 
        
        Parameters
        ----------
        queue : queue
            The queue that the data is arriving on.
        callback : func
            The signal.emit to call to update the fields. 
        setup : func
            The signal.emit to call when the device is connected.
        """
        while True:
            rsp = queue.get()
            response = rsp.response
            if response == 'exit':
                break
            elif response == 'connected':
                setup()
            else:
                callback(rsp)
            queue.task_done()
    
    def send_command(self, command, *args, **kwargs):
        """ Send commands to this windows instruments. 
        
        Parameters
        ----------
        command : string
            The name of the function that should be executed.
        args : tuple
            Arguments to be sent to the command function.
        """
        DAQ = self.DAQ
        DAQ.send_command(self.instr, command, *args, **kwargs)
        
    def set_delay_fields(self, channel):
        """ Set the delay fields to the delay for the current channel. 
        
        Parameters
        ----------
        channel : string
            Identifier for the channel, either T0, T1, or A-H.
        """
        delay = self.settings[channel]['delay']
        s = np.floor(delay)
        delay = (delay - s)*1000
        ms = np.floor(delay)
        delay = (delay - ms)*1000
        us = np.floor(delay)
        delay = (delay - us)*1000
        ns = np.floor(delay)
        delay = (delay - ns)*1000
        ps = np.floor(delay)
        self.sField.setValue(s)
        self.msField.setValue(ms)
        self.usField.setValue(us)
        self.nsField.setValue(ns)
        self.psField.setValue(ps)
        
    def set_reference_field(self, channel):
        """ Set the reference field for the passed channel. 
        
        Parameters
        ----------
        channel : string
            Identifier for the channel, either T0, T1, or A-H.
        """
        ref = self.settings[channel]['ref']
        # T1 isn't a reference field so we have to shift the indices
        ind = self.index[ref]
        if ind > 0:
            ind -= 1
        self.referenceField.setCurrentIndex(ind)
        
    def set_output_field(self, channel):
        """ Set the voltage field for the passed channel. 
        
        Parameters
        ----------
        channel : string
            Identifier for the channel, either T0, T1, or A-H.
        """
        output = self.settings[channel]['output']
        self.voltageField.setValue(output)
        
    def set_polarity_field(self, channel):
        """ Set the polarity field for the passed channel. 
        
        Parameters
        ----------
        channel : string
            Identifier for the channel, either T0, T1, or A-H.
        """
        polarity = self.settings[channel]['polarity']
        self.polarityField.setCurrentIndex(polarity)
        
    def set_channel_settings(self, channel):
        """ Set the settings on the delay generator. 
        
        Parameters
        ----------
        channel : string
            Identifier for the channel, either T0, T1, or A-H.
        """
        if not self.updating:
            delay = self.build_delay()
            ref = self.referenceField.currentText()
            output = self.voltageField.value()
            polarity = self.polarityField.currentIndex()
            settings = {
                        'delay' : delay,
                        'output' : output,
                        'ref' : ref,
                        'polarity' : polarity
                        }
            self.settings[channel] = settings
            self.send_command('set_settings', {channel : settings})
    
    def build_delay(self):
        """ Build the delay from the delay combo boxes. 
        
        Returns
        -------
        delay : float
            The delay for the channel.
        """
        s = self.sField.value()
        ms = self.msField.value()
        us = self.usField.value()
        ns = self.nsField.value()
        ps = self.psField.value()
        delay = s + ms*1e-3 + us*1e-6 + ns*1e-9 + ps*1e-12
        return delay
    
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def setup_window(self):
        """ Perform setup after the gauge connects. """
        # Eanble all the buttons and things
        self.channelField.setEnabled(True)
        self.sField.setEnabled(True)
        self.msField.setEnabled(True)
        self.usField.setEnabled(True)
        self.nsField.setEnabled(True)
        self.psField.setEnabled(True)
        self.voltageField.setEnabled(True)
        self.polarityField.setEnabled(True)
        self.referenceField.setEnabled(True)
        self.sourceField.setEnabled(True)
        self.singleCheck.setEnabled(True)
        self.thresholdField.setEnabled(True)
        self.saveButton.setEnabled(True)
        self.recallButton.setEnabled(True)
        self.connected = True
        
        # Get the initial settings
        self.send_command("get_settings")
    
    @pyqtSlot(object)
    def update_fields(self, rsp):
        """ Update the fields with current settings. 
        
        Parameters
        ----------
        rsp : rsp object
            The response object with the field settings
        """
        channel = self.channelField.currentText()
        self.settings = rsp.data
        # Stop the channel change from doing anythin
        self.updating = True
        self.set_delay_fields(channel)
        self.set_reference_field(channel)
        self.set_output_field(channel)
        self.set_polarity_field(channel)
        self.updating = False
    
    @pyqtSlot(int)
    def change_channel(self, ind):
        """ Change the channel displayed in the delay boxes. 
        
        Parameters
        ----------
        ind : int
            The index of the channel.
        """
        channel = self.channelField.currentText()
        self.updating = True
        self.set_delay_fields(channel)
        self.set_reference_field(channel)
        self.set_output_field(channel)
        self.set_polarity_field(channel)
        if channel == 'T1' or channel == 'B' or channel == 'D' or channel == 'F' or channel == 'H':
            self.voltageField.setEnabled(False)
            self.polarityField.setEnabled(False)
        else:
            self.voltageField.setEnabled(True)
            self.polarityField.setEnabled(True)
        self.updating = False
    
    @pyqtSlot(int)
    def change_settings(self, value):
        """ Update on setting changes. """
        channel = self.channelField.currentText()
        self.set_channel_settings(channel)
        
    @pyqtSlot(int)
    def change_trigger(self, ind):
        """ The trigger source changed, updated the SDG. """
        if self.singleCheck.isChecked():
            if ind == 0: ind = 5
            elif ind == 1: ind = 3
            elif ind == 2: ind = 4
        self.send_command('set_trigger_source', ind)
        
    @pyqtSlot(float)
    def change_threshold(self, threshold):
        """ The trigger threshold changed, update the sdg. """
        self.send_command('set_trigger_threshold', threshold)
        
    @pyqtSlot()
    def save_settings(self):
        """ Save the settings internally on the sdg. """
        ind = self.locationField.value()
        self.send_command('save_settings_SDG', ind)
        
    @pyqtSlot()
    def recall_settings(self):
        """ Recall settings internally saved on the sdg. """
        ind = self.locationField.value()
        self.send_command('recall_settings_SDG', ind)
        # Update the GUI with the new settings
        self.send_command("get_settings")

