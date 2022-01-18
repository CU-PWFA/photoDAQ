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
from scipy.ndimage import center_of_mass
import threading
import time
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "camera.ui")
Ui_CameraWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class CameraWindow(QtBaseClass, Ui_CameraWindow):
    data_acquired = pyqtSignal(object)
    device_connected = pyqtSignal(object)
    
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
        Ui_CameraWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.startStreamButton.clicked.connect(self.start_stream)
        self.stopStreamButton.clicked.connect(self.stop_stream)
        self.shutterField.valueChanged.connect(self.set_shutter)
        self.gainField.valueChanged.connect(self.set_gain)
        self.framerateField.valueChanged.connect(self.set_framerate)
        self.data_acquired.connect(self.update_canvas)
        self.data_acquired.connect(self.update_info)
        self.triggerCheck.stateChanged.connect(self.set_trigger)
        self.device_connected.connect(self.setup_window)
        self.startXField.valueChanged.connect(self.set_offsetX)
        self.startYField.valueChanged.connect(self.set_offsetY)
        self.heightField.valueChanged.connect(self.set_height)
        self.widthField.valueChanged.connect(self.set_width)
        self.fullROIButton.clicked.connect(self.fullROI)
        self.referenceCrossCheck.stateChanged.connect(self.toggle_ref_cross)
        self.crossXField.valueChanged.connect(self.set_cross)
        self.crossYField.valueChanged.connect(self.set_cross)
        self.centroidCrossCheck.stateChanged.connect(self.toggle_cen_cross)
        self.getCenButton.clicked.connect(self.ref_centroid)
        
        # Grab references for controlling the camera
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr

        # Create the container for the image
        self.create_image()
        self.create_update_thread()
        self.setWindowTitle(self.serial)
        
        self.refvLine = None
        self.refhLine = None
        self.cenvLine = None
        self.cenhLine = None
        self.calc_cen = False
        self.cen_x = 0
        self.cen_y = 0
        
    def create_image(self):
        """ Create the matplotlib image canvas. """
        # Following the pyqtgraph VideoSpeedTest example, add the image
        pyqtgraph.setConfigOptions(imageAxisOrder='row-major')
        #self.vb = pg.ViewBox()
        #self.graphicsView = pg.GraphicsView(self.imageWidget)
        #self.mplvl.addWidget(self.graphicsView)
        #self.graphicsView.setCentralItem(self.vb)
        #self.vb.setAspectLocked()
        #self.image_view = pg.ImageItem()
        #self.vb.addItem(self.image_view)
        self.image_view = pg.ImageView()
        self.mplvl.addWidget(self.image_view)
        self.image_view.setHistogramRange(0, 2**8)
        self.image_view.setLevels(0, 2**8)
        self.image_view.ui.roiBtn.setVisible(False)
        self.image_view.ui.menuBtn.setVisible(False)
        
    def create_update_thread(self):
        """ Create a thread to poll the response queue and update the image. """
        args = (self.queue, self.data_acquired.emit, self.device_connected.emit)
        thread = threading.Thread(target=self.update_thread, args=args, name='CameraUpdateThread')
        thread.setDaemon(True)
        thread.start()
         
    def update_thread(self, queue, callback, setup):
        """ Wait for updated data to display. 
        
        Parameters
        ----------
        queue : queue
            The queue that the image data is arriving on.
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
                setup(rsp)
            else:
                callback(rsp)
            queue.task_done()
        
    def set_field_range(self, rsp):
        """ Set the range and values of the spinbox fields based on the camera. 
        
        Parameters
        ----------
        rsp : object
            The response object from the connection response. The data contains
            the INFO objects from the camera.
        """
        data = rsp.info
        self.gainField.blockSignals(True)
        self.gainField.setMaximum(data['GainMax'])
        self.gainField.setValue(data['Gain'])
        self.gainField.blockSignals(False)
        
        self.shutterField.blockSignals(True)
        self.shutterField.setMinimum(data['ShutterMin'])
        self.shutterField.setMaximum(data['ShutterMax'])
        self.shutterField.setValue(data['Shutter'])
        self.shutterField.blockSignals(False)
        
        self.framerateField.blockSignals(True)
        self.framerateField.setValue(data['Framerate'])
        self.framerateField.blockSignals(False)
        
        offsetX = data['OffsetX']
        offsetY = data['OffsetY']
        height = data['Height']
        width = data['Width']
        self.maxHeight = maxHeight = data['SensorHeight']
        self.maxWidth = maxWidth = data['SensorWidth']
        
        self.startXField.blockSignals(True)
        self.startXField.setMaximum(maxWidth-width)
        self.startXField.setValue(offsetX)
        self.startXField.blockSignals(False)
        
        self.startYField.blockSignals(True)
        self.startYField.setMaximum(maxHeight-height)
        self.startYField.setValue(offsetY)
        self.startYField.blockSignals(False)
        
        self.heightField.blockSignals(True)
        self.heightField.setMaximum(maxHeight-offsetY)
        self.heightField.setValue(height)
        self.heightField.blockSignals(False)
        
        self.widthField.blockSignals(True)
        self.widthField.setMaximum(maxWidth-offsetX)
        self.widthField.setValue(width)
        self.widthField.blockSignals(False)
        
        self.crossXField.blockSignals(True)
        self.crossXField.setMaximum(maxWidth-offsetX)
        self.crossXField.blockSignals(False)
        
        self.crossYField.blockSignals(True)
        self.crossYField.setMaximum(maxHeight-offsetY)
        self.crossYField.blockSignals(False)
        
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
        
    def hide_ref_cross(self):
        self.image_view.removeItem(self.refvLine)
        self.image_view.removeItem(self.refhLine)
    
    def draw_ref_cross(self):
        if self.refvLine is None:
            self.refvLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('b', width=1))
        if self.refhLine is None:
            self.refhLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('b', width=1))
        self.image_view.addItem(self.refvLine, ignoreBounds=True)
        self.image_view.addItem(self.refhLine, ignoreBounds=True)
        self.refvLine.setPos(self.crossXField.value()+0.5)
        self.refhLine.setPos(self.crossYField.value()+0.5)
        
    def hide_cen_cross(self):
        self.image_view.removeItem(self.cenvLine)
        self.image_view.removeItem(self.cenhLine)
    
    def draw_cen_cross(self):
        if self.cenvLine is None:
            self.cenvLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('g', width=1))
        if self.cenhLine is None:
            self.cenhLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('g', width=1))
        self.image_view.addItem(self.cenvLine, ignoreBounds=True)
        self.image_view.addItem(self.cenhLine, ignoreBounds=True)
        self.cenvLine.setPos(self.cen_x)
        self.cenhLine.setPos(self.cen_y)
        
    def find_cen(self, data):
        self.CM = center_of_mass(data)
        #CM = [500, 500]
        self.cen_x = self.CM[1]
        self.cen_y = self.CM[0]
        
    # Event Handlers
    ###########################################################################
    @pyqtSlot(object)
    def setup_window(self, rsp):
        """ Perform setup after the camera connects. """
        self.set_field_range(rsp)
        
        self.startStreamButton.setEnabled(True)
        self.stopStreamButton.setEnabled(True)
        self.shutterField.setEnabled(True)
        self.gainField.setEnabled(True)
        self.framerateField.setEnabled(True)
        self.triggerCheck.setEnabled(True)
        self.startXField.setEnabled(True)
        self.startYField.setEnabled(True)
        self.widthField.setEnabled(True)
        self.heightField.setEnabled(True)
        self.fullROIButton.setEnabled(True)
    
    @pyqtSlot()
    def start_stream(self):
        """ Start the camera stream and display it. """
        self.heightField.setEnabled(False)
        self.widthField.setEnabled(False)
        self.fullROIButton.setEnabled(False)
        self.send_command('start_stream')
        
    @pyqtSlot()
    def stop_stream(self):
        """ Stop the camera stream and the display. """
        self.send_command('stop_stream')
        self.heightField.setEnabled(True)
        self.widthField.setEnabled(True)
        self.fullROIButton.setEnabled(True)
        
    @pyqtSlot(float)
    def set_shutter(self, value):
        """ Set the shutter value. """
        self.send_command('set_shutter', value)
        
    @pyqtSlot(float)
    def set_gain(self, value):
        """ Set the gain value. """
        self.send_command('set_gain', value)
        
    @pyqtSlot(float)
    def set_framerate(self, value):
        """ Set the framerate value. """
        self.send_command('set_frame_rate', value)
        
    @pyqtSlot(float)
    def set_offsetX(self, value):
        """ Set the offsetX value. """
        # Ensure the number is even
        value = int(value/2)*2
        self.widthField.setMaximum(self.maxWidth-value)
        self.crossXField.setMaximum(self.maxWidth-value)
        self.send_command('set_offsetX', value)

    @pyqtSlot(float)
    def set_offsetY(self, value):
        """ Set the offsetY value. """
        value = int(value/2)*2
        self.heightField.setMaximum(self.maxHeight-value)
        self.crossYField.setMaximum(self.maxHeight-value)
        self.send_command('set_offsetY', value)
        
    @pyqtSlot(float)
    def set_height(self, value):
        """ Set the height value. """
        value = int(value/2)*2
        self.startYField.setMaximum(self.maxHeight-value)
        self.send_command('set_height', value)
        
    @pyqtSlot(float)
    def set_width(self, value):
        """ Set the width value. """
        value = int(value/4)*4
        self.startXField.setMaximum(self.maxWidth-value)
        self.send_command('set_width', value)
    
    @pyqtSlot(object)
    def update_canvas(self, rsp):
        """ Update the canvas with the new image. 
        
        Parameters
        ----------
        rsp : rsp object
            The response object with the image data.
        """
        self.image_view.setImage(rsp.data, autoLevels=False, autoRange=False,
                                 autoHistogramRange=False)
        if self.calc_cen:
            self.find_cen(rsp.data)
            if self.centroidCrossCheck.isChecked():
                self.draw_cen_cross()
                
    
    @pyqtSlot(dict)
    def update_info(self, rsp):
        """ Update the info blocks. 
        
        Parameters
        ----------
        rsp : rsp object
            The response object with the image data.
        """
        self.r_queueNum.setNum(self.instr.response_queue.qsize())
        self.s_queueNum.setNum(self.instr.output_queue.qsize())
        
    @pyqtSlot(int)
    def set_trigger(self, trigger):
        """ Set the external trigger on or off. """
        if trigger==0:
            self.startStreamButton.setEnabled(True)
            self.framerateField.setEnabled(True)
            self.send_command('set_trigger_settings', False)
        else:
            self.startStreamButton.setEnabled(True)
            self.framerateField.setEnabled(False)
            self.send_command('set_trigger_settings', True)
            
    @pyqtSlot()
    def fullROI(self):
        """ Start the camera stream and display it. """
        self.startXField.setValue(0)
        self.startYField.setValue(0)
        self.heightField.setValue(self.heightField.maximum())
        self.widthField.setValue(self.widthField.maximum())
        
    @pyqtSlot(int)
    def toggle_ref_cross(self, cross):
        if cross==0:
            self.hide_ref_cross()
        else:
            self.draw_ref_cross()
            
    @pyqtSlot(float)
    def set_cross(self, value):
        if self.referenceCrossCheck.isChecked():
            self.draw_ref_cross()
        
    @pyqtSlot(int)
    def toggle_cen_cross(self, cross):
        if cross==0:
            self.calc_cen = False
            self.hide_cen_cross()
        else:
            self.calc_cen = True
            self.draw_cen_cross()
            self.getCenButton.setEnabled(True)
            
    @pyqtSlot()
    def ref_centroid(self):
        self.crossXField.setValue(self.CM[1])
        self.crossYField.setValue(self.CM[0])
            

# For testing the window directly
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = CameraWindow(None, None, None)
    ui.show()
    sys.exit(app.exec_())
    