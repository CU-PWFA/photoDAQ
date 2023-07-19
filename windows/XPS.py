#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 11:24:44 2021

@author: jamie

Source module: https://github.com/pyepics/newportxps

"""

from PyQt5 import uic
from PyQt5.QtCore import (pyqtSlot, pyqtSignal)
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
        self.rebootButton.clicked.connect(self.reboot)
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
        self.rebootButton.setEnabled(True)
        self.connected = True
        self.send_command('update_status1')
        self.send_command('update_position1')
        #self.send_command('update_status2')
        #self.send_command('update_position2')
        
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
        self.send_command('update_status2')

    @pyqtSlot()
    def home_group1(self):
        """ Home Group1. """
        self.send_command('homing_status1')
        self.send_command('home_group1')
        self.send_command('update_status1')

    @pyqtSlot()
    def home_group2(self):
        """ Home Group2. """
        self.send_command('homing_status2')
        self.send_command('home_group2')
        self.send_command('update_status2')
    
    @pyqtSlot()
    def reboot(self):
        """Reboot XPS controller"""
        self.send_command('reboot_status')
        self.send_command('reboot')
        self.send_command('update_status1')
        self.send_command('update_status2')

    @pyqtSlot(object)
    def update_text(self, rsp):
        if "pos_readback1" in rsp.info:        
            self.currentPosValue.setText(str(rsp.info['pos_readback1']))
        if "status1" in rsp.info:
            self.status.setText(str(rsp.info['status1']))
        if "pos_readback2" in rsp.info:        
            self.currentPosValue_2.setText(str(rsp.info['pos_readback2']))
        if "status2" in rsp.info:
            self.status_2.setText(str(rsp.info['status2']))
        if "reboot" in rsp.info:
            self.status.setText(str(rsp.info['reboot']))
            self.status_2.setText(str(rsp.info['reboot']))
        if "homing1" in rsp.info:
            self.status.setText(str(rsp.info['homing1']))
        if 'homing2' in rsp.info:
            self.status_2.setText(str(rsp.info['homing2']))
        
    
    @pyqtSlot(float)
    def move_stage1(self):
        """ Move stage 1 to absolute or relative position 'pos' [mm]. """
        current_pos_text = self.currentPosValue.text()
        current_pos = float(current_pos_text)
        req_pos = self.requestPosValue.value()
        upper_bound = self.upperBoundValue_1.value()
        lower_bound = self.lowerBoundValue_1.value()
        if self.absCheckBox.checkState():
            if req_pos <= upper_bound and req_pos >= lower_bound:
                self.send_command('move_stage1_abs', req_pos)
                self.send_command('update_status1')
            else:
                print("Error: Requested position out of range")
        elif self.relCheckBox.checkState():
            sum_pos = current_pos + req_pos
            if sum_pos <= upper_bound and sum_pos > lower_bound:
                self.send_command('move_stage1_rel', req_pos)
                self.send_command('update_status1')
            else:
                print("Error: Requested position out of range")

    @pyqtSlot(float)
    def move_stage2(self):
        """ Move stage 2 to absolute or relative position 'pos' [mm]. """
        current_pos_text = self.currentPosValue_2.text()
        current_pos = float(current_pos_text)
        req_pos = self.requestPosValue_2.value()
        upper_bound = self.upperBoundValue_2.value()
        lower_bound = self.lowerBoundValue_2.value()
        if self.absCheckBox_2.checkState():
            if req_pos <= upper_bound and req_pos >= lower_bound:
                self.send_command('move_stage2_abs', req_pos)
                self.send_command('update_status2')
            else:
                print("Error: Requested position out of range")
        elif self.relCheckBox_2.checkState():
            sum_pos = current_pos + req_pos
            if sum_pos <= upper_bound and sum_pos > lower_bound:
                self.send_command('move_stage2_rel', req_pos)
                self.send_command('update_status2')
            else:
                print("Error: Requested position out of range")


