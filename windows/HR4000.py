#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  9 17:03:50 2019

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
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "HR4000.ui")
Ui_SpecWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class SpecWindow(QtBaseClass, Ui_SpecWindow):
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
        Ui_SpecWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startStreamButton.clicked.connect(self.start_stream)
        self.stopStreamButton.clicked.connect(self.stop_stream)
        self.data_acquired.connect(self.update_canvas)
        self.intField.valueChanged.connect(self.set_integration)
        self.takeBackButton.clicked.connect(self.take_background)
        self.showBackButton.clicked.connect(self.show_background)
        self.startIntButton.clicked.connect(self.start_integration)
        self.stopIntButton.clicked.connect(self.stop_integration)
        self.showIntButton.clicked.connect(self.show_integration)
        self.triggerCheck.stateChanged.connect(self.set_trigger)
        self.device_connected.connect(self.setup_window)
        
        # Grab references for controlling the spectrometer
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr

        # Create the container for the image
        self.create_image()
        self.create_update_thread()
        self.setWindowTitle(self.serial)
        self.initial_update = True
        
        # Setup everything for taking backgrounds
        self.reset_background()
        self.streaming = False # Track if currently streaming
        self.taking_background = False # track if currently taking a background
        self.background_shot = 0
        
        # Setup everything for integration post processing
        self.reset_integration()
        self.integrating = False
        self.integration_shot = 0
        
    def create_image(self):
        """ Create the matplotlib canvas. """
        self.fig = fig = Figure()
        self.sp_ax = fig.add_subplot(111)
        #self.sp_ax = plt.Axes(fig, rect=[0, 0, 1, 1])
        #fig.add_axes(self.sp_ax, xlabel = 'Wavelength', ylabel = 'Intensity')
        fig.add_subplot(self.sp_ax)
        
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
        
    def create_plot(self, l, I):
        """ Handle all the matplotlib that goes into the plot.

        Parameters
        ----------
        l : array-like
            Wavelength array.
        I : array-like
            Intensity array.
        """  
        ax = self.sp_ax
        self.spec_plot, = ax.plot(l, I)
        ax.set_axis_on()
        ax.set_ybound(-1000, 16384)
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Intensity (shots)')
        # Show the major grid lines with dark grey lines
        ax.grid(b=True, which='major', color='#666666', linestyle='-')
        # Show the minor grid lines with very faint and almost transparent grey lines
        ax.minorticks_on()
        ax.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
        
    def add_background_shot(self, I):
        """ Add a single shot to the background. 
        
        Parameters
        ----------
        I : array-like
            Intensity array to add.
        """
        self.background += I
        self.background_shot += 1
        self.backProgress.setValue(self.background_shot)
        if self.background_shot == self.backShotField.value():
            self.taking_background = False
            self.enable_interaction()
            
    def reset_background(self):
        """ Reset the background to zeros. """
        self.background = np.zeros(3648)
        
    def add_integration_shot(self, I):
        """ Add a shot to the integration.
        
        Parmaeters
        ----------
        I : array-like
            Spectrum intensities from one shot.
            
        Returns
        -------
        I : array-like
            Integrated signal.
        """
        self.integration += I
        self.integration_shot += 1
        self.intProgress.setValue(self.integration_shot)
        I = self.get_integration_data()
        if self.integration_shot == self.intShotField.value():
            self.reset_integration()
            self.integration_shot = 0
        return I
    
    def get_integration_data(self):
        """ get the integration data for plotting. 
        
        Returns
        -------
        I : array-like
            Integration data including averaging.
        """
        if self.background_shot != 0:
            if self.avgCheck.isChecked():
                I = self.integration/self.integration_shot - self.background/self.background_shot
            else:
                I = self.integration - self.background * self.integration_shot/self.background_shot
        else: 
            if self.avgCheck.isChecked():
                I = self.integration/self.integration_shot
            else:
                I = self.integration
        return I
    
    def reset_integration(self):
        """ Reset the integrated signal to zero. """
        self.integration = np.zeros(3648)
        
    def disable_interaction(self):
        """ Disable all the interaction buttons. """
        self.backShotField.setEnabled(False)
        self.takeBackButton.setEnabled(False)
        self.startIntButton.setEnabled(False)
        self.intShotField.setEnabled(False)
        
    def enable_interaction(self):
        """ Enable all the interaction buttons. """
        self.backShotField.setEnabled(True)
        self.takeBackButton.setEnabled(True)
        self.startIntButton.setEnabled(True)
        self.intShotField.setEnabled(True)
        
    def enable_show_buttons(self):
        """ Enable the show buttons. """
        self.showBackButton.setEnabled(True)
        self.showIntButton.setEnabled(True)
        
    def disable_show_buttons(self):
        """ Disable the show buttons. """
        self.showBackButton.setEnabled(False)
        self.showIntButton.setEnabled(False)
        
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def setup_window(self):
        """ Perform setup after the spectrometer connects. """
        self.startStreamButton.setEnabled(True)
        self.stopStreamButton.setEnabled(True)
        self.intField.setEnabled(True)
        self.backShotField.setEnabled(True)
        self.takeBackButton.setEnabled(True)
        self.startIntButton.setEnabled(True)
        self.stopIntButton.setEnabled(True)
        self.intShotField.setEnabled(True)
    
    @pyqtSlot()
    def start_stream(self):
        """ Start the camera stream and display it. """
        self.send_command('start_stream')   
        self.streaming = True   
        self.disable_show_buttons()
        
    @pyqtSlot()
    def stop_stream(self):
        """ Stop the camera stream and the display. """
        self.send_command('stop_stream')
        self.streaming = False
        self.enable_show_buttons()
        
    @pyqtSlot(float)
    def set_integration(self, value):
        """ Set the integration time. """
        self.send_command('set_integration_time', value*1000.)
    
    @pyqtSlot(object)
    def update_canvas(self, rsp):
        """ Update the canvas with the new image. 
        
        Parameters
        ----------
        rsp : rsp object
            The response object with the spectrum data.
        """
        data = rsp.info
        I = data['I']
        # Take the background first, before we modify I at all
        if self.taking_background == True:
            self.add_background_shot(I)
        if self.initial_update == True:
            self.initial_update = False
            self.create_plot(data['lambda'], I)
        elif self.integrating == True:
            I = self.add_integration_shot(I)
            self.spec_plot.set_ydata(I)
        else:
            if self.subtractBackCheck.isChecked() and self.background_shot != 0:
                I -= (self.background/self.background_shot)
            self.spec_plot.set_ydata(I)
        self.canvas.draw()
        
    @pyqtSlot()
    def take_background(self):
        """ Record a background for the specified number of shots. """
        self.reset_background()
        self.taking_background = True
        self.background_shot = 0
        self.disable_interaction()
        self.backProgress.setMaximum(self.backShotField.value())
        if self.streaming == False:
            self.start_stream()
            
    @pyqtSlot()
    def show_background(self):
        """ Show the background, must not be capturing. """
        self.spec_plot.set_ydata(self.background/self.background_shot)
        self.canvas.draw()
        
    @pyqtSlot()
    def start_integration(self):
        """ Start integrating the incoming signals. """
        self.reset_integration()
        self.integrating = True
        self.integration_shot = 0
        self.disable_interaction()
        self.intProgress.setMaximum(self.intShotField.value())
        if self.streaming == False:
            self.start_stream()
    
    @pyqtSlot()
    def stop_integration(self):
        """ Stop integrating the signal. """
        if self.streaming == True:
            self.stop_stream()
        self.integrating = False
        self.enable_interaction()
        
    @pyqtSlot()
    def show_integration(self):
        """ Show the last integrated signal collected. """
        data = self.get_integration_data()
        self.spec_plot.set_ydata(data)
        self.canvas.draw()
    
    @pyqtSlot(int)        
    def set_trigger(self, trigger):
        """ Set the external trigger on or off. """
        if trigger==0:
            self.startStreamButton.setEnabled(True)
            self.send_command('set_triggermode', False)
        else:
            self.startStreamButton.setEnabled(False)
            self.send_command('set_triggermode', True)
    