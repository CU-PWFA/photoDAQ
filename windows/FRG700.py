#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 16 12:04:04 2019

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

qtCreatorFile = "windows/FRG700.ui"
Ui_GaugeWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class GaugeWindow(QtBaseClass, Ui_GaugeWindow):
    data_acquired = pyqtSignal(dict)
    
    def __init__(self, parent, DAQ, serial, queue):
        """ Create the parent class and add event handlers. 
        
        Parameters
        ----------
        parent : QtClass
            The parent window that creates this window.
        DAQ : DAQ class
            The class representing the DAQ.
        serial : string or int
            The serial number or string of the device the window is for.
        queue : queue
            Queue with output from the DAQ.
        """
        QtBaseClass.__init__(self)
        Ui_GaugeWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startStreamButton.clicked.connect(self.start_stream)
        self.stopStreamButton.clicked.connect(self.stop_stream)
        self.data_acquired.connect(self.update_canvas)
        self.lengthField.valueChanged.connect(self.change_buffer)
        self.sampleField.valueChanged.connect(self.change_delay)
        
        # Grab references for controlling the spectrometer
        self.DAQ = DAQ
        self.serial = serial
        self.queue = queue
        
        # Large bacause it is a double array buffer
        self.bufferSize = self.lengthField.value()
        self.pressure = np.zeros(2*self.bufferSize)
        self.i = 0
        
        # Create the container for the image
        self.load_adjustments()
        self.create_image()
        self.create_update_thread()
        self.setWindowTitle(str(serial))
        
    def create_image(self):
        """ Create the matplotlib canvas. """
        self.fig = fig = Figure()
        self.pr_ax = ax = fig.add_subplot(111)
        ax.set_yscale('log')
        ax.set_autoscale_on(False)
        ax.set_xbound(0, 1000)
        ax.set_ybound(1e-6, 1000)
        ax.set_ylabel('Pressure (mbar)')
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        fig.tight_layout()
        data = self.prep_data()
        self.pr_plot, = ax.plot(data)
        self.pr_display = ax.text(0.3, 0.8, '%.2E mbar' % 0.0,
                                  transform=ax.transAxes, fontsize=42)
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
        args = (self.queue, self.data_acquired.emit)
        thread = threading.Thread(target=self.update_thread, args=args)
        thread.setDaemon(True)
        thread.start()
        
    def update_thread(self, queue, callback):
        """ Wait for updated data to display. 
        
        Parameters
        ----------
        queue : queue
            The queue that the data is arriving on.
        callback : func
            The signal.emit to call to update the plot. 
        """
        while True:
            data = queue.get()
            if data == '__exit__':
                break
            elif data == '__Connected__':
                self.setup_window()
            else:
                callback(data)
            queue.task_done()
            
    def setup_window(self):
        """ Perform setup after the gauge connects. """
        self.startStreamButton.setEnabled(True)
        self.stopStreamButton.setEnabled(True)
        self.lengthField.setEnabled(True)
        self.speciesField.setEnabled(True)
        self.sampleField.setEnabled(True)
    
    def send_command(self, command, args=None, kwargs=None):
        """ Send commands to this windows instruments. 
        
        Parameters
        ----------
        command : string
            The name of the function that should be executed.
        args : tuple
            Arguments to be sent to the command function.
        """
        DAQ = self.DAQ
        DAQ.send_command(DAQ.command_queue[self.serial], command, args)
        
    def update_plot(self, pressure):
        """ Handle matplotlib updating. 
        
        Parmaeters
        ----------
        pressure : double
            The most recent pressure measurement.
        """
        data = self.prep_data()
        self.pr_plot.set_ydata(data)
        self.pr_display.set_text('%.2E mbar' % self.prep_data(pressure))
        
    def update_buffer(self, pressure):
        """ Update the rolling buffer. 
        
        Parameters
        ----------
        pressure : double
            The pressure to add to the buffer. 
        """
        buffer = self.pressure
        size = self.bufferSize
        i = self.i
        buffer[i] = buffer[i+size] = pressure
        self.i = (i+1)%size
        
    def prep_data(self, data=None):
        """ Prepare the pressure data for plotting. 
        
        Parameters
        ----------
        data : double, optional
            If pressure data is passed it will be converted for the current gas.
        
        Returns
        -------
        data : array-like
            The pressure data for plotting.
        """
        i = self.i
        if data is None:
            data = self.pressure[i:i+self.bufferSize]
        species = self.speciesField.currentText()
        if species == 'Ar':
            data = self.Ar(data)
        if species == 'He':
            data = self.He(data)
        return data
    
    def load_adjustments(self):
        """ Load in the CSV data for adjusting the curves for different gases. """
        Ar = np.genfromtxt("adjustments/Ar.csv", delimiter=',')
        He = np.genfromtxt("adjustments/He.csv", delimiter=',')
        self.Ar = interp1d(Ar[:, 1], Ar[:, 0], fill_value='extrapolate')
        self.He = interp1d(He[:, 1], He[:, 0], fill_value='extrapolate')
        
    # Event Handlers
    ###########################################################################
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
        
    @pyqtSlot(dict)
    def update_canvas(self, data):
        """ Update the canvas with the new image. 
        
        Parameters
        ----------
        data : dict
            The dictionary with the image data and meta.
        """
        self.update_buffer(data['pressure'])
        self.update_plot(data['pressure'])
        self.canvas.draw()
        
    @pyqtSlot(int)
    def change_buffer(self, length):
        """ Change the length of the buffer.
        
        Parameters
        ----------
        length : int
            The new length of the buffer. 
        """
        oldLength = self.bufferSize
        newBuffer = np.zeros(2*length)
        i = self.i
        if length >= oldLength:
            newBuffer[length-oldLength:length] = self.pressure[i:i+oldLength]
        else:
            newBuffer[:length] = self.pressure[i+oldLength-length:i+oldLength]
        self.pressure = newBuffer
        self.bufferSize = length
        self.i = 0
        # We also need to update the plot 
        self.update_plot(self.pressure[length])
        self.pr_plot.set_xdata(range(length))
        self.pr_ax.set_xbound(0, length)
    
    @pyqtSlot(int)
    def change_delay(self, delay):
        """ Change the sampling delay.
        
        Parameters
        ----------
        delay : int
            The sampling delay in ms. 
        """
        self.send_command('set_sample_delay', (delay,))

