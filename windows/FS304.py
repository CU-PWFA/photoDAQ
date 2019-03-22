#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 18:00:55 2019

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
from time import sleep

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "FS304.ui")
Ui_PumpWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class PumpWindow(QtBaseClass, Ui_PumpWindow):
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
        Ui_PumpWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startStreamButton.clicked.connect(self.start_stream)
        self.stopStreamButton.clicked.connect(self.stop_stream)
        self.data_acquired.connect(self.update_canvas)
        self.device_connected.connect(self.setup_window)
        self.lengthField.valueChanged.connect(self.change_buffer)
        self.sampleField.valueChanged.connect(self.change_delay)
        self.startTurboButton.clicked.connect(self.start_turbo)
        self.stopTurboButton.clicked.connect(self.stop_turbo)
        
        # Grab references for controlling the spectrometer
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.connected = False
        
        # Large bacause it is a double array buffer
        self.bufferSize = self.lengthField.value()
        self.status = np.zeros((3, 2*self.bufferSize))
        self.i = 0
        
        # Create the container for the image
        self.create_image()
        self.create_update_thread()
        self.setWindowTitle(self.serial)
        
    def create_image(self):
        """ Create the matplotlib canvas. """
        self.fig = fig = Figure()
        self.pr_ax = ax = fig.add_subplot(111)
        ax.set_autoscale_on(False)
        ax.set_xbound(0, 1000)
        ax.set_ybound(0, 155)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        fig.tight_layout()
        data = self.prep_data()
        self.pr_plot0, = ax.plot(data[0])
        self.pr_plot1, = ax.plot(data[1])
        ax.legend(['Power (W)', 'Temperature (C)'], loc=2)
        self.pr_ax1 = ax1 = ax.twinx()
        ax1.set_autoscale_on(False)
        ax1.set_ybound(0, 1200)
        ax1.set_ylabel('Drive frequency (Hz)')
        ax1.spines['top'].set_visible(False)
        self.pr_plot2, = ax1.plot(data[2], 'g')
        #self.pr_ax = plt.Axes(fig, rect=[0, 0, 1, 1])
        #fig.add_axes(self.pr_ax)
        
        # The mplvl is a named layout on the imageWidget
        self.canvas = canvas = FigureCanvas(fig)
        self.mplvl.addWidget(canvas)
        canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, self.imageWidget,
                                         coordinates=True)
        self.mplvl.addWidget(self.toolbar)
        
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
        
    def update_plot(self):
        """ Handle matplotlib updating. """
        data = self.prep_data()
        self.pr_plot0.set_ydata(data[0])
        self.pr_plot1.set_ydata(data[1])
        self.pr_plot2.set_ydata(data[2])
        
    def update_buffer(self, status):
        """ Update the rolling buffer. 
        
        Parameters
        ----------
        status : double
            The array of power, temperature and speed to add to the buffer. 
        """
        buffer = self.status
        size = self.bufferSize
        i = self.i
        buffer[:, i] = buffer[:, i+size] = status
        self.i = (i+1)%size
        
    def prep_data(self):
        """ Prepare the pump status for plotting. 
        
        Returns
        -------
        data : array-like
            The pump parameters ready for plotting.
        """
        i = self.i
        data = self.status[:, i:i+self.bufferSize]
        return data
    
    def update_status(self, data):
        """ Update the status and error text. 
        
        Parmaeters
        ----------
        data : dict
            The data dictionary from the device response queue.
        """
        self.statusDisplay.setText(data['status'])
        self.errorDisplay.setText(data['error'])
        
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def setup_window(self):
        """ Perform setup after the gauge connects. """
        self.startStreamButton.setEnabled(True)
        self.stopStreamButton.setEnabled(True)
        self.lengthField.setEnabled(True)
        self.sampleField.setEnabled(True)
        self.startTurboButton.setEnabled(True)
        self.stopTurboButton.setEnabled(True)
        self.connected = True
    
    @pyqtSlot()
    def start_stream(self):
        """ Start the camera stream and display it. """
        self.send_command('start_stream')   
        self.streaming = True   
        
    @pyqtSlot()
    def stop_stream(self):
        """ Stop the camera stream and the display. """
        self.send_command('stop_stream')
        self.streaming = False
        
    @pyqtSlot(object)
    def update_canvas(self, rsp):
        """ Update the canvas with the new image. 
        
        Parameters
        ----------
        rsp : rsp object
            The response object with the field settings
        """
        status = [rsp.data['power'], rsp.data['temperature'], rsp.data['frequency']]
        self.update_buffer(status)
        self.update_plot()
        self.canvas.draw()
        self.update_status(rsp.data)
        
    @pyqtSlot(int)
    def change_buffer(self, length):
        """ Change the length of the buffer.
        
        Parameters
        ----------
        length : int
            The new length of the buffer. 
        """
        oldLength = self.bufferSize
        newBuffer = np.zeros((3, 2*length))
        i = self.i
        if length >= oldLength:
            newBuffer[:, length-oldLength:length] = self.status[:, i:i+oldLength]
        else:
            newBuffer[:, :length] = self.status[:, i+oldLength-length:i+oldLength]
        self.status = newBuffer
        self.bufferSize = length
        self.i = 0
        # We also need to update the plot 
        #self.update_plot(self.status[:, length])
        self.pr_plot0.set_xdata(range(length))
        self.pr_plot1.set_xdata(range(length))
        self.pr_plot2.set_xdata(range(length))
        self.pr_ax.set_xbound(0, length)
        self.pr_ax1.set_xbound(0, length)
    
    @pyqtSlot(int)
    def change_delay(self, delay):
        """ Change the sampling delay.
        
        Parameters
        ----------
        delay : int
            The sampling delay in ms. 
        """
        self.send_command('set_sample_delay', delay)
        
    @pyqtSlot()
    def start_turbo(self):
        """ Start the turbo pump. """
        self.stop_stream()
        sleep(0.5)
        self.send_command('turn_on')
        sleep(0.5)
        self.start_stream()
        
    @pyqtSlot()
    def stop_turbo(self):
        """ Stop the turbo pump. """
        self.stop_stream()
        sleep(0.5)
        self.send_command('turn_off')
        sleep(0.5)
        self.start_stream()