#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 17:54:53 2019

@author: robert
"""

from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt5.QtGui import (QPixmap, QImage)
from PyQt5.QtWidgets import QLabel
import numpy as np
import threading
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "KA3005P.ui")
Ui_PSWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class PSWindow(QtBaseClass, Ui_PSWindow):
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
        Ui_PSWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.device_connected.connect(self.setup_window)
        self.powerOnButton.clicked.connect(self.turn_on)
        self.powerOffButton.clicked.connect(self.turn_off)
        self.OVPCheck.stateChanged.connect(self.toggle_ovp)
        self.OCPCheck.stateChanged.connect(self.toggle_ocp)
        self.voltageField.valueChanged.connect(self.change_voltage)
        self.currentField.valueChanged.connect(self.change_current)
        
        # Grab references for controlling the power supply
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.updating = False
        
        self.create_update_thread()
        self.setWindowTitle(self.serial)
        
    def create_update_thread(self):
        """ Create a thread to poll the response queue and update the image. """
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
            The signal.emit to call to update the plot. 
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
        
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def setup_window(self):
        """ Perform setup after the gauge connects. """
        self.powerOnButton.setEnabled(True)
        self.powerOffButton.setEnabled(True)
        self.currentField.setEnabled(True)
        self.voltageField.setEnabled(True)
        self.OVPCheck.setEnabled(True)
        self.OCPCheck.setEnabled(True)
        
    @pyqtSlot()
    def turn_on(self):
        """ Turn on the power supply. """
        self.send_command('turn_on')
    
    @pyqtSlot()
    def turn_off(self):
        """ Turn off the power supply. """
        self.send_command('turn_off')
        
    @pyqtSlot(int)
    def toggle_ovp(self, state):
        """ Turn over voltage protection on or off. """
        if state == 2:
            self.send_command('ovp_on')
        else:
            self.send_command('ovp_off')
        
    @pyqtSlot(int)
    def toggle_ocp(self, state):
        """ Turn over current protection on or off. """
        if state == 2:
            self.send_command('ocp_on')
        else:
            self.send_command('ocp_off')
            
    @pyqtSlot(float)
    def change_voltage(self, voltage):
        """ Change the power supply voltage setting. """
        self.send_command('set_voltage', voltage)
    
    @pyqtSlot(float)
    def change_current(self, current):
        """ Change the power supply current setting. """
        self.send_command('set_current', current)
        
    
