#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 11:22:23 2019

@author: robert
"""

from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt5.QtGui import (QPixmap, QImage)
from PyQt5.QtWidgets import QLabel
import numpy as np
import threading
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "datasetInstr.ui")
Ui_InstrWidget, QtBaseClass = uic.loadUiType(qtCreatorFile)

class DatasetInstr(QtBaseClass, Ui_InstrWidget):
    remove = pyqtSignal(object)
    
    def __init__(self, parent, DAQ, instr):
        """ Create the parent class and add event handlers. 
        
        Parameters
        ----------
        parent : QtClass
            The parent window that creates this window.
        DAQ : DAQ class
            The class representing the DAQ.
        serial : string or int
            The serial number or string of the device the window is for.
        instr : instr object
            Object for an instrument.
        """
        QtBaseClass.__init__(self)
        Ui_InstrWidget.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all the buttons
        self.removeButton.clicked.connect(self.emit_remove)
        self.sweepCheck.stateChanged.connect(self.activate_fields)
        self.parameterField.currentIndexChanged.connect(self.update_fields)
        
        self.DAQ = DAQ
        self.serial = instr.serial
        self.instr = instr
        
        self.setup_fields()
    
    def setup_fields(self):
        """ Setup the fields in the item with their available values. """
        self.instrName.setText(self.serial)
        first = True
        for key, value in self.instr.sweep_params.items():
            self.parameterField.addItem(value['display'])
            # Set the initial spinbox min and max values
            if first:
                first = False
                self.startField.setMinimum(value['min'])
                self.startField.setMaximum(value['max'])
                self.stopField.setMinimum(value['min'])
                self.stopField.setMaximum(value['max'])
                if 'decimals' in value:
                    self.startField.setDecimals(value['decimals'])
                    self.stopField.setDecimals(value['decimals'])
                    
    def get_values(self):
        """ Get the values from the fields in the widget. 
        
        Returns
        -------
        value : dict
            The sweep parameters if there are any.
        """
        value = {}
        value['sweep'] = self.sweepCheck.isChecked()
        if value['sweep']:
            display = self.parameterField.currentText()
            for key, param in self.instr.sweep_params.items():
                if param['display'] == display:
                    value['parameter'] = key
                    break;
            value['start'] = self.startField.value()
            value['stop'] = self.stopField.value()
            value['step'] = self.stepField.value()
            value['command'] = param['command']
        return value
        
    # Event Handlers
    ###########################################################################
    @pyqtSlot()
    def emit_remove(self):
        """ Emit the remove signal when the button is pushed. """
        self.remove.emit(self.instr)
        
    @pyqtSlot(int)
    def activate_fields(self, check):
        """ Activate the sweep fields. 
        
        Parameters
        ----------
        check : int
            The value of the checkbox that was checked. 
        """
        if self.sweepCheck.isChecked():
            self.parameterField.setEnabled(True)
            self.startField.setEnabled(True)
            self.stopField.setEnabled(True)
            self.stepField.setEnabled(True)
        else:
            self.parameterField.setEnabled(False)
            self.startField.setEnabled(False)
            self.stopField.setEnabled(False)
            self.stepField.setEnabled(False)
            
    @pyqtSlot(int)
    def update_fields(self, ind):
        """ Update the allowed min and max values of the start and stop fields.
    
        Parameters
        ----------
        ind : int
            The index of the parameter combo box.
        """
        text = self.parameterField.itemText(ind)
        for key, value in self.instr.sweep_params.items():
            if value['display'] == text:
                self.startField.setMinimum(value['min'])
                self.startField.setMaximum(value['max'])
                self.stopField.setMinimum(value['min'])
                self.stopField.setMaximum(value['max'])
                if 'decimals' in value:
                    self.startField.setDecimals(value['decimals'])

