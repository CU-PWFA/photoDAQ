#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


@author: robert
"""

import daq
import detect
from PyQt4.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt4 import QtCore, QtGui, uic
import threading

# Display names for different instruments in terms of their model number
instr_display = {
        'Blackfly BFLY-PGE-31S4M' : 'Blackfly BFLY-PGE-31S4M',
        'Blackfly BFLY-PGE-13S2M' : 'Blackfly BFLY-PGE-13S2M',
        'Blackfly BFLY-PGE-50S5M' : 'Blackfly BFLY-PGE-50S5M',
        'Blackfly BFLY-PGE-50A2M' : 'Blackfly BFLY-PGE-50A2M',
        'TDS2024C' : 'TDS2024C Oscilloscope',
        'KA3005P' : 'KA3005P DC Power Supply',
        'HR4000' : 'HR4000 Spectrometer',
        'DG645' : 'SRSDG645 Signal Delay Generator',
        'FRG700' : 'FRG700 Vacuum Gauge',
        'FS304' : '304 FS Turbomolecular Pump',
        }

qtCreatorFile = "DAQGUI.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# DAQ UI classes
class UI(QtBaseClass, Ui_MainWindow):
    message_acquired = pyqtSignal(str)
    
    def __init__(self, DAQ):
        """ Create the parent UI classes and add event handlers. 
        
        Parameters
        ----------
        DAQ : Daq object
            The main daq object controlling the daq.
        """
        QtBaseClass.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.DAQ = DAQ
        
        # Add event handlers to all the buttons
        self.message_acquired.connect(self.print_log)
        self.connectButton.clicked.connect(self.connect_instrs)
        self.refreshListButton.clicked.connect(self.refresh_list)
        self.disconnectButton.clicked.connect(self.disconnect_instr)
        self.detailButton.clicked.connect(self.open_detail_panel)
        self.startDatasetButton.clicked.connect(self.start_dataset)
        self.detectSerialButton.clicked.connect(self.detect_serial)
        self.detectSpecButton.clicked.connect(self.detect_spectrometer)
        self.detectVisaButton.clicked.connect(self.detect_visa)
        self.detectSDGButton.clicked.connect(self.detect_SDG)
        self.detectCamerasButton.clicked.connect(self.detect_camera)
        
        # Define useful variables
        self.connected_instr = {} # Tracks all connected instruments
        self.available_instr = {} # Tracks all available unconnected instruments
        self.initial_dataset = True
        
        # Create the logging thread
        self.create_logging_thread()
        
    def center(self, DAQWindow):
        resolution = QtGui.QDesktopWidget().screenGeometry()
        DAQWindow.move((resolution.width() / 2) - \
                       (DAQWindow.frameSize().width() / 2),
                  (resolution.height() / 2) - \
                  (DAQWindow.frameSize().height() / 2)) 
        
    def create_logging_thread(self):
        """ Create a thread to pull from stdout. """
        args = (self.DAQ.p_queue, self.message_acquired.emit)
        thread = threading.Thread(target=self.logging_thread, args=args)
        thread.setDaemon(True)
        thread.start()
        
    def logging_thread(self, queue, callback):
        """ Wait for data to be printed to stdout. 
        
        Parameters
        ----------
        queue : queue
            The queue that the data is arriving on.
        callback : func
            The signal.emit to call to update the field. 
        """
        while True:
            text = queue.get()
            if text == '__exit__':
                break
            else:
                callback(text)
            queue.task_done()
    
    def set_dataset_num(self):
        """ Set the dataset number to the DAQ's dataset. """
        self.datasetNumber.setNum(self.DAQ.dataset)
        
    def set_shot_number(self, num):
        """ Set the shot number. """
        self.shotNumber.setNum(num)
        
    def set_totalshot_number(self, num):
        """ Set the total number of shots for the dataset. """
        self.totalshotNumber.setNum(num)
    
    # TODO should update this so an instrument can be in more than one list
    # List Manipulation
    ###########################################################################
    def create_item(self, serial, instr, parent):
        """ Adds the QListWidgetItem to the instrument and adds it to a list. 
        
        Parameters
        ----------
        serial : string
            The serial number for the instrument.
        instr : instr object
            Object for a instrument.
        parent : QListWidget
            The list to add the item to.
        """
        if instr.model in instr_display:
            text = instr_display[instr.model]+' ('+instr.serial+')'
        else:
            text = instr.model+' ('+instr.serial+')'
        item = QtGui.QListWidgetItem(text, parent=parent)
        item.__key__ = serial
        instr.item = item
    
    def remove_item(self, instr, parent):
        """ Remove a instrument from a list. 
        
        Parameters
        ----------
        instr : instr object
            Object for a instrument.
        parent : QListWidget
            The list to remove the item from.
        """
        item = instr.item
        row = parent.row(item)
        parent.takeItem(row)
        
    def add_item(self, instr, parent):
        """ Add an item to a list. 
        
        Parameters
        ----------
        instr : instr object
            Object for an instrument.
        parent : QListWidget
            The list to add the item to.
        """
        item = instr.item
        parent.addItem(item)
        
    def add_instrs(self, instrs):
        """ Add the passed instruments to the available list. 
        
        Parameters
        ----------
        instr : dictionary
            Dictionary with serial number keys and instr object items.
        """
        available_instr = self.available_instr
        connected_instr = self.connected_instr
        for serial, instr in instrs.items():
            if serial not in connected_instr and serial not in available_instr:
                self.create_item(serial, instr, self.availableList)
                available_instr[serial] = instr
                
    def integrate_instr(self, instr):
        """ Add an direct integration with the DAQ main panel. 
        
        Parmaeters
        ----------
        instr : instr object
            Object for an instrument.
        """
        # Turbomolecular pump integration
        if instr.device_type == 'FS304':
            self.integrate_turbo(instr)
        elif instr.device_type == 'FRG700':
            self.integrate_gauge(instr)
    
    # Vacuum system integration
    ###########################################################################
    # Turbo molecular pump
    #--------------------------------------------------------------------------
    def integrate_turbo(self, instr):
        """ Add connections with the turbo molecular pump. 
        
        Parmaeters
        ----------
        instr : instr object
            Object for the turbo pump.
        """
        win = instr.window
        win.data_acquired.connect(self.update_turbo_status)
        win.device_connected.connect(win.start_stream)
        win.device_connected.connect(self.setup_turbo)
        self.startTurboButton.clicked.connect(win.start_turbo)
        self.stopTurboButton.clicked.connect(win.stop_turbo)
        
    @pyqtSlot(object)
    def update_turbo_status(self, rsp):
        """ Update the turbo information pages. 
        
        Parameters
        ----------
        rsp : rsp object
            The response object with the pump status.
        """
        self.turboPower.setText(str(rsp.data['power'])+' W')
        self.turboStatus.setText(rsp.data['status'])
        
    @pyqtSlot()
    def setup_turbo(self):
        """ Eanble the turbo buttons once the pump is connected. """
        self.startTurboButton.setEnabled(True)
        self.stopTurboButton.setEnabled(True)
        
    # Vacuum gauge
    #--------------------------------------------------------------------------
    def integrate_gauge(self, instr):
        """ Add connections with the vacuum gauge controller. 
        
        Parmaeters
        ----------
        instr : instr object
            Object for the turbo pump.
        """
        win = instr.window
        win.data_acquired.connect(self.update_chamber_pressure)
        win.device_connected.connect(win.start_stream)
    
    @pyqtSlot(object)
    def update_chamber_pressure(self, rsp):
        """ Update the chamber pressure readouts. 
        
        Parameters
        ----------
        rsp : rsp object
            The response object with the gauge pressures.
        """
        self.APressure.setText('%0.2E' % rsp.data[0])
        self.BPressure.setText('%0.2E' % rsp.data[3])
    
    # Event Handlers
    ###########################################################################
    @pyqtSlot(str)
    def print_log(self, text):
        self.logBrowser.moveCursor(QtGui.QTextCursor.End)
        self.logBrowser.insertPlainText(text)
    
    @pyqtSlot()
    def refresh_list(self):
        """ Refresh the list of available instruments. """
        available_instr = self.available_instr
        instrs = detect.all_instrs()
        self.add_instrs(instrs)
        
        # Check to make sure available instruments are still available
        for serial in list(available_instr.keys()):
            if serial not in instrs:
                self.remove_item(available_instr[serial], self.availableList)
                del available_instr[serial]
        
        # XXX might want to remove it from the connected instruments as well
        
    @pyqtSlot()
    def detect_serial(self):
        """ Detect and add serial device to the available instruments. """
        instrs = detect.serial_ports()
        self.add_instrs(instrs)
        
    @pyqtSlot()
    def detect_spectrometer(self):
        """ Detect and add spectrometers to the available instruments. """
        instrs = detect.spectrometer()
        self.add_instrs(instrs)
        
    @pyqtSlot()
    def detect_visa(self):
        """ Detect and add visa instruments to the available instruments. """
        instrs = detect.pyvisa()
        self.add_instrs(instrs)
        
    @pyqtSlot()
    def detect_SDG(self):
        """ Detect and add the SDG to the available instruments. """
        instrs = detect.SRSDG645()
        self.add_instrs(instrs)
        
    @pyqtSlot()
    def detect_camera(self):
        """ Detect and add cameras to the available instruments. """
        instrs = detect.camera()
        self.add_instrs(instrs)
    
    @pyqtSlot()
    def connect_instrs(self):
        """ Connect the DAQ to the selected instruments. """
        available_instr = self.available_instr
        connected_instr = self.connected_instr
        add_list = self.availableList.selectedItems()
        for item in add_list:
            serial = item.__key__
            instr = available_instr[serial]
            # Move things between the lists
            self.remove_item(instr, self.availableList)
            self.add_item(instr, self.connectedList)
            connected_instr[serial] = available_instr.pop(serial)
            # Connect the instrument within the DAQ
            self.DAQ.connect_instr(instr)
            if instr.window_cls is not None:
                instr.window = instr.window_cls(self, self.DAQ, instr)
                self.integrate_instr(instr)
        
    @pyqtSlot()
    def disconnect_instr(self):
        """ Disconnect the DAQ from the selected instrument. """
        available_instr = self.available_instr
        connected_instr = self.connected_instr
        remove_list = self.connectedList.selectedItems()
        for item in remove_list:
            serial = item.__key__
            instr = connected_instr[serial]
            # Move things between the lists
            self.remove_item(instr, self.connectedList)
            self.add_item(instr, self.availableList)
            available_instr[serial] = connected_instr.pop(serial)
            # Disconnect the instrument from the DAQ
            self.DAQ.disconnect_instr(instr)
    
    @pyqtSlot()
    def open_detail_panel(self):
        """ Open the detail panel for the selected instruments. """
        open_list = self.connectedList.selectedItems()
        for item in open_list:
            serial = item.__key__
            instr = self.connected_instr[serial]
            instr.window.show()
    
    @pyqtSlot()
    def start_dataset(self):
        """ Start a new dataset. """
        DAQ = self.DAQ
        # Don't create a new dataset if it is the initial dataset
        if self.initial_dataset:
            self.initial_dataset = False
            DAQ.desc = self.DescriptionEdit.toPlainText()
        else:
            DAQ.adv_dataset(self.DescriptionEdit.toPlainText())
            self.set_dataset_num()
        shots = self.shotsField.value()
        DAQ.save_stream(shots)
    
    def closeEvent(self, event):
        """ Override the close method to disconnect all instruments. """
        self.DAQ.close_daq()
        # Cause the logging thread to end
        print('__exit__')
        event.accept()
    
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    DAQ = daq.Daq(broadcast=True)
    ui = UI(DAQ)
    ui.set_dataset_num()
    ui.show()
    sys.exit(app.exec_())
