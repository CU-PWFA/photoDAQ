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
        super().__init__(instr)
        self.sampleDelay = 0.05
        self.slave = "1>"
        self.axes  = [1, 2]
        
    def set_slave_axis(self, axes, slave):
        self.axes  = axes
        self.slave = slave
#        print('Controller: ' + str(slave) + ', Motors: ' + str(self.axes)) #Debugging
        
    def get_datatype(self):
        """ Return the type of data. """
        return "SET"
    
    def get_type(self):
        """ Return the instrument type. """
        return "NF8742"
    
    def get_settings(self):
        """Place the current settings on the NF8742 into the response queue."""
        
        settings = {}
        nf       = self.device
        x_position     = nf.get_position(self.axes[0], self.slave)
        y_position     = nf.get_position(self.axes[1], self.slave)
        velocity       = nf.get_velocity(self.axes[0], self.slave)
        acceleration   = nf.get_acceleration(self.axes[0], self.slave)
        x_home         = nf.get_home(self.axes[0], self.slave)
        y_home         = nf.get_home(self.axes[1], self.slave)
        
        
        settings       = {"x"          : x_position, 
                          "y"          : y_position,
                        "velocity"     : velocity, 
                        "acceleration" : acceleration, 
                        "x_home"       : x_home, 
                        "y_home"       : y_home}  
        return settings
        
    def capture_thread(self, r_queue, axis, slave = ""):
        """ Continually quieres the pressure gauge for the pressure. 
        
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

    def move_rel_x(self, x_dist):
        nf = self.device
        x_axis = self.axes[0]
        slave = self.slave
        nf.relative_move(x_axis, x_dist, slave)

    def move_rel_y(self, y_dist):
        nf = self.device
        y_axis = self.axes[1]
        slave = self.slave
        nf.relative_move(y_axis, y_dist, slave)

    def move_abs_x(self, x_pos):
        nf = self.device
        x_axis = self.axes[0]
        slave = self.slave
        nf.target_position(str(x_axis), str(x_pos), str(slave))

    def move_abs_y(self, y_pos):
        nf = self.device
        y_axis = self.axes[1]
        slave = self.slave
        nf.target_position(str(y_axis), str(y_pos), str(slave))
        
    def move_indef_vert(self, direction):
        nf = self.device
        axis = self.axes[1]
        slave = self.slave
#        if direction == "+":  # Debugging
#            print('up button clicked, controller = ' + str(slave) + ' motor = ' + str(axis))   
#        elif direction == "-":
#            print('down button clicked, controller = ' + str(slave) + ' motor = ' + str(axis))
        nf.indefinite_move(axis, direction, slave)

    def move_indef_horiz(self, direction):
        nf = self.device
        axis = self.axes[0]
        slave = self.slave
#        if direction == "+":   # Debugging
#            print('right button clicked, controller = ' + str(slave) + ' motor = ' + str(axis))
#        elif direction == "-":
#            print('left button clicked, controller = ' + str(slave) + ' motor = ' + str(axis))
        nf.indefinite_move(axis, direction, slave)

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

    def update_position(self):
        nf = self.device  
        axes = self.axes
        slave = self.slave
        x_pos_raw = nf.get_position(axes[0], slave)
        x_pos_split = x_pos_raw.split(">")
        x_pos_readback = x_pos_split[-1]
        y_pos_raw = nf.get_position(axes[1], slave)
        y_pos_split = y_pos_raw.split(">")
        y_pos_readback = y_pos_split[-1]
        rsp = daq.Rsp('driver', info={'x_pos_readback': x_pos_readback, 'y_pos_readback': y_pos_readback})
        self.r_queue.put(rsp)

    def update_home(self):
        nf = self.device
        axes = self.axes
        slave = self.slave
        x_home_readback = nf.get_home(axes[0], slave)
        y_home_readback = nf.get_home(axes[1], slave)
        rsp = daq.Rsp('driver', info={'x_home_readback': x_home_readback,
                                      'y_home_readback': y_home_readback})
        self.r_queue.put(rsp)
        
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
    
    def abort_motion(self):
        nf = self.device
        slave = self.slave
        nf.abort_motion(slave)

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

    def motor_check(self):
        nf = self.device
        slave = self.slave
        nf.motor_check(slave)

    def motor_type(self):
        # Function not fully working, needs some updates
        nf = self.device
#        slave = self.slave
#        for i in self.axes:
#            axis_ = self.axes[]
        motor = nf.get_motor()
        print(motor)

    def set_config(self):
        nf = self.device
        nf.config_behavior(2)

    def reset(self):
        nf = self.device
        slave = self.slave
        nf.reset(slave)

    def set_home_x(self, x_home):
        nf = self.device
        slave = self.slave
        x_axis = self.axes[0]
        nf.define_home(x_axis, x_home, slave)
        self.update_home()

    def set_home_y(self, y_home):
        nf = self.device
        slave = self.slave
        y_axis = self.axes[1]
        nf.define_home(y_axis, y_home, slave)
        self.update_home()

# -----------------------------------------------------------------------------