#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 22 12:38:53 2025

@author: valentina
"""

from PyQt6.QtCore import pyqtSlot, pyqtSignal, QTimer
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog
import os
import threading
from PyQt6.QtGui import QDoubleValidator

package_directory = os.path.dirname(os.path.abspath(__file__))
probe_ui_path = os.path.join(package_directory, "ProbeAttenuator.ui")
Ui_ProbePanel, QtBaseClass = uic.loadUiType(probe_ui_path)

class ProbePanel(QDialog, Ui_ProbePanel):
    data_acquired = pyqtSignal(object)
    device_connected = pyqtSignal()
    def __init__(self, parent, DAQ, instr):
        super().__init__(parent)

        self.setupUi(self)
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_position)

        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.updating = False
        self.connected = False
        
        self.data_acquired.connect(self.update_text)
        self.device_connected.connect(self.setup_window) 
        self.Stepp1Button.clicked.connect(self.set_step_p1)
        self.Step1Button.clicked.connect(self.set_step_1)
        self.Step10Button.clicked.connect(self.set_step_10)
        self.PlusButton.clicked.connect(self.move_plus)
        self.MinusButton.clicked.connect(self.move_minus)
        self.requestPosValue.returnPressed.connect(self.move_abs)
        self.requestPosValue.setValidator(QDoubleValidator())
        
        self.Percent1Button.clicked.connect(self.set_percent_1)
        self.Percent5Button.clicked.connect(self.set_percent_5)
        self.Percent10Button.clicked.connect(self.set_percent_10)
        self.PlusEnButton.clicked.connect(self.move_plus_en)
        self.MinusEnButton.clicked.connect(self.move_minus_en)
        self.requestEnValue.returnPressed.connect(self.move_abs_en)
        self.requestEnValue.setValidator(QDoubleValidator())

    
    def position_to_energy(self):
        current_pos_text = self.currentPosValue.text()
        current_pos = float(current_pos_text)
        print(current_pos)
        return current_pos*2
    
    def energy_to_position(self):
        current_percent_text = self.currentEnergyValue.text()
        current_percent = float(current_percent_text)
        return current_percent/2
   
    def energy_to_position_cal(self, current_percent):
        return current_percent/2

    def position_to_energy_cal(self, current_position):
        return current_position*2
           
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

    def poll_position(self):
       self.send_command('update_position1')

    @pyqtSlot()
    def setup_window(self):
        """ Perform setup after the controller connects. """
        # Eanble all the buttons and things
        self.requestPosValue.setEnabled(True)
        self.requestRev= 1
        self.send_command('update_status1')
        self.send_command('update_position1')
          
    @pyqtSlot(object)
    def update_text(self, rsp):
        if "pos_readback1" in rsp.info:
            pos = rsp.info['pos_readback1']
            self.currentPosValue.setText(str(pos))
    
            # ✅ Update energy display here
            energy = self.position_to_energy_cal(pos)
            self.currentEnergyValue.setText(f"{energy:.2f}")
    
        if "status1" in rsp.info:
            status = rsp.info["status1"]
            if hasattr(self, "statusLabel"):
                if "Ready" in status or "IDLE" in status:
                    self.statusLabel.setText("Ready")
                    self.statusLabel.setStyleSheet("color: green;")
                    self.poll_timer.stop()
            
#    @pyqtSlot(object)
#    def update_text(self, rsp):
#        if "pos_readback1" in rsp.info:
#            self.currentPosValue.setText(str(rsp.info['pos_readback1']))

    @pyqtSlot(bool)
    def set_step_p1(self):
        self.requestRev= 0.1

    @pyqtSlot(bool)
    def set_step_1(self):
        self.requestRev= 1

    @pyqtSlot(bool)
    def set_step_10(self):
        self.requestRev= 10

    @pyqtSlot(bool)
    def move_plus(self):
        self.move_stage_rev_plus()

    @pyqtSlot(bool)
    def move_minus(self):
        self.move_stage_rev_minus()
        
    @pyqtSlot(float)
    def move_stage_rev_plus(self):
        """ Move stage 1 to absolute or relative position 'pos' [deg]. """
        req_pos = self.requestRev
        self.statusLabel.setText("Moving...")
        self.statusLabel.setStyleSheet("color: orange;")
        self.poll_timer.start(100)
        self.send_command('move_stage1_rel', req_pos)
        self.send_command('update_status1')

    @pyqtSlot(float)
    def move_stage_rev_minus(self):
        """ Move stage 1 to absolute or relative position 'pos' [deg]. """
        req_pos = self.requestRev
        self.statusLabel.setText("Moving...")
        self.statusLabel.setStyleSheet("color: orange;")
        self.poll_timer.start(100)
        self.send_command('move_stage1_rel', -req_pos)
        self.send_command('update_status1')
    
    @pyqtSlot()
    def move_abs(self):
        """ Move stage 1 to absolute or relative position 'pos' [mm]. """
        try:
            req_pos = float(self.requestPosValue.text())
            self.statusLabel.setText("Moving...")
            self.statusLabel.setStyleSheet("color: orange;")
            self.poll_timer.start(100)
            self.send_command('move_stage1_abs', req_pos)
            self.send_command('update_status1')
        except ValueError:
            print("[move_abs] Invalid number entered.")

    @pyqtSlot(bool)
    def set_percent_1(self):
        self.requestRev_percent= 1

    @pyqtSlot(bool)
    def set_percent_5(self):
        self.requestRev_percent= 5

    @pyqtSlot(bool)
    def set_percent_10(self):
        self.requestRev_percent= 10

    @pyqtSlot(bool)
    def move_plus_en(self):
        self.move_stage_rev_plus_en()

    @pyqtSlot(bool)
    def move_minus_en(self):
        self.move_stage_rev_minus_en()

    @pyqtSlot(float)
    def move_stage_rev_plus_en(self):
        """ Move stage 1 to absolute or relative position 'pos' [deg]. """
        current_percent_text = self.currentEnergyValue.text()
        current_percent = float(current_percent_text)
        req_en = current_percent+ self.requestRev_percent
        req_pos = self.energy_to_position_cal(req_en)
        self.statusLabel.setText("Moving...")
        self.statusLabel.setStyleSheet("color: orange;")
        self.poll_timer.start(100)
        self.send_command('move_stage1_abs', req_pos)
        self.send_command('update_status1')

    @pyqtSlot(float)
    def move_stage_rev_minus_en(self):
        """ Move stage 1 to absolute or relative position 'pos' [deg]. """
        current_percent_text = self.currentEnergyValue.text()
        current_percent = float(current_percent_text)
        req_en = current_percent- self.requestRev_percent
        req_pos = self.energy_to_position_cal(req_en)
        self.statusLabel.setText("Moving...")
        self.statusLabel.setStyleSheet("color: orange;")
        self.poll_timer.start(100)
        self.send_command('move_stage1_abs', req_pos)
        self.send_command('update_status1')
    
    @pyqtSlot()
    def move_abs_en(self):
        """ Move stage 1 to absolute or relative position 'pos' [mm]. """
        try:
            req_en = float(self.requestEnValue.text())
            req_pos = self.energy_to_position_cal(req_en)
            self.statusLabel.setText("Moving...")
            self.statusLabel.setStyleSheet("color: orange;")
            self.poll_timer.start(100)
            self.send_command('move_stage1_abs', req_pos)
            self.send_command('update_status1')
        except ValueError:
            print("[move_abs] Invalid number entered.")
