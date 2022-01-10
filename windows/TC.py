#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 14:51:51 2019

@author: robert
"""

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt4.QtGui import (QPixmap, QImage, QLabel)
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import threading
from scipy.interpolate import interp1d
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "TC.ui")
Ui_TCWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class TCWindow(QtBaseClass, Ui_TCWindow):
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
            The object representing the instrument.
        """
        QtBaseClass.__init__(self)
        Ui_TCWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startButton.clicked.connect(self.start)
        self.stopButton.clicked.connect(self.stop)
        self.resetButton.clicked.connect(self.reset)
        self.data_acquired.connect(self.update_text)
        self.device_connected.connect(self.setup_window)

        self.TriggerModeButton.clicked.connect(self.TriggerMode)
        self.FreeRunButton.clicked.connect(self.FreeRun)
        
        # Grab references for controlling the gauge
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.connected = False
        
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
        """ Perform setup after the controller connects. """
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(True)
        self.resetButton.setEnabled(True)
        self.FreeRunButton.setEnabled(True)
        self.connected = True
        
    @pyqtSlot()
    def start(self):
        """ Start the dataset. """
        self.send_command('start_stream')
        self.send_command('start')
        self.streaming = True
        
    @pyqtSlot()
    def stop(self):
        """ Stop the dataset. """
        self.send_command('stop')
        self.send_command('stop_stream')
        self.streaming = False
        
    @pyqtSlot()
    def reset(self):
        """ Reset the counter. """
        shots = self.shotField.value()
        self.send_command('reset', shots)
        self.currentShot.setText('0')
        
    @pyqtSlot(object)
    def update_text(self, rsp):
        """ Update the text with the shot count. 
        
        Parameters
        ----------
        rsp : rsp object
            The response object with the shot count.
        """
        self.currentShot.setText(str(rsp.info))

    @pyqtSlot()
    def FreeRun(self):
        """ Free Run Trigger """
#        self.send_command('start_stream')
        self.send_command('FreeRun')
        self.FR= True

    @pyqtSlot()
    def TriggerMode(self):
        """ original trigger mode"""
#TODO figure out what to do here
        self.send_command('start_stream')
