#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 10:17:00 2019

@author: cu-pwfa
"""
from processes.streamProcess import StreamProcess
import daq
import time
class NF8742(StreamProcess):
    """ Process class for the NF8742. """
    def __init__(self, instr):
        """ For parameters see the parent method. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        self.sampleDelay = 0.05
        super().__init__(instr)
    
    def connect_info(self):
        """ Gather data for the UI to use. """
        nf = self.device
        slaves = nf.controllers
        controllers = []
        for slave in slaves:
            controllers.append(nf.get_IDN(slave))
            
        data = {'slaves': slaves,
                'controllers': controllers,
                }
        return data
    
    def get_motor_settings(self, slave):
        nf = self.device
        data = {'vel1': nf.get_velocity(1, slave),
                'acc1': nf.get_acceleration(1, slave),
                'typ1': nf.get_motor(1, slave),
                'vel2': nf.get_velocity(2, slave),
                'acc2': nf.get_acceleration(2, slave),
                'typ2': nf.get_motor(2, slave),
                'vel3': nf.get_velocity(3, slave),
                'acc3': nf.get_acceleration(3, slave),
                'typ3': nf.get_motor(3, slave),
                'vel4': nf.get_velocity(4, slave),
                'acc4': nf.get_acceleration(4, slave),
                'typ4': nf.get_motor(4, slave),
                }
        response = 'settings'
        rsp = daq.Rsp(response, info=data)
        self.r_queue.put(rsp)
    
    def set_slave(self, slave):
        self.slave = slave
        #print('Controller: ' + str(slave)) #Debugging
        
    def get_datatype(self):
        """ Return the type of data. """
        return "SET"
    
    def get_type(self):
        """ Return the instrument type. """
        return "NF8742"
    
    def get_settings(self):
        """Place the current settings on the NF8742 into the response queue."""
        nf = self.device
        settings = {
                'pos1': nf.get_actual_position(1, self.slave),
                'pos2': nf.get_actual_position(2, self.slave),
                'pos3': nf.get_actual_position(3, self.slave),
                'pos4': nf.get_actual_position(4, self.slave),
                }
        return settings
        
    def capture_thread(self, r_queue):
        """ Continually quieres the controller for motor positions. 
        
        Parameters
        ----------
        r_queue : mp.Queue
            The response queue to place the pressure in.
        """
        while self.streaming:
            raw = self.get_settings()
            response = 'driver'
            rsp = daq.Rsp(response, info=raw)
            self.r_queue.put(rsp)
            time.sleep(self.sampleDelay)

    def set_vel(self, vel):
        nf = self.device
        slave = self.slave
        for axis in self.axes:
            nf.set_velocity(axis, vel, slave)
        self.update_vel()

    def set_accel(self, accel):
        nf = self.device
        slave = self.slave
        for axis in self.axes:
            nf.set_acceleration(axis, accel, slave)
        self.update_accel()
        
    def update_vel(self):
        nf = self.device
        axes = self.axes
        slave = self.slave
        raw_velocity = nf.get_velocity(axes[0], slave)
        split_velocity = raw_velocity.split(">")
        velocity_readback = split_velocity[-1]
        rsp = daq.Rsp('driver', info={'velocity_readback': velocity_readback})
        self.r_queue.put(rsp)

    def update_accel(self):
        nf = self.device
        axes = self.axes
        slave = self.slave
        raw_accel = nf.get_acceleration(axes[0], slave)
        split_accel = raw_accel.split(">")
        acceleration_readback = split_accel[-1]
        rsp = daq.Rsp('driver', info={'acceleration_readback': acceleration_readback})
        self.r_queue.put(rsp)

    def get_error(self):
        nf = self.device
        slave = self.slave
        error = nf.get_error(slave)
        print(error)
        
# ----------- Extra functions not currently being used ------------------------
# -----------------------------------------------------------------------------

    def start_scan(self):
        nf = self.device
        nf.scan(2)

    def list_controllers(self):
        nf = self.device
        lst = nf.list_controllers()
        print(lst)   

    def scan_status(self):
        nf = self.device
        status = nf.scan_status()
        print(status)
    
    def query_address(self):
        nf = self.device
        slave = self.slave
        address = nf.get_address(slave)
        print(address)

    def get_config(self):
        nf = self.device
        slave = self.slave
        config = nf.get_config(slave)
        if config[-1] == "0":
            print("0: Perform auto motor detection, check and set motor type\
                  automatically when commanded to move. Do not scan for\
                  motors connected to controllers upon reboot")
        elif config[-1] == "1":
            print("1: Do not perform auto motor detection on move. Do not scan \
                    for motors connected to controllers upon reboot")
        elif config[-1] == "2":
            print("Perform auto motor detection check and set motor type \
                  automatically when commanded to move. Scan for motors \
                    connected to controller upon power-up or reset")
        elif config[-1] == "3":
            print("Do not perform auto motor detection on move. \
                  Scan for motors connected to controller upon power-up or \
                    reset")

    def motor_type(self):
        # Function not fully working, needs some updates
        nf = self.device
#        slave = self.slave
#        for i in self.axes:
#            axis_ = self.axes[]
        motor = nf.get_motor()
        print(motor)

# -----------------------------------------------------------------------------