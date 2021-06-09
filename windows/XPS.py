#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 11:24:44 2021

@author: jamie

Source module: https://github.com/pyepics/newportxps

"""

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt4.QtGui import (QPixmap, QImage, QLabel)
import numpy as np
import threading
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "XPS.ui")
Ui_XPSWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class XPSWindow(QtBaseClass, Ui_XPSWindow):
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
        instr : instr object
            Object for an instrument.
        """
        
        QtBaseClass.__init__(self)
        Ui_XPSWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.data_acquired.connect(self.update_text)
        self.device_connected.connect(self.setup_window) 
        self.homeButton.clicked.connect(self.home_group1)
        self.homeButton_2.clicked.connect(self.home_group2)
        self.initializeButton.clicked.connect(self.initialize_group1)
        self.initializeButton_2.clicked.connect(self.initialize_group2)
        self.requestPosButton.clicked.connect(self.move_stage1)  
        self.requestPosButton_2.clicked.connect(self.move_stage2)     
        # Make checkboxes exclusive and make absolute motion the default
        self.absCheckBox.stateChanged.connect(self.abs_clicked)
        self.relCheckBox.stateChanged.connect(self.rel_clicked)
        self.absCheckBox.setCheckState(True)
        self.absCheckBox_2.stateChanged.connect(self.abs_clicked)
        self.relCheckBox_2.stateChanged.connect(self.rel_clicked)
        self.absCheckBox_2.setCheckState(True)
       
        # Grab references for controlling the XPS controller
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.updating = False
        self.connected = False

        self.create_update_thread()
    
    def create_update_thread(self):
        """ Create a thread to poll the response queue and update the fields. """
        args = (self.queue, self.data_acquired.emit, self.device_connected.emit)
        thread = threading.Thread(target=self.update_thread, args=args)
        thread.setDaemon(True)
        thread.start()
        
    def update_thread(self, queue, update, setup):
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
            elif response == 'driver':
                update(rsp)
            queue.task_done()  

    # Make check boxes exclusive
    def abs_clicked(self):
        if self.absCheckBox.checkState():
            self.relCheckBox.setCheckState(False)
        if self.absCheckBox_2.checkState():
            self.relCheckBox_2.setCheckState(False)

    def rel_clicked(self):
        if self.relCheckBox.checkState():
            self.absCheckBox.setCheckState(False)
        if self.relCheckBox_2.checkState():
            self.absCheckBox_2.setCheckState(False)

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
        """ Perform setup after the controller connects. """
        # Eanble all the buttons and things
        self.initializeButton.setEnabled(True)
        self.homeButton.setEnabled(True)
        self.requestPosValue.setEnabled(True)
        self.initializeButton_2.setEnabled(True)
        self.homeButton_2.setEnabled(True)
        self.requestPosValue_2.setEnabled(True)
        self.connected = True
        self.send_command('update_status1')
        self.send_command('update_position1')
        
        # Get the initial settings
        self.send_command("get_settings")

    @pyqtSlot()
    def initialize_group1(self):
        """ Initialize Group1. """
        self.send_command('initialize_group1')
        self.send_command('update_status1')

    @pyqtSlot()
    def initialize_group2(self):
        """ Initialize Group2. """
        self.send_command('initialize_group2')

    @pyqtSlot()
    def home_group1(self):
        """ Home Group1. """
        self.send_command('home_group1')
        self.send_command('update_status1')

    @pyqtSlot()
    def home_group2(self):
        """ Home Group2. """
        self.send_command('home_group2')

    @pyqtSlot(object)
    def update_text(self, rsp):
        if "pos_readback" in rsp.info:        
            self.currentPosValue.setText(str(rsp.info['pos_readback']))
        if "status" in rsp.info:
            self.status.setText(str(rsp.info['status']))
    
    @pyqtSlot(float)
    def move_stage1(self):
        """ Move stage 1 to absolute or relative position 'pos' [mm]. """
        pos = self.requestPosValue.value()
        if self.absCheckBox.checkState():
            self.send_command('move_stage1_abs', pos)
            self.send_command('update_status1')
        elif self.relCheckBox.checkState():
            self.send_command('move_stage1_rel', pos)
            self.send_command('update_status1')

    @pyqtSlot(float)
    def move_stage2(self):
        """ Move stage 2 to absolute or relative position 'pos' [mm]. """
        pos = self.requestPosValue_2.value()
        if self.absCheckBox_2.checkState():
            self.send_command('move_stage2_abs', pos)
            self.send_command('update_status2')
        elif self.relCheckBox_2.checkState():
            self.send_command('move_stage2_rel', pos)
            self.send_command('update_status2')
    


