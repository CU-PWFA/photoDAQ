#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 08:57:56 2019

@author: keenan & jamie
"""

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt4.QtGui import (QPixmap, QImage, QLabel)
import numpy as np
import threading
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "NF8742.ui")
Ui_NFWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


# Controllable mirrors and their slave/axis numbers
mirror_list = {"Mirror 1"  : {"slave" : "1>",  "x" : 1, "y" : 2}, 
               "Mirror 2"  : {"slave" : "1>",  "x" : 3, "y" : 4},
               "Mirror 3"  : {"slave" : "2>",  "x" : 1, "y" : 2},
               "Mirror 4"  : {"slave" : "2>",  "x" : 3, "y" : 4},
               "Mirror 5"  : {"slave" : "3>",  "x" : 1, "y" : 2},
               "Mirror 6"  : {"slave" : "3>",  "x" : 3, "y" : 4},
               "Mirror 7"  : {"slave" : "4>",  "x" : 1, "y" : 2},
               "Mirror 8"  : {"slave" : "4>",  "x" : 3, "y" : 4},
               "Mirror 9"  : {"slave" : "5>",  "x" : 1, "y" : 2}}
#               "Mirror 10" : {"slave" : "5>",  "x" : 3, "y" : 4},
#               "Mirror 11" : {"slave" : "6>",  "x" : 1, "y" : 2},
#               "Mirror 12" : {"slave" : "6>",  "x" : 3, "y" : 4}}


class NF8742Window(QtBaseClass, Ui_NFWindow):
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
        Ui_NFWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all buttons
        self.data_acquired.connect(self.update_params)
        self.device_connected.connect(self.update_mirror)
        self.device_connected.connect(self.setup_window) 
        self.abortButton.clicked.connect(self.abort_motion)
        self.moveToXButton.clicked.connect(self.move_abs_rel_x)
        self.moveToYButton.clicked.connect(self.move_abs_rel_y)
        self.upButton.clicked.connect(self.move_ind_up)
        self.downButton.clicked.connect(self.move_ind_down)
        self.leftButton.clicked.connect(self.move_ind_left)
        self.rightButton.clicked.connect(self.move_ind_right)
        self.homeXButton.clicked.connect(self.go_home_x)
        self.homeYButton.clicked.connect(self.go_home_y)
        self.setVelocityButton.clicked.connect(self.set_velocity)
        self.setAccelButton.clicked.connect(self.set_acceleration)
        self.getPositionButton.clicked.connect(self.update_position)
        self.getErrorButton.clicked.connect(self.get_error)
        
        # Set the driver number
        self.driverSerialText.setText("Driver #" + instr.address)
        self.mirrorSelectionCombo.activated.connect(self.update_mirror)
        self.mirrorSelectionCombo.activated.connect(self.update_position)
        # Populate mirror selection combo box
        for key in mirror_list:
            self.mirrorSelectionCombo.addItem(key)
        self.mirrorSelectionCombo.setCurrentIndex(0)    
        
        
        # Make checkboxes exclusive 
        self.absCheckBox.stateChanged.connect(self.abs_clicked)
        self.relCheckBox.stateChanged.connect(self.rel_clicked)
        
        # Default motion is absolute
        self.absCheckBox.setCheckState(True)
        # Grab references for controlling driver
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.updating = False
        self.connected = False        
        
        self.create_update_thread()

# -------------  Extra buttons not currently on device panel ----------------
        self.scanButton.clicked.connect(self.start_scan)
        self.scanStatusButton.clicked.connect(self.scan_status)
        self.listButton.clicked.connect(self.list_controllers)
        self.addressButton.clicked.connect(self.query_address)
#        self.getConfigButton.clicked.connect(self.get_config)
        self.motorCheckButton.clicked.connect(self.motor_check)
#        self.motorTypeButton.clicked.connect(self.motor_type)
#        self.setConfigButton.clicked.connect(self.set_config)
#        self.setHomeXButton.clicked.connect(self.set_home_x)
#        self.setHomeYButton.clicked.connect(self.set_home_y)
#        self.resetButton.clicked.connect(self.reset)
# ---------------------------------------------------------------------------
    
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
    
    #Make check boxes exclusive
    def abs_clicked(self):
        if self.absCheckBox.checkState():
            self.relCheckBox.setCheckState(False)
            
    def rel_clicked(self):
        if self.relCheckBox.checkState():
            self.absCheckBox.setCheckState(False)
    
    def check_motion(self):
        if self.absCheckBox.checkState():
            return "abs"
        elif self.relCheckBox.checkState():
            return "rel"
        
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

    def get_mirror(self):
        """ Gets the currently selected mirror to control
        Returns:
        --------
        mirror_params : tuple
            The tuple corresponding to the selected mirror in mirror_list
        """
        return mirror_list[self.mirrorSelectionCombo.currentText()]

    @pyqtSlot()
    def setup_window(self):
        """ Perform setup after the controller connects. """
        # Eanble all the buttons and things
        self.abortButton.setEnabled(True)
        self.moveToXButton.setEnabled(True)
        self.moveToYButton.setEnabled(True)
        self.getPositionButton.setEnabled(True)
        self.setVelocityButton.setEnabled(True)
        self.setAccelButton.setEnabled(True)
        self.upButton.setEnabled(True)
        self.downButton.setEnabled(True)
        self.rightButton.setEnabled(True)
        self.leftButton.setEnabled(True)
        self.getErrorButton.setEnabled(True)
        self.send_command('update_position')
        self.send_command('update_vel')
        self.send_command('update_accel')

    # ----- Extra buttons ---------------------
        self.scanButton.setEnabled(True)
        self.listButton.setEnabled(True)
        self.scanStatusButton.setEnabled(True)
        self.addressButton.setEnabled(True)
#        self.getConfigButton.setEnabled(True)
        self.motorCheckButton.setEnabled(True)
#        self.motorTypeButton.setEnabled(True)
#        self.setConfigButton.setEnabled(True)
#        self.setHomeXButton.setEnabled(True)
#        self.setHomeYButton.setEnabled(True)

    
    @pyqtSlot()
    def update_mirror(self):
        mirror = self.get_mirror()
        axes   = [mirror["x"], mirror["y"]]
        slave  = mirror["slave"]
        self.send_command("set_slave_axis", axes, slave)
        
    @pyqtSlot(object)
    def update_params(self, rsp):
        if "x_pos_readback" and "y_pos_readback" in rsp.info:  
            self.currentPosValue.setText("(" + str(rsp.info['x_pos_readback']) +","+ str(rsp.info['y_pos_readback'])+')')
        if "velocity_readback" in rsp.info:
            self.currentVelocityValue.setText(str(rsp.info['velocity_readback']))
        if "acceleration_readback" in rsp.info:
            self.currentAccelValue.setText(str(rsp.info['acceleration_readback']))
    
    @pyqtSlot()
    def move_abs_rel_x(self):
        """ Absolute or relative motion in horizontal direction"""
        x_pos_text = self.moveToXText.toPlainText()
        x_pos = int(x_pos_text)
        if self.absCheckBox.checkState():
            self.send_command('move_abs_x', x_pos)
        elif self.relCheckBox.checkState():
            self.send_command('move_rel_x', x_pos)

    @pyqtSlot()
    def move_abs_rel_y(self):
        """ Absolute or relative motion in vertical direction"""
        y_pos_text = self.moveToYText.toPlainText()
        y_pos = int(y_pos_text)
        if self.absCheckBox.checkState():
            self.send_command('move_abs_y', y_pos)
        elif self.relCheckBox.checkState():
            self.send_command('move_rel_x', y_pos)

    @pyqtSlot()
    def move_ind_up(self):
        """ Move indefinitely in positive vertical direction """
        direction = "+"
        self.send_command('move_indef_vert', direction)

    @pyqtSlot()
    def move_ind_down(self):
        """ Move indefinitely in negative vertical direction """
        direction = "-"
        self.send_command('move_indef_vert', direction)

    @pyqtSlot()
    def move_ind_left(self):
        """ Move indefinitely in negative horizontal direction """
        direction = "-"
        self.send_command('move_indef_horiz', direction)

    @pyqtSlot()
    def move_ind_right(self):
        """ Move indefinitely in positive horizontal direction """
        direction = "+"
        self.send_command('move_indef_horiz', direction)

    @pyqtSlot()
    def go_home_x(self):
        self.send_command('move_abs_x', 0)
    
    @pyqtSlot()
    def go_home_y(self):
        self.send_command('move_abs_y', 0)
    
    @pyqtSlot()    
    def set_velocity(self):
        vel_text = self.setVelocityText.toPlainText()
        velocity = int(vel_text)
        self.send_command('set_vel', velocity)
    
    @pyqtSlot()
    def set_acceleration(self):
        accel_text = self.setAccelText.toPlainText()
        accel = int(accel_text)
        self.send_command('set_accel', accel)
 
    @pyqtSlot()
    def abort_motion(self):
        self.send_command('abort_motion')
        
    @pyqtSlot()
    def update_position(self):
        self.send_command('update_position')

    @pyqtSlot()
    def get_error(self):
        self.send_command('get_error')

# ---------- Extra functions not currently being used -------------------------
#------------------------------------------------------------------------------

    @pyqtSlot()
    def start_scan(self):
        self.send_command('start_scan')
    
    @pyqtSlot()
    def list_controllers(self):
        self.send_command('list_controllers')
    
    @pyqtSlot()
    def scan_status(self):
        self.send_command('scan_status')

    @pyqtSlot()
    def query_address(self):
        self.send_command('query_address')

    @pyqtSlot()
    def get_config(self):
        self.send_command('get_config')

    @pyqtSlot()
    def motor_check(self):
        self.send_command('motor_check')

    @pyqtSlot()
    def motor_type(self):
        self.send_command('motor_type')

    @pyqtSlot()
    def set_config(self):
        self.send_command('set_config')

    @pyqtSlot()
    def reset(self):
        self.send_command('reset')

    @pyqtSlot()
    def set_home_x(self):
        x_home_text = self.setHomeXText.toPlainText()
        x_home = int(x_home_text)
        self.send_command('set_home_x', x_home)

    @pyqtSlot()
    def set_home_y(self):
        y_home_text = self.setHomeYText.toPlainText()
        y_home = int(y_home_text)
        self.send_command('set_home_y', y_home)

# -----------------------------------------------------------------------------