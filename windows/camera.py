#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  4 16:00:22 2019

@author: robert
"""

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

qtCreatorFile = "windows/camera.ui"
Ui_CameraWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class CameraWindow(QtBaseClass, Ui_CameraWindow):
    def __init__(self, parent, DAQ, serial):
        """ Create the parent class and add event handlers. 
        
        Parameters
        ----------
        parent : QtClass
            The parent window that creates this window.
        DAQ : DAQ class
            The class representing the DAQ.
        serial : string or int
            The serial number or string of the device the window is for.
        """
        QtBaseClass.__init__(self)
        Ui_CameraWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startStreamButton.clicked.connect(self.start_stream)
        self.stopStreamButton.clicked.connect(self.stop_stream)
        
        # Grab references for controlling the camera
        self.DAQ = DAQ
        self.serial = serial
        
        # Create the matplotlib container for the image
        self.create_image()
        
    def create_image(self):
        """ Create the matplotlib image canvas. """
        self.fig = fig = Figure()
        self.im_ax = im_ax = plt.Axes(fig, [0., 0., 1., 1.])
        im_ax.set_axis_off()
        fig.add_axes(im_ax)
        im_ax.imshow([[0, 0], [0, 0]], aspect='equal')
        
        # The mplvl is a named layout on the imageWidget
        self.canvas = canvas = FigureCanvas(fig)
        self.mplvl.addWidget(canvas)
        canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, self.imageWidget,
                                         coordinates=True)
        self.mplvl.addWidget(self.toolbar)
        
    def send_command(self, command, *args):
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
        
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def start_stream(self):
        """ Start the camera stream and display it. """
        self.send_command('start_stream')            
        
    @pyqtSlot()
    def stop_stream(self):
        """ Stop the camera stream and the display. """
        # It appears that the stop capture does not actually stop the data from the camera
        self.send_command('stop_stream')
    
        
# For testing the window directly
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = CameraWindow(None, None, None)
    ui.show()
    sys.exit(app.exec_())
    