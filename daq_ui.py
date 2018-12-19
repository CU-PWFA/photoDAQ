import PyCapture2 as pc2
import numpy as np
import daq
import cv2
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot
import liveView as lv
import file
import globalVAR as Gvar
import time
import importlib
import passive_daq as pd
# Dictionaries for the DAQ instruments
instr_dict = {
    '2.2 micron camera' : 
        {'serial' : 1234567,
         'name' : 'Camera'},
    '3.45 (2048x1536) micron camera' : 
        {'serial' : 17583372,
         'name' : 'Camera'},
    '3.75 micron camera' : 
        {'serial' : 17570564,
         'name' : 'Camera'},
    '3.45 (2448x2048) micron camera' : 
        {'serial' : 17529184,
         'name': 'Camera'}
    }

qtCreatorFile = "DAQGUI.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# Functions for the DAQ
def getAvailableCameras():
    # Dictionary of available cameras
    cam_dict = {17571186.0:'2.2', 17583372.0:'3.45 (2048x1536)', \
                17570564.0:'3.75', 17529184.0:"3.45 (2448x2048)"}
    bus   = pc2.BusManager()
    nCams = bus.getNumOfCameras()
    cam_list = {}
    for i in range(nCams):
        cam_list[i] = cam_dict[bus.getCameraSerialNumberFromIndex(i)]  + \
        " micron camera"
    # convert to int
    return cam_list 

def clearSelection(listWidget):
    for i in range(listWidget.count()):
        item = listWidget.item(i)
        listWidget.setItemSelected(item, False) 
def passDAQFunc(self):
	ui = self.PWFAui
    # Get number of shots to take
	ui.DAQProgress.setValue(0)

# DAQ UI classes
class UI(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        """ Create the parent UI classes and add event handlers. """
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.connectButton.clicked.connect(self.connect_instrs)
        self.refreshListButton.clicked.connect(self.refresh_list)
        self.disconnectButton.clicked.connect(self.disconnect_instr)
        self.detailButton.clicked.connect(self.open_detail_panel)
        
        # Define useful variables
        self.connected_instr = {}
        self.available_instr = {}
        
    def center(self, DAQWindow):
        resolution = QtGui.QDesktopWidget().screenGeometry()
        DAQWindow.move((resolution.width() / 2) - \
                       (DAQWindow.frameSize().width() / 2),
                  (resolution.height() / 2) - \
                  (DAQWindow.frameSize().height() / 2)) 
        
    def print_output(self, msg):
        """ Print a newline to the output text box. """
        pass
    
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def refresh_list(self):
        """ Refresh the list of connected instruments. """
        DAQ = self.DAQ
        instr = DAQ.get_available_instr()
        self.availableList.clear()
        for i in range(len(instr)):
            self.availableList.addItem(instr[i])
    
    @pyqtSlot()
    def connect_instrs(self):
        """ Connect the DAQ to the selected instruments. """
        # Get current connected list to make sure there are no repeats
        connectedInstr = []
        for i in range(self.connectedList.count()):
            connectedInstr.append(self.connectedList.item(i).text())
        
        add_list = self.availableList.selectedItems()
        # If its not a repeat add it to the selected list widget
        # XXX We should handle repeats when we refresh the list so we don't need to check here
        for i in add_list:
            if not i.text() in connectedInstr:
                self.connectedList.addItem(i.text())
                #self.instr = daq.connect_instr(self.instr_dict[i.text()], \
                #                        self.instr_serials[i.text()], self.instr)
        clearSelection(self.availableList)
        
    @pyqtSlot()
    def disconnect_instr(self):
        """ Disconnect the DAQ from the selected instrument. """
        pass
    
    @pyqtSlot()
    def open_detail_panel(self):
        """ Open the detail panel for a given instrument. """
        pass


class DAQMainWindow(QtGui.QMainWindow):
    def addFunction(self):
        ui = self.PWFAui
        # Get current selected list to make sure there are no repeats
        selectedList = []
        for index in range(ui.selectedListWidget.count()):
            selectedList.append(ui.selectedListWidget.item(index).text())
        
        add_list = ui.availableListWidget.selectedItems()
        # If its not a repeat add it to the selected list widget
        for i in add_list:
            if not i.text() in selectedList:
                ui.selectedListWidget.addItem(i.text())
                # Add item as a daq instrument
                
                self.instr = daq.connect_instr(self.instr_dict[i.text()], \
                                        self.instr_serials[i.text()], self.instr)
        clearSelection(ui.availableListWidget)
        
    def refreshListFunc(self):
        ui = self.PWFAui
        ui.availableListWidget.clear()
        cam_list = getAvailableCameras()
        for i in cam_list:
            ui.availableListWidget.addItem(cam_list[i])
        ui.refreshListButton.setText("Refresh list")
        
    def removeFunction(self):
        ui = self.PWFAui
        for i in ui.selectedListWidget.selectedItems():
            # Disconnect  in daq
            self.instr = daq.disconnect_instr(self.instr_dict[i.text()], \
                                 self.instr, \
                                 self.instr[str(self.instr_serials[i.text()])])
            # delete from list
            ui.selectedListWidget.takeItem(ui.selectedListWidget.row(i))
            
    def liveViewFunc(self):
        ui = self.PWFAui
        if len(ui.selectedListWidget.selectedItems()) > 1:
            QtGui.QMessageBox.question(self, 'Error', 'May only select one camera.')
        else:
            name = ui.selectedListWidget.selectedItems()[0].text()
            lv.streamCam(self.instr[str(self.instr_serials[name])], name)
            self.instr = daq.disconnect_instr(self.instr_dict[name], self.instr, \
            	                              self.instr[str(self.instr_serials[name])])
            self.instr = daq.connect_instr(self.instr_dict[name], self.instr_serials[name],\
                                           self.instr)
            
    def startDAQFunc(self):
    	if self.PWFAui.PassDAQCheckBox.isChecked():
    		passDAQFunc(self)
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    #DAQWindow = DAQMainWindow()
    ui = UI()
    ui.DAQ = daq.Daq()
    #DAQWindow.PWFAui = ui
    #ui.setupUi(DAQWindow)
    #ui.center(DAQWindow)
    #DAQWindow.show()
    ui.show()
    sys.exit(app.exec_())
