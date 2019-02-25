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
import pyqtgraph
import pyqtgraph as pg
import matplotlib.pyplot as plt
import numpy as np
import threading
import time
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "camera.ui")
Ui_CameraWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class CameraWindow(QtBaseClass, Ui_CameraWindow):
    data_acquired = pyqtSignal(dict)
    
    def __init__(self, parent, DAQ, device):
        """ Create the parent class and add event handlers. 
        
        Parameters
        ----------
        parent : QtClass
            The parent window that creates this window.
        DAQ : DAQ class
            The class representing the DAQ.
        device : deviceInfo object
            Object for a device.
        """
        QtBaseClass.__init__(self)
        Ui_CameraWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startStreamButton.clicked.connect(self.start_stream)
        self.stopStreamButton.clicked.connect(self.stop_stream)
        self.shutterField.valueChanged.connect(self.set_shutter)
        self.gainField.valueChanged.connect(self.set_gain)
        self.framerateField.valueChanged.connect(self.set_framerate)
        self.brightnessField.valueChanged.connect(self.set_brightness)
        self.data_acquired.connect(self.update_canvas)
        self.data_acquired.connect(self.update_info)
        self.triggerCheck.stateChanged.connect(self.set_trigger)
        
        # Grab references for controlling the camera
        self.DAQ = DAQ
        self.serial = device.serial
        self.queue = device.output_queue
        self.device = device

        # Create the container for the image
        self.create_image()
        self.create_update_thread()
        self.setWindowTitle(self.serial)
        self.set_field_range()
        
    def create_image(self):
        """ Create the matplotlib image canvas. """
        # Following the pyqtgraph VideoSpeedTest example, add the image
        pyqtgraph.setConfigOptions(imageAxisOrder='row-major')
        self.vb =  pg.ViewBox()
        self.graphicsView = pg.GraphicsView(self.imageWidget)
        self.mplvl.addWidget(self.graphicsView)
        self.graphicsView.setCentralItem(self.vb)
        self.vb.setAspectLocked()
        self.image_view = pg.ImageItem()
        self.vb.addItem(self.image_view)
        
    def create_update_thread(self):
        """ Create a thread to poll the response queue and update the image. """
        args = (self.queue, self.data_acquired.emit)
        thread = threading.Thread(target=self.update_thread, args=args, name='CameraUpdateThread')
        thread.setDaemon(True)
        thread.start()
         
    def update_thread(self, queue, callback):
        """ Wait for updated data to display. 
        
        Parameters
        ----------
        queue : queue
            The queue that the image data is arriving on.
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
        """ Perform setup after the camera connects. """
        self.startStreamButton.setEnabled(True)
        self.stopStreamButton.setEnabled(True)
        self.shutterField.setEnabled(True)
        self.gainField.setEnabled(True)
        self.framerateField.setEnabled(True)
        self.brightnessField.setEnabled(True)
        self.triggerCheck.setEnabled(True)
        
    def set_field_range(self):
        """ Set the range of the spinbox fields based on the camera serial. """
        # TODO should probably just grab this from the cameras
        serial = self.serial
        bounds = {'17583372' : {'ShutterMin' : 0.0477,
                              'GainMax' : 47.99,
                              'BrightnessMin' : 0.0,
                              'BrightnessMax' : 12.47},
                  '17571186' : {'ShutterMin' : 0.039,
                              'GainMax' : 18,
                              'BrightnessMin' : 0.0,
                              'BrightnessMax' : 25},
                  '17529184' : {'ShutterMin' : 0.0596,
                              'GainMax' : 47.99,
                              'BrightnessMin' : 0.0,
                              'BrightnessMax' : 12.475},
                  '17570564' : {'ShutterMin' : 0.0456,
                              'GainMax' : 23.99,
                              'BrightnessMin' : 1.368,
                              'BrightnessMax' : 7.42}
                  }
        self.shutterField.setMinimum(bounds[serial]['ShutterMin'])
        self.gainField.setMaximum(bounds[serial]['GainMax'])
        # The device isn't connected yet so we can't update it's parameters
        self.brightnessField.blockSignals(True)
        self.brightnessField.setRange(bounds[serial]['BrightnessMin'], 
                                      bounds[serial]['BrightnessMax'])
        self.brightnessField.setValue(bounds[serial]['BrightnessMin'])
        self.brightnessField.blockSignals(False)
        
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
        DAQ.send_command(self.device, command, *args, **kwargs)
        
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def start_stream(self):
        """ Start the camera stream and display it. """
        self.send_command('start_stream')            
        
    @pyqtSlot()
    def stop_stream(self):
        """ Stop the camera stream and the display. """
        self.send_command('stop_stream')
        
    @pyqtSlot(float)
    def set_shutter(self, value):
        """ Set the shutter value. """
        self.send_command('set_shutter_settings', (None, value))
        
    @pyqtSlot(float)
    def set_gain(self, value):
        """ Set the gain value. """
        self.send_command('set_gain_settings', (None, value))
        
    @pyqtSlot(float)
    def set_framerate(self, value):
        """ Set the framerate value. """
        self.send_command('set_frame_rate', (None, value))
        
    @pyqtSlot(float)
    def set_brightness(self, value):
        """ Set the brightness value. """
        self.send_command('set_brightness_settings', (value,))
    
    @pyqtSlot(dict)
    def update_canvas(self, data):
        """ Update the canvas with the new image. 
        
        Parameters
        ----------
        data : dict
            The dictionary with the image data and meta.
        """
        self.image_view.setImage(data['raw'], autoLevels=False)
    
    @pyqtSlot(dict)
    def update_info(self, data):
        """ Update the info blocks. 
        
        Parameters
        ----------
        data : dict
            The dictionary with the image data and meta.
        """
        DAQ = self.DAQ
        serial = self.serial
        self.r_queueNum.setNum(DAQ.response_queue[serial].qsize())
        self.s_queueNum.setNum(DAQ.save_queue[serial].qsize())
        
    @pyqtSlot(int)
    def set_trigger(self, trigger):
        """ Set the external trigger on or off. """
        print(trigger)
        if trigger==0:
            self.framerateField.setEnabled(True)
            self.send_command('set_trigger_settings', (False,))
        else:
            self.framerateField.setEnabled(False)
            self.send_command('set_trigger_settings', (True,))

# For testing the window directly
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = CameraWindow(None, None, None)
    ui.show()
    sys.exit(app.exec_())
    