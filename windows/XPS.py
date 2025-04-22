#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 11:24:44 2021

@author: jamie

Source module: https://github.com/pyepics/newportxps

"""

from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import QWidget  # or QMainWindow, etc.
import threading
import os
import glob
import sys
from types import SimpleNamespace

for f in glob.glob(os.path.expanduser('~/CU-PWFA/photoDAQ/windows'), recursive=True):
    sys.path.insert(0, f)
from ProbeAttenuator import ProbePanel

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "XPS.ui")
Ui_XPSWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class XPSWindow(QtBaseClass, Ui_XPSWindow):
    data_acquired = pyqtSignal(object)
    device_connected = pyqtSignal()

    
    def __init__(self, parent, DAQ, instr):
        QtBaseClass.__init__(self)
        Ui_XPSWindow.__init__(parent)
        self.setupUi(self)
        self.ProbeAttenuator.clicked.connect(self.open_probe_panel)

        
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.updating = False
        self.connected = False
        self.create_update_thread()

        


    def create_update_thread(self):
        """ Create a thread to poll the response queue and update the fields. """
        args = (self.queue, self.data_acquired.emit, self.device_connected.emit)
        thread = threading.Thread(target=self.update_thread, args=args)
        thread.setDaemon(True)
        thread.start()

    def update_thread(self, queue, update, setup):
        """ Wait for updated data to display. 
        
        Parameters
        ----------
        queue : queue
            The queue that the data is arriving on.
        callback : func
            The signal.emit to call to update the fields. 
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
                update(rsp)
            queue.task_done()

    @pyqtSlot()
    def open_probe_panel(self):
        self.probe_panel = ProbePanel(self, self.DAQ, self.instr)
        self.data_acquired.connect(self.probe_panel.update_text) 
        self.probe_panel.show()
        self.DAQ.send_command(self.instr, 'update_position1')


