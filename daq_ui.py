#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


@author: robert
"""

import daq
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot
from windows import camera
from windows import HR4000
from windows import FRG700
# Display names for different instruments in terms of their model number
instr_display = {
        'Blackfly BFLY-PGE-31S4M' : 'Blackfly BFLY-PGE-31S4M',
        'Blackfly BFLY-PGE-13S2M' : 'Blackfly BFLY-PGE-13S2M',
        'Blackfly BFLY-PGE-50S5M' : 'Blackfly BFLY-PGE-50S5M',
        'Blackfly BFLY-PGE-50A2M' : 'Blackfly BFLY-PGE-50A2M',
        'TDS2024C' : 'TDS2024C Oscilloscope',
        'KA3005P' : 'KA3005P DC Power Supply',
        'HR4000' : 'HR4000 Spectrometer',
        'SRSDG645' : 'SRSDG645 Signal Delay Generator',
        'FRG700' : 'FRG700 Vacuum Gauge',
        }
#    '2.2 micron camera' : 
#        {'serial' : 1234567,
#         'name' : 'Camera'},
#    '3.45 (2048x1536) micron camera' : 
#        {'serial' : 17583372,
#         'name' : 'Camera'},
#    '3.75 micron camera' : 
#        {'serial' : 17570564,
#         'name' : 'Camera'},
#    '3.45 (2448x2048) micron camera' : 
#        {'serial' : 17529184,
#         'name': 'Camera'}
#    }

qtCreatorFile = "DAQGUI.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

window_dict = {
        'Camera' : camera.CameraWindow,
        'HR4000' : HR4000.SpecWindow,
        'FRG700' : FRG700.GaugeWindow,
        }

# DAQ UI classes
class UI(QtBaseClass, Ui_MainWindow):
    def __init__(self):
        """ Create the parent UI classes and add event handlers. """
        QtBaseClass.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.connectButton.clicked.connect(self.connect_instrs)
        self.refreshListButton.clicked.connect(self.refresh_list)
        self.disconnectButton.clicked.connect(self.disconnect_instr)
        self.detailButton.clicked.connect(self.open_detail_panel)
        self.startDatasetButton.clicked.connect(self.start_dataset)
        
        # Define useful variables
        self.connected_instr = {}
        self.available_instr = {}
        self.initial_dataset = True
        
    def center(self, DAQWindow):
        resolution = QtGui.QDesktopWidget().screenGeometry()
        DAQWindow.move((resolution.width() / 2) - \
                       (DAQWindow.frameSize().width() / 2),
                  (resolution.height() / 2) - \
                  (DAQWindow.frameSize().height() / 2)) 
        
    def print_output(self, msg):
        """ Print a newline to the output text box. """
        pass
    
    def set_dataset_num(self):
        """ Set the dataset number to the DAQ's dataset. """
        self.datasetNumber.setNum(self.DAQ.dataset)
        
    def set_shot_number(self, num):
        """ Set the shot number. """
        self.shotNumber.setNum(num)
        
    def set_totalshot_number(self, num):
        """ Set the total number of shots for the dataset. """
        self.totalshotNumber.setNum(num)
    
    # List Manipulation
    ###########################################################################
    def create_item(self, key, instr_item, parent):
        """ Create the item object for the lists. 
        
        Parameters
        ----------
        key : string
            The unique key for the instrument, normally the serial number.
        instr_item : dict
            Dictionary for an instrument from DAQ.get_available_instr.
        parent : QListWidget
            The list to add the item to.
        
        Returns
        -------
        instr_item : dict
            The instr dictionary with the QListWidgetItem added.
        """
        if instr_item['model'] in instr_display:
            text = instr_display[instr_item['model']]+' ('+str(key)+')'
        else:
            text = instr_item['model']+' ('+str(key)+')'
        item = QtGui.QListWidgetItem(text, parent=parent)
        item.__key__ = key
        instr_item['item'] = item
        return instr_item
    
    def remove_item(self, instr_item, parent):
        """ Remove an item from a list. 
        
        Parameters
        ----------
        instr_item : dict
            Dictionary representing an item.
        parent : QListWidget
            The list to remove the item from.
        """
        item = instr_item['item']
        row = parent.row(item)
        parent.takeItem(row)
        
    def add_item(self, instr_item, parent):
        """ Add an item to a list. 
        
        Parameters
        ----------
        instr_item : dict
            Dictionary representing an item.
        parent : QListWidget
            The list to add the item to.
        """
        item = instr_item['item']
        parent.addItem(item)
    
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def refresh_list(self):
        """ Refresh the list of connected instruments. """
        available_instr = self.available_instr
        connected_instr = self.connected_instr
        instr = self.DAQ.get_available_instr()
        for key in instr:
            if key not in connected_instr and key not in available_instr:
                item = self.create_item(key, instr[key], self.availableList)
                available_instr[key] = item
        
        # Check to make sure available instruments are still available
        for key in list(available_instr.keys()):
            if key not in instr:
                self.remove_item(available_instr[key], self.availableList)
                del available_instr[key]
        
        # XXX might want to remove it from the connected instruments as well
    
    @pyqtSlot()
    def connect_instrs(self):
        """ Connect the DAQ to the selected instruments. """
        available_instr = self.available_instr
        connected_instr = self.connected_instr
        add_list = self.availableList.selectedItems()
        for item in add_list:
            key = item.__key__
            instr = available_instr[key]
            # Move things between the lists
            self.remove_item(instr, self.availableList)
            self.add_item(instr, self.connectedList)
            connected_instr[key] = available_instr.pop(key)
            # Connect the instrument within the DAQ
            queue = self.DAQ.connect_instr(instr['name'], instr['adr'])
            if queue is not None:
                # Create the popup window for the instrument
                instr['window'] = window_dict[instr['name']](self, self.DAQ, key, queue)
        
    @pyqtSlot()
    def disconnect_instr(self):
        """ Disconnect the DAQ from the selected instrument. """
        available_instr = self.available_instr
        connected_instr = self.connected_instr
        remove_list = self.connectedList.selectedItems()
        for item in remove_list:
            key = item.__key__
            instr = connected_instr[key]
            # Move things between the lists
            self.remove_item(instr, self.connectedList)
            self.add_item(instr, self.availableList)
            available_instr[key] = connected_instr.pop(key)
            # Disconnect the instrument from the DAQ
            self.DAQ.disconnect_instr(instr['name'], key)
    
    @pyqtSlot()
    def open_detail_panel(self):
        """ Open the detail panel for the selected instruments. """
        open_list = self.connectedList.selectedItems()
        for item in open_list:
            key = item.__key__
            instr = self.connected_instr[key]
            instr['window'].show()
    
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
    
    def closeEvent(self, event):
        """ Override the close method to disconnect all devices. """
        self.DAQ.turn_off_daq()
        event.accept()
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    #DAQWindow = DAQMainWindow()
    ui = UI()
    ui.DAQ = daq.Daq()
    ui.set_dataset_num()
    #DAQWindow.PWFAui = ui
    #ui.setupUi(DAQWindow)
    #ui.center(DAQWindow)
    #DAQWindow.show()
    ui.show()
    sys.exit(app.exec_())
