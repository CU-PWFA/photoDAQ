#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  4 16:00:22 2019

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
import time

qtCreatorFile = "windows/camera.ui"
Ui_CameraWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class CameraWindow(QtBaseClass, Ui_CameraWindow):
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
        Ui_CameraWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startStreamButton.clicked.connect(self.start_stream)
        self.stopStreamButton.clicked.connect(self.stop_stream)
        
        # Grab references for controlling the camera
        self.DAQ = DAQ
        self.serial = serial
        self.queue = queue
        th = Thread(queue, parent=self)
        th.changePixmap.connect(self.setPixMap)
        th.start()
        # Create the matplotlib container for the image
        #self.create_image()
        #self.create_update_thread()
        
    def create_image(self):
        """ Create the matplotlib image canvas. """
        self.fig = fig = Figure()
        self.im_ax = im_ax = plt.Axes(fig, [0., 0., 1., 1.])
        im_ax.set_axis_off()
        fig.add_axes(im_ax)
        self.image = im_ax.imshow([[0, 0], [0, 0]], aspect='equal', animated=True)
        
        # The mplvl is a named layout on the imageWidget
        self.canvas = canvas = FigureCanvas(fig)
        self.mplvl.addWidget(canvas)
        canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, self.imageWidget,
                                         coordinates=True)
        self.mplvl.addWidget(self.toolbar)
        
    def create_update_thread(self):
        """ Create a thread to poll the response queue and update the image. """
        args = (self.queue,)
        thread = threading.Thread(target=self.update_thread, args=args)
        thread.setDaemon(True)
        thread.start()
         
    def update_thread(self, queue):
        """ Wait for updated data to display. 
        
        Parameters
        ----------
        queue : queue
            The queue that the image data is arriving on.
        """
        while True:
            data = queue.get()
            if data == 'Connected':
                self.enable_window()
            else:
                self.update_canvas(data)
            queue.task_done()
            
    def update_canvas(self, data):
        """ Update the canvas with the new image. 
        
        Parameters
        ----------
        data : dict
            The dictionary with the image data and meta.
        """
        self.im_ax.clear()
        self.im_ax.set_axis_off()
        # XXX set_array or set_data should work, but they don't
        #self.image.set_array(data['raw'])
        self.im_ax.imshow(data['raw'], aspect='equal')
        self.canvas.draw()
        
    def enable_window(self):
        """ Enable control of the instrument after it connects. """
        pass
        
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
        
    @pyqtSlot(QImage)
    def setPixMap(self, p):
        p = QPixmap.fromImage(p)    
        self.label.setPixmap(p)
    
       
class Thread(QThread):
    changePixmap = pyqtSignal(QImage)
    def __init__(self, queue, parent=None):
        super().__init__(parent=parent)
        self.queue = queue

    def run(self):
        while True:
            data = self.queue.get()
            if data == 'Connected':
                pass
            else:
                width, height = data['meta']['pixel']
                rawImage = QImage(data['raw'], width, height, QImage.Format_Indexed8)
                self.changePixmap.emit(rawImage)
            self.queue.task_done()
# For testing the window directly
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = CameraWindow(None, None, None)
    ui.show()
    sys.exit(app.exec_())
    