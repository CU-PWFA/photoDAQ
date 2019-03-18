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
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "FRG700.ui")
Ui_GaugeWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class GaugeWindow(QtBaseClass, Ui_GaugeWindow):
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
        Ui_GaugeWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startStreamButton.clicked.connect(self.start_stream)
        self.stopStreamButton.clicked.connect(self.stop_stream)
        self.data_acquired.connect(self.update_canvas)
        self.device_connected.connect(self.setup_window)
        self.lengthField.valueChanged.connect(self.change_buffer)
        self.sampleField.valueChanged.connect(self.change_delay)
        self.gaugeCheck_0.stateChanged.connect(self.toggle_plot)
        self.gaugeCheck_1.stateChanged.connect(self.toggle_plot)
        self.gaugeCheck_2.stateChanged.connect(self.toggle_plot)
        self.gaugeCheck_3.stateChanged.connect(self.toggle_plot)
        
        # Grab references for controlling the spectrometer
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        
        # Large bacause it is a double array buffer
        self.bufferSize = self.lengthField.value()
        self.pressure = np.zeros((4, 2*self.bufferSize))
        self.i = 0
        
        # Create the container for the image
        self.load_adjustments()
        self.create_image()
        self.create_update_thread()
        self.setWindowTitle(self.serial)
        
    def create_image(self):
        """ Create the matplotlib canvas. """
        self.fig = fig = Figure()
        self.pr_ax = ax = fig.add_subplot(111)
        ax.set_yscale('log')
        ax.set_autoscale_on(False)
        ax.set_xbound(0, 1000)
        ax.set_ybound(1e-6, 5000)
        ax.set_ylabel('Pressure (mbar)')
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        fig.tight_layout()
        data = self.prep_data()
        self.pr_plot0, = ax.plot(data[0])
        self.pr_plot1, = ax.plot(data[1])
        self.pr_plot2, = ax.plot(data[2])
        self.pr_plot3, = ax.plot(data[3])
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
        
    def update_plot(self, pressure):
        """ Handle matplotlib updating. 
        
        Parmaeters
        ----------
        pressure : double
            The most recent pressure measurement.
        """
        data = self.prep_data()
        self.pr_plot0.set_ydata(data[0])
        self.pr_plot1.set_ydata(data[1])
        self.pr_plot2.set_ydata(data[2])
        self.pr_plot3.set_ydata(data[3])
        ind = self.gaugeDisplayField.currentIndex()
        self.pr_display.set_text('%.2E mbar' % self.prep_data(pressure[ind]))
        
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
        buffer[:, i] = buffer[:, i+size] = pressure
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
            data = self.pressure[:, i:i+self.bufferSize]
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
    def setup_window(self):
        """ Perform setup after the gauge connects. """
        self.startStreamButton.setEnabled(True)
        self.stopStreamButton.setEnabled(True)
        self.lengthField.setEnabled(True)
        self.speciesField.setEnabled(True)
        self.sampleField.setEnabled(True)
        
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
        self.update_buffer(rsp.data)
        self.update_plot(rsp.data)
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
        newBuffer = np.zeros((4, 2*length))
        i = self.i
        if length >= oldLength:
            newBuffer[:, length-oldLength:length] = self.pressure[:, i:i+oldLength]
        else:
            newBuffer[:, :length] = self.pressure[:, i+oldLength-length:i+oldLength]
        self.pressure = newBuffer
        self.bufferSize = length
        self.i = 0
        # We also need to update the plot 
        self.update_plot(self.pressure[:, length])
        self.pr_plot0.set_xdata(range(length))
        self.pr_plot1.set_xdata(range(length))
        self.pr_plot2.set_xdata(range(length))
        self.pr_plot3.set_xdata(range(length))
        self.pr_ax.set_xbound(0, length)
    
    @pyqtSlot(int)
    def change_delay(self, delay):
        """ Change the sampling delay.
        
        Parameters
        ----------
        delay : int
            The sampling delay in ms. 
        """
        self.send_command('set_sample_delay', delay)
        
    @pyqtSlot(int)
    def toggle_plot(self, check):
        """ Set the plots visible or invisible based on the current check boxs.
        
        Parameters
        ----------
        check : int
            The value of the checkbox that was checked. 
        """
        # Gauge 0
        if self.gaugeCheck_0.isChecked():
            self.pr_plot0.set_visible(True)
        else:
            self.pr_plot0.set_visible(False)
        # Gauge 1
        if self.gaugeCheck_1.isChecked():
            self.pr_plot1.set_visible(True)
        else:
            self.pr_plot1.set_visible(False)
        # Gauge 2
        if self.gaugeCheck_2.isChecked():
            self.pr_plot2.set_visible(True)
        else:
            self.pr_plot2.set_visible(False)
        # Gauge 3
        if self.gaugeCheck_3.isChecked():
            self.pr_plot3.set_visible(True)
        else:
            self.pr_plot3.set_visible(False)

