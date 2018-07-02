import PyCapture2 as pc2
import numpy as np
import base_ui
import daq
import cv2
from PyQt4 import QtCore, QtGui
import liveView as lv
import file
import globalVAR as Gvar
import time
import importlib
import passive_daq as pd
# Dictionaries for the DAQ instruments
instr_serials = {'2.2 micron camera':17571186, 
                       '3.45 (2048x1536) micron camera':17583372,
                       '3.75 micron camera':17570564,
                       '3.45 (2448x2048) micron camera':17529184}
instr_dict = {'2.2 micron camera': "Camera", 
                       '3.45 (2048x1536) micron camera': "Camera",
                       '3.75 micron camera': "Camera",
                       '3.45 (2448x2048) micron camera': "Camera"}
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
def getSelectedCameras(ui):
    selectedList = []
def clearSelection(listWidget):
    for i in range(listWidget.count()):
        item = listWidget.item(i)
        listWidget.setItemSelected(item, False) 
def passDAQFunc(self):
	ui = self.PWFAui
    # Get number of shots to take
	nShots = int(ui.nShotsLineEdit.text())
	daq.setup_daq()
	dataSet = Gvar.getDataSetNum()
	file.add_to_log(dataSet)
	file.make_dir_struct('META', dataSet)
	# Create all the instrument classes
	instrInit = []
	instrAdr  = []
	for i in range(ui.selectedListWidget.count()):
		instrInit.append(self.instr_dict[ui.selectedListWidget.item(i).text()])
		instrAdr.append(self.instr_serials[ui.selectedListWidget.item(i).text()])
	for i in range(len(instrInit)):
		name = instrInit[i]
		try:
			file.make_dir_struct(daq.INSTR[name]['dataType'], dataSet)
		except:
			print('The directory structure couldn\'t be made, instrument:', name)
	failed = 0
	pd.setupCam(self.instr)
	startTime = time.clock()
	for i in range(nShots):
		shot = i + 1
		failed += daq.do_measurement(self.instr, pd.measureCam, shot, dataSet)
		ui.DAQProgress.setValue(shot/nShots * 100)
	endTime = time.clock()
	# Save the dataset metadata
	arg = [instrInit, instrAdr, 'cam_test', nShots, ui.DescriptionEdit.toPlainText()]
	meta = Gvar.create_metadata(arg, startTime)
	file.save_meta(meta, dataSet)
	attempts  = 'Total number of attempted measurements:  %d' % (shot+failed)
	success   = 'Number of successful measurements:       %d' % shot
	failedMes = 'Total number of failed measurements:     %d' % failed
	elapsed   = endTime - startTime
	timeMes   =  'Total measurement time:                 %0.3f s' % elapsed
	message = [attempts, success, failedMes, timeMes]
	for i in message:
		ui.PassDAQTextBrowser.append("\n" + i)
	daq.post_process(self.instr, dataSet, shot)
	ui.DAQProgress.setValue(0)
# DAQ UI classes
class UI(base_ui.Ui_DAQWindow):
    def center(self, DAQWindow):
        resolution = QtGui.QDesktopWidget().screenGeometry()
        DAQWindow.move((resolution.width() / 2) - \
                       (DAQWindow.frameSize().width() / 2),
                  (resolution.height() / 2) - \
                  (DAQWindow.frameSize().height() / 2)) 
    
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
    DAQWindow = DAQMainWindow()
    ui = UI()
    DAQWindow.PWFAui = ui
    DAQWindow.instr  = {}
    DAQWindow.instr_serials = instr_serials
    DAQWindow.instr_dict = instr_dict
    ui.setupUi(DAQWindow)
    ui.center(DAQWindow)
    DAQWindow.show()
    sys.exit(app.exec_())
