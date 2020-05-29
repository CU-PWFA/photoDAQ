#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 08:57:56 2019

@author: keenan
"""



#import numpy as np
import os
from PyQt4 import  QtGui, uic
from PyQt4.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt4.QtGui import (QPixmap, QImage, QLabel)
import threading

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
               "Mirror 9"  : {"slave" : "5>",  "x" : 1, "y" : 2},
               "Mirror 10" : {"slave" : "5>",  "x" : 3, "y" : 4},
               "Mirror 11" : {"slave" : "6>",  "x" : 1, "y" : 2},
               "Mirror 12" : {"slave" : "6>",  "x" : 3, "y" : 4}}


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
        instr : instrInfo object
            Object for a instrument.
        """
        
        QtBaseClass.__init__(self)
        Ui_NFWindow.__init__(parent)
        self.setupUi(self)
        #self.setupUI()
        
        # Add event handlers to all buttons
        self.upButton.clicked.connect(self.move_up)
        self.downButton.clicked.connect(self.move_down)
        self.rightButton.clicked.connect(self.move_right)
        self.leftButton.clicked.connect(self.move_left)
        self.homeButton.clicked.connect(self.move_home)
        self.abortButton.clicked.connect(self.abort_motion)
        self.moveToButton.clicked.connect(self.move_to)
        self.setStepButton.clicked.connect(self.set_step)
        self.setHomeButton.clicked.connect(self.set_home)
        self.setVelocityButton.clicked.connect(self.set_velocity)
        self.setAccelButton.clicked.connect(self.set_acceleration)
        self.data_acquired.connect(self.update_params)
        self.mirrorSelectionCombo.activated.connect(self.update_mirror)
        # Set the driver number
        self.driverSerialText.setText("Driver #" + instr.address)
        # Populate mirror selection combo box
        for key in mirror_list:
            self.mirrorSelectionCombo.addItem(key)
        self.mirrorSelectionCombo.setCurrentIndex(0)    
        
        
        # Make checkboxes exclusive and start with relative motion
        self.absCheckBox.stateChanged.connect(self.abs_clicked)
        self.relCheckBox.stateChanged.connect(self.rel_clicked)
        self.indCheckBox.stateChanged.connect(self.ind_clicked)
        
        # Default motion is absolute
        self.absCheckBox.setCheckState(True)
        # Grab references for controlling driver
        self.DAQ = DAQ
        self.queue = instr.output_queue
        self.instr = instr
        self.updating = False
        
        
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
    
    def abs_clicked(self):
        if self.absCheckBox.checkState():
            self.relCheckBox.setCheckState(False)
            self.indCheckBox.setCheckState(False)
            
    def rel_clicked(self):
        if self.relCheckBox.checkState():
            self.absCheckBox.setCheckState(False)
            self.indCheckBox.setCheckState(False)
            
    def ind_clicked(self):
        if self.indCheckBox.checkState():
            self.relCheckBox.setCheckState(False)
            self.absCheckBox.setCheckState(False)
    
    def check_motion(self):
        if self.absCheckBox.checkState():
            return "abs"
        
        elif self.relCheckBox.checkState():
            return "rel"
        
        elif self.absCheckBox.checkState():
            return "ind"
        
        
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
    def update_mirror(self):
        mirror = self.get_mirror()
        axes   = [mirror["x"], mirror["y"]]
        slave  = mirror["slave"]
        self.send_command(self.instr, "set_slave_axis", axes, slave)
        
    @pyqtSlot(object)
    def update_params(self, rsp):
        self.positionLabel.setText("(" + rsp["x"] + "," + rsp["y"] + ")")
        self.setHomeText.setText("(" + rsp["x_home"] + "," \
                                   + rsp["y_home"] + ")")
        self.setVelocityText.setText(rsp["velocity"])
        self.setAccelerationText.setText(rsp["acceleration"])
    
    @pyqtSlot(str)
    def output(self, text):
        """ Print text to the output box """
        self.outputText.setText(text)
    
    @pyqtSlot()
    def move_up(self):
        print("Move up function")
        
    @pyqtSlot()
    def move_down(self):
        print("Move down function")
    
    @pyqtSlot()
    def move_right(self):
        print("Move right function")
    
    @pyqtSlot()
    def move_left(self):
        print("Move left function")
    
    @pyqtSlot()
    def move_home(self):
        print("Move home function")
    
    @pyqtSlot()
    def abort_motion(self):
        print("Abort motion function")
    
    @pyqtSlot()
    def move_to(self):
        print("Move to function")
    
    @pyqtSlot()
    def set_step(self):
        print("Set step function")
    
    @pyqtSlot()
    def set_home(self):
        print("Set home function")
    
    @pyqtSlot()    
    def set_velocity(self):
        print("Set velocity function")
    
    @pyqtSlot()
    def set_acceleration(self):
        print("Set acceleration function")
        
    