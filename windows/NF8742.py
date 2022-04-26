#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 08:57:56 2019

@author: keenan & jamie
"""

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import (pyqtSlot, QThread, pyqtSignal)
from PyQt4.QtGui import (QPixmap, QImage, QLabel)
import numpy as np
import threading
import os

package_directory = os.path.dirname(os.path.abspath(__file__))

qtCreatorFile = os.path.join(package_directory, "NF8742.ui")
Ui_NFWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

motor_names = {
        '1>': {1: 'M5 Horizontal',
               2: 'M5 Vertical',
               3: 'M4 Horizontal',
               4: 'M4 Vertical'
                },
        '2>': {1: 'Test Horizontal',
               2: 'Test Vertical',
               3: 'M2 Horizontal',
               4: 'M2 Vertical'
                },
        '3>': {1: 'NC',
               2: 'NC',
               3: 'NC',
               4: 'NC'
                },
        '4>': {1: 'M3 Horizontal',
               2: 'M3 Vertical',
               3: 'M6 Horizontal',
               4: 'M6 Vertical'
                },
        }

class NF8742Window(QtBaseClass, Ui_NFWindow):
    data_acquired = pyqtSignal(object)
    device_connected = pyqtSignal(object)
    recieved_settings = pyqtSignal(object)
    
    def __init__(self, parent, DAQ, instr):
        """ Create the parent class and add event handlers. 
        
        Parameters
        ----------
        parent : QtClass
            The parent window that creates this window.
        DAQ : DAQ class
            The class representing the DAQ.
        instr : instr object
            Object for an instrument.
        """
        
        QtBaseClass.__init__(self)
        Ui_NFWindow.__init__(parent)
        self.setupUi(self)
        
        # Add event handlers to all buttons
        self.data_acquired.connect(self.update_params)
        self.recieved_settings.connect(self.update_settings_window)
        self.device_connected.connect(self.setup_window) 
        self.selectButton.clicked.connect(self.select_driver)
        self.rightButton1_1.clicked.connect(self.positive_step1)
        self.leftButton1_1.clicked.connect(self.negative_step1)
        self.rightButton1_2.clicked.connect(self.positive_step2)
        self.leftButton1_2.clicked.connect(self.negative_step2)
        self.rightButton1_3.clicked.connect(self.positive_step3)
        self.leftButton1_3.clicked.connect(self.negative_step3)
        self.rightButton1_4.clicked.connect(self.positive_step4)
        self.leftButton1_4.clicked.connect(self.negative_step4)
        self.stepField1.valueChanged.connect(self.update_step_size)
        self.step1_1.clicked.connect(self.set_step1)
        self.step10_1.clicked.connect(self.set_step10)
        self.step100_1.clicked.connect(self.set_step100)
        self.step1000_1.clicked.connect(self.set_step1000)
        self.abortButton1_1.clicked.connect(self.abort_motion)
        self.abortButton1_2.clicked.connect(self.abort_motion)
        self.abortButton1_3.clicked.connect(self.abort_motion)
        self.abortButton1_4.clicked.connect(self.abort_motion)
        self.moveToButton1_1.clicked.connect(self.move_to1)
        self.moveToButton1_2.clicked.connect(self.move_to2)
        self.moveToButton1_3.clicked.connect(self.move_to3)
        self.moveToButton1_4.clicked.connect(self.move_to4)
        self.homeButton1_1.clicked.connect(self.home1)
        self.homeButton1_2.clicked.connect(self.home2)
        self.homeButton1_3.clicked.connect(self.home3)
        self.homeButton1_4.clicked.connect(self.home4)
        self.motorCheckButton1.clicked.connect(self.check_motors)
        self.resetButton1.clicked.connect(self.reset)
        self.motorSettingsButton1.clicked.connect(self.open_settings_window)
#        self.setVelocityButton.clicked.connect(self.set_velocity)
#        self.setAccelButton.clicked.connect(self.set_acceleration)
#        self.getErrorButton.clicked.connect(self.get_error)        

        # Grab references for controlling driver
        self.DAQ = DAQ
        self.serial = instr.serial
        self.queue = instr.output_queue
        self.instr = instr
        self.updating = False
        self.connected = False  
        self.slave = None
        self.step = 10
        
        self.settingsWindow = NF8742Settings(self)
        setWin = self.settingsWindow
        setWin.motorVelocity1.valueChanged.connect(self.set_motor1_vel)
        setWin.motorVelocity2.valueChanged.connect(self.set_motor2_vel)
        setWin.motorVelocity3.valueChanged.connect(self.set_motor3_vel)
        setWin.motorVelocity4.valueChanged.connect(self.set_motor4_vel)
        setWin.motorAcceleration1.valueChanged.connect(self.set_motor1_acc)
        setWin.motorAcceleration2.valueChanged.connect(self.set_motor2_acc)
        setWin.motorAcceleration3.valueChanged.connect(self.set_motor3_acc)
        setWin.motorAcceleration4.valueChanged.connect(self.set_motor4_acc)
        setWin.motorType1.currentIndexChanged.connect(self.set_motor1_typ)
        setWin.motorType2.currentIndexChanged.connect(self.set_motor2_typ)
        setWin.motorType3.currentIndexChanged.connect(self.set_motor3_typ)
        setWin.motorType4.currentIndexChanged.connect(self.set_motor4_typ)
        
        self.create_update_thread()
    
    def create_update_thread(self):
        """ Create a thread to poll the response queue and update the fields. """
        args = (self.queue, self.data_acquired.emit, self.device_connected.emit, self.recieved_settings.emit)
        thread = threading.Thread(target=self.update_thread, args=args)
        thread.setDaemon(True)
        thread.start()
        
    def update_thread(self, queue, update, setup, settings):
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
                setup(rsp)
            elif response == 'driver':
                update(rsp)
            elif response == 'settings':
                settings(rsp)
            queue.task_done()   
            
    def set_motor_names(self):
        names = motor_names[self.slave]
        self.motorLabel1_1.setText(names[1])
        self.motorLabel1_2.setText(names[2])
        self.motorLabel1_3.setText(names[3])
        self.motorLabel1_4.setText(names[4])
    
    def do_step(self, motor, direction):
        steps = self.step
        if direction == 'n':
            steps *= -1
        self.send_command('relative_move', motor, steps, self.slave)
        
    def move_to(self, motor, target):
        self.send_command('target_position', motor, target, self.slave)
        
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
    
    def motor_type_ind(self, motor_type):
        ind = int(motor_type.split('>')[-1])
        return ind
    
    def get_motor_settings(self):
        self.send_command("stop_stream")
        self.send_command("get_motor_settings", self.slave)
        self.send_command("start_stream")
        
    # Event Handlers
    ###########################################################################
    @pyqtSlot(object)
    def setup_window(self, rsp):
        """ Perform setup after the controller connects. """
        data = rsp.info
        self.slaves = data['slaves']
        self.controllers = data['controllers']
        for i in range(len(self.slaves)):
            text = "Id: {:s} (Address: {:s})".format(self.controllers[i], self.slaves[i])
            item = QtGui.QListWidgetItem(text, parent=self.controllerList)
            item.__key__ = self.slaves[i]
            item.__name__ = self.controllers[i]
        self.controllerList.addItem(item)
        self.slave = self.slaves[0]
        self.driverSerialText.setText('Driver #{:s}'.format(self.controllers[0]))
        self.send_command("set_slave", self.slave)
        self.set_motor_names()
        if self.settingsWindow.isVisible():
            self.get_motor_settings()

    @pyqtSlot()
    def start_stream(self):
        """ Start the camera stream and display it. """
        self.send_command('start_stream')   
        self.streaming = True
    
    @pyqtSlot()
    def select_driver(self):
        driver_item = self.controllerList.selectedItems()[0]
        self.slave = driver_item.__key__
        self.driverSerialText.setText('Driver #{:s}'.format(driver_item.__name__))
        self.send_command("set_slave", self.slave)
        self.set_motor_names()
        if self.settingsWindow.isVisible():
            self.get_motor_settings()
            
    @pyqtSlot(object)
    def update_params(self, rsp):
        data = rsp.info
        if data['pos1'] is not None:
            self.position1_1.setText(data['pos1'].split('>')[-1])
        if data['pos2'] is not None:
            self.position1_2.setText(data['pos2'].split('>')[-1])
        if data['pos3'] is not None:
            self.position1_3.setText(data['pos3'].split('>')[-1])
        if data['pos4'] is not None:
            self.position1_4.setText(data['pos4'].split('>')[-1])
            
    @pyqtSlot()
    def open_settings_window(self):
        self.settingsWindow.show()
        
    @pyqtSlot(object)
    def update_settings_window(self, rsp):
        data = rsp.info
        setWin = self.settingsWindow
        setWin.motorVelocity1.setValue(int(data['vel1'].split('>')[-1]))
        setWin.motorVelocity2.setValue(int(data['vel2'].split('>')[-1]))
        setWin.motorVelocity3.setValue(int(data['vel3'].split('>')[-1]))
        setWin.motorVelocity4.setValue(int(data['vel4'].split('>')[-1]))
        setWin.motorAcceleration1.setValue(int(data['acc1'].split('>')[-1]))
        setWin.motorAcceleration2.setValue(int(data['acc2'].split('>')[-1]))
        setWin.motorAcceleration3.setValue(int(data['acc3'].split('>')[-1]))
        setWin.motorAcceleration4.setValue(int(data['acc4'].split('>')[-1]))
        ind = self.motor_type_ind(data['typ1'])
        setWin.motorType1.setCurrentIndex(ind)
        ind = self.motor_type_ind(data['typ2'])
        setWin.motorType2.setCurrentIndex(ind)
        ind = self.motor_type_ind(data['typ3'])
        setWin.motorType3.setCurrentIndex(ind)
        ind = self.motor_type_ind(data['typ4'])
        setWin.motorType4.setCurrentIndex(ind)
            
    @pyqtSlot(int)
    def update_step_size(self, size):
        self.step = size
        
    @pyqtSlot()
    def set_step1(self):
        self.stepField1.setValue(1)
        
    @pyqtSlot()
    def set_step10(self):
        self.stepField1.setValue(10)
        
    @pyqtSlot()
    def set_step100(self):
        self.stepField1.setValue(100)
        
    @pyqtSlot()
    def set_step1000(self):
        self.stepField1.setValue(1000)
        
    @pyqtSlot()
    def positive_step1(self):
        self.do_step(1, 'p')
    
    @pyqtSlot()
    def negative_step1(self):
        self.do_step(1, 'n')
        
    @pyqtSlot()
    def positive_step2(self):
        self.do_step(2, 'p')
    
    @pyqtSlot()
    def negative_step2(self):
        self.do_step(2, 'n')
        
    @pyqtSlot()
    def positive_step3(self):
        self.do_step(3, 'p')
    
    @pyqtSlot()
    def negative_step3(self):
        self.do_step(3, 'n')
        
    @pyqtSlot()
    def positive_step4(self):
        self.do_step(4, 'p')
    
    @pyqtSlot()
    def negative_step4(self):
        self.do_step(4, 'n')
        
    @pyqtSlot()
    def move_to1(self):
        target = self.moveTo1_1.value()
        self.move_to(1, target)
    
    @pyqtSlot()
    def move_to2(self):
        target = self.moveTo1_2.value()
        self.move_to(2, target)
    
    @pyqtSlot()
    def move_to3(self):
        target = self.moveTo1_3.value()
        self.move_to(3, target)
        
    @pyqtSlot()
    def move_to4(self):
        target = self.moveTo1_4.value()
        self.move_to(4, target)
        
    @pyqtSlot()
    def abort_motion(self):
        self.send_command('abort_motion', self.slave)
        
    @pyqtSlot()
    def home1(self):
        self.send_command('define_home', 1, 0, self.slave)
        
    @pyqtSlot()
    def home2(self):
        self.send_command('define_home', 2, 0, self.slave)
        
    @pyqtSlot()
    def home3(self):
        self.send_command('define_home', 3, 0, self.slave)
        
    @pyqtSlot()
    def home4(self):
        self.send_command('define_home', 4, 0, self.slave)
    
    @pyqtSlot()
    def check_motors(self):
        self.send_command('motor_check')
        if self.settingsWindow.isVisible():
            self.get_motor_settings()
        
    @pyqtSlot()
    def reset(self):
        self.send_command('reset', self.slave)

    @pyqtSlot(int)
    def set_motor1_typ(self, typ):
        self.send_command('set_motor', 1, typ, self.slave)

    @pyqtSlot(int)
    def set_motor2_typ(self, typ):
        self.send_command('set_motor', 2, typ, self.slave)

    @pyqtSlot(int)
    def set_motor3_typ(self, typ):
        self.send_command('set_motor', 3, typ, self.slave)

    @pyqtSlot(int)
    def set_motor4_typ(self, typ):
        self.send_command('set_motor', 4, typ, self.slave)

    @pyqtSlot(int)
    def set_motor1_vel(self, vel):
        self.send_command('set_velocity', 1, vel, self.slave)

    @pyqtSlot(int)
    def set_motor2_vel(self, vel):
        self.send_command('set_velocity', 2, vel, self.slave)

    @pyqtSlot(int)
    def set_motor3_vel(self, vel):
        self.send_command('set_velocity', 3, vel, self.slave)

    @pyqtSlot(int)
    def set_motor4_vel(self, vel):
        self.send_command('set_velocity', 4, vel, self.slave)

    @pyqtSlot(int)
    def set_motor1_acc(self, acc):
        self.send_command('set_acceleration', 1, acc, self.slave)

    @pyqtSlot(int)
    def set_motor2_acc(self, acc):
        self.send_command('set_acceleration', 2, acc, self.slave)

    @pyqtSlot(int)
    def set_motor3_acc(self, acc):
        self.send_command('set_acceleration', 3, acc, self.slave)

    @pyqtSlot(int)
    def set_motor4_acc(self, acc):
        self.send_command('set_acceleration', 4, acc, self.slave)

#    @pyqtSlot()
#    def get_error(self):
#        self.send_command('get_error')

# ---------- Extra functions not currently being used -------------------------
#------------------------------------------------------------------------------
    
    @pyqtSlot()
    def list_controllers(self):
        self.send_command('list_controllers')
    
    @pyqtSlot()
    def scan_status(self):
        self.send_command('scan_status')

    @pyqtSlot()
    def query_address(self):
        self.send_command('query_address')

    @pyqtSlot()
    def get_config(self):
        self.send_command('get_config')        

    @pyqtSlot()
    def motor_type(self):
        self.send_command('motor_type')

    @pyqtSlot()
    def set_config(self):
        self.send_command('set_config')

# -----------------------------------------------------------------------------
        
qtCreatorFile = os.path.join(package_directory, "NF8742_Settings.ui")
Ui_NFSettingsWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class NF8742Settings(QtBaseClass, Ui_NFSettingsWindow):
    
    def __init__(self, parent):
        """ Create the parent class and add event handlers. 
        
        Parameters
        ----------
        parent : QtClass
            The parent window that creates this window.
        """
        QtBaseClass.__init__(self)
        Ui_NFSettingsWindow.__init__(parent)
        self.setupUi(self)
