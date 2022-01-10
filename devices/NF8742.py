#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 09:54:33 2019

@author: keenan & jamie
"""

from devices.device import Device
import usb
import usb.core
import usb.util

class NF8742(Device):
    """ 
    Class to control New Focus picomotor drivers. 
    """
    def __init__(self, address):
        """ Create the usb device object for the driver.
        
        Parameters
        -----------
        address : int
            The port number of the control driver.
        """
        
        self.connect_driver(address)
        self.detect_slaves()
        self.set_config()
        self.flush()      
    
    def connect_driver(self, address):
        """ Connect to the driver. 
        
        Parameters
        ----------
        address : int
            The serial number of the control driver.
        """
        # Find all connected drivers and distinguish by serial number
        VID = 0x104d; PID = 0x4000
        
        controllers = usb.core.find(find_all = True, \
                                   idVendor = VID, idProduct = PID)
        for cont in controllers:
            cfg  = cont.get_active_configuration()
            intf = cfg[(0,0)]
            # Get endpoints
            ep_out = usb.util.find_descriptor(intf, custom_match=lambda e:
                     usb.util.endpoint_direction(e.bEndpointAddress) == \
                     usb.util.ENDPOINT_OUT)
            self.ep_out = ep_out
            if ep_out is None:
                print("Picomotor USB error, endpoint out is None.")
                self.connection_error = True
                return
            if ep_out.wMaxPacketSize != 64:
                print("Picomotor USB error, endpoint out packet size is not 64.")
                self.connection_error = True
                return
            ep_in = usb.util.find_descriptor(intf, 
                    custom_match=lambda e:
                        usb.util.endpoint_direction(e.bEndpointAddress) == \
                        usb.util.ENDPOINT_IN)
            self.ep_in = ep_in
            if ep_in is None:
                print("Picomotor USB error, endpoint in is None.")
                self.connection_error = True
                return
            if ep_in.wMaxPacketSize != 64:
                print("Picomotor USB error, endpoint in packet size is not 64.")
                self.connection_error = True
                return
            self.flush()
            # Get serial number
            ep_out.write(b"*IDN?\r")
            serial = ep_in.read(64).tobytes()
            serial = serial.decode().split()[-1]
            self.flush()
            if serial == address:
                self.nf = cont
                self.serialNum = self.ID = serial
            else:
                usb.util.dispose_resources(cont)
                print("No picomotor controller found at address {:s}".format(address))
                self.connection_error = True
                return
        

        # Set configuration and get interface
        self.cfg  = self.nf.get_active_configuration()
        self.intf = self.cfg[(0,0)]
    
    def flush(self):
        while True:
            try:
                self.ep_in.read(64, timeout = 10)
            except usb.core.USBError:
                break
            
    def close(self):
        usb.util.dispose_resources(self.nf)
    
    def detect_slaves(self):
        """ Detect and record the number of slaves controllers connected. """
        controllers = self.list_controllers()
        conflict = controllers[-1]
        if conflict == '1':
            print("Pico motor controllers on the same bus have an address conflict.")
            self.connection_error = True
        self.controllers = []
        for i in range(len(controllers)):
            if controllers[-i] == '1':
                self.controllers.append("{:d}>".format(i-1))
            
    def set_config(self):
        """ Set a default configuration on each controller. """
        for i in range(len(self.controllers)):
            self.config_behavior(3, self.controllers[i])
            self.save_settings(self.controllers[i])
       
    def pass_command(self, command, slave = ""):
        """ Send a command to the driver and get the response
        
        Parameters
        ----------
        command : string
            The command to pass to the driver (e.g. "*IDN?\r"). NOTE: all \
            commands must end in a carriage return (\r).
        slave : string, optional
            The slave driver to pass the command to (e.g. "2>"), default "".
            
        Returns:
        --------
        response : str
            The response of the driver, returns None if there is no response.
        """
        if command[-1] == '?':
            query = True
        else:
            query = False
            
        command = slave + command + "\r"
        command = command.encode()
#        print('command: ' + str(command)) # debugging
        self.ep_out.write(command)
        
        if query:
            
            try:
                response = self.ep_in.read(64).tobytes()
                response = response.decode()
                response = response.strip()
                self.flush()
#                print('response: ' + str(response)) #debugging
                return response
            except:
                print("NF8742: Expected response but received none.")
                print("Likely timeout or no motor connected.")
        else:
            self.flush()
            return
    
    def get_IDN(self, slave = ""):
        """ Get serial number of the driver. """
        IDN = self.pass_command("*IDN?", slave)
        IDN = IDN.strip()
        IDN = IDN.split()[-1]
        return IDN
    
    def restore_params(self, slave = "", Bin = 0):
        """ Restore parameters to previous settings.
        
        Parameters
        ----------
        Bin : int, optional
            Determines whether to restore the driver to factor settings (0)
            or previous saved settings (1), default = 0.
        """
        # NOTE: Need to reconnect after running this command
        self.pass_command("*RST", slave)
    
    def reset(self, slave = ""):
        """ Resets the controller and reload parameters last saved in non-
        volatile memory.
        """
        command  = "*RST"
        self.pass_command(command, slave)
    
    def abort_motion(self, slave = ""):
        """ Instantaneously stop motion. """
        self.pass_command("AB", slave)
        
    def set_acceleration(self, axis, accel = 100000, slave = ""):
        """ Set acceleration of motor.
        
        Parameters
        ----------
        axis : int, 1 to 4
            The axis/motor number.
        accel : int, optional
            The acceleration value in steps/s^2, default = 100000.
        """
        command = str(axis) + "AC" + str(accel)
        self.pass_command(command, slave)
    
    def get_acceleration(self, axis, slave = ""):
        """ Get the acceleration of a motor. """
        command = str(axis) + "AC?"
        accel = self.pass_command(command, slave)
        return accel
        
    def define_home(self, axis, home, slave = ""):
        """ Set the home position for an axis.
        
        Parameters
        ----------
        home : int, optional
            The home position in steps betweein +/- 2147483648, default = 0.
        """
        command = str(axis) + "DH" + str(home)
        self.pass_command(command, slave)
    
    def get_home(self, axis, slave = ""):
        """ Query the home position of an axis. """
        command = str(axis) + "DH?"
        home = self.pass_command(command, slave)
        return home
    
    def motor_check(self, slave = ""):
        """ Scan for motors connected to a controller and set the motor type. """
        self.pass_command("MC", slave)
    
    def motion_check(self, axis, slave = ""):
        """ Query if motion is done on an axis. """
        command = str(axis) + "MD?"
        check = self.pass_command(command, slave)
        return check
    
    def indefinite_move(self, axis, direction, slave = ""):
        """ Move indefinitely in a given direction.
        
        Parameters
        ----------
        direction : string
            "+" or "-" for the direction of motion.
        """
        command = str(axis) + "MV" + direction
        self.pass_command(command, slave)
        
    def target_position(self, axis, position = 0, slave = ""):
        """  Move motor to desired position.
        
        Parameters
        ----------
        axis : int
            From 1 to 4, specifies axis number.
        position : int, optional
            The position to move to in steps between +/- 2147483648, default 0.
        """
        command = str(axis) + "PA" + str(position) + "\r"
        self.pass_command(command, slave)
        
    def get_position(self, axis, slave = ""):
        """ Query the position of an axis. """
        command = str(axis) + "PA?"
        position = self.pass_command(command, slave)
        return position
    
    def relative_move(self, axis, distance = 0, slave = ""):
        """ Move motor by a relative amount.
        
        Parameters
        ----------
        distance: int, optional
            Relative distance in steps between +/- 2147483648, default is 0.
        """
     
        command = str(axis) + "PR" + str(distance)
        self.pass_command(command, slave)
        
    def relative_position(self, axis, slave = ""):
        """ Query the relative position of an axis. """
        command = str(axis) + "PR?"
        position = self.pass_command(command)
        return position
    
    def set_motor(self, axis, mtype, slave = ""):
        """ Manually set the motor type.
        
        Parameters
        ----------
        mtype : int
            The motor type either 0, 1, 2, or 3 for no motor, unknown motor, 
            tiny motor, or standard motor.
        """
        command = str(axis) + "QM" + str(mtype)
        self.pass_command(command, slave)
        
    def get_motor(self, slave = ""):
        """ Query the motor type of an axis. """
        command = "2QM?"
        mtype = self.pass_command(command, slave)
        return mtype
    
    def reset_cpu(self, slave = ""):
        """ Soft reset of the controller cpu. NOTE: Must reconnect after. """
        self.pass_command("RS", slave)
        
    def set_address(self, address = 1, slave = ""):
        """ Set the address of a controller.
        
        Parameters
        ----------
        address : int, optional
            Controller address between 1 and 31, default 1.
        """
        command = "SA" + str(address)
        self.pass_command(command, slave)
        
    def get_address(self, slave = ""):
        """ Query the address of a controller. """
        address = self.pass_command("SA?", slave)
        return address
    
    def scan(self, nn, slave = ""):
        """ Scan controllers on the RS-485 network. 1 or 2 will break picomotors.
        
        Parameters
        ----------
        nn : int, optional
            Scan parameters, 0 to scan. 1 to scan and resolve address conflicts
            starting with the lowest available address, and 2 to resolve 
            conflict addresses in sequential order with the master at address 1.
        """
        command = "SC" + str(nn)
        self.pass_command(command, slave)
            
    def list_controllers(self):
        """ Query the list of all controllers on an RS-485 network. """
        controllers = self.pass_command("SC?")
        controllers = int(controllers)
        return bin(controllers)
    
    def scan_status(self):
        """ Query status of a scan.
        
        Returns
        -------
        status : int
            0 or 1 for ongoing/finished
        """
        status = self.pass_command("SD?")
        return status
    
    def save_settings(self, slave = ""):
        """ Saves the controller settings in non-volatile memory, saves hostname, 
        IP model, IP address, subnet mask address, gateway address, 
        configuration register, motor type, desired velocity, and
        desired acceleration  .      
        """
        self.pass_command("SM", slave)
        
    def stop_motion(self, axis, slave = ""):
        """ Stop the motion of an axis using the current acceleration. """
        command = str(axis) + "ST"
        self.pass_command(command, slave)
        
    def get_error(self, slave = ""):
        """ Error message query.
        
        Returns
        -------
        error : the last error that occured
        """
        error = self.pass_command("TB?", slave)
        return error
    
    def get_error_code(self, slave = ""):
        """ Error code query
        
        Returns
        -------
        code : the last error code that occured
        """
        code = self.pass_command("TE?", slave)
        return code
    
    def get_actual_position(self, axis, slave = ""):
        """ Query the actual position of an axis (internal number of steps made
        by a controller relative to its position when the controller was 
        powered on).
        """
        command = str(axis) + "TP?"
        position = self.pass_command(command, slave)
        return position
    
    def set_velocity(self, axis, velocity = 2000, slave = ""):
        """ Set the velocity of a motor
        
        Parameters
        ----------
        velocity : int, optional
            The velocity to set in steps/sec between 1 and 2000, default 2000.
        """
        command = str(axis) + "VA" + str(velocity)
        self.pass_command(command, slave)
        
    def get_velocity(self, axis, slave = ""):
        """ Query the motor velocity. """
        command = str(axis) + "VA?"
        velocity = self.pass_command(command, slave)
        return velocity
    
    def get_firmware(self, slave = ""):
        """ Query controller model number and firmware version.
        
        Returns
        -------
        firmare : string
            The firmware version and model number of the controller.
        """
        firmware = self.pass_command("VE?", slave)
        return firmware
    
    def purge(self, slave  = ""):
        """ Purge all user settings in controller memory. """
        self.pass_command("XX", slave)
    
    def config_behavior(self, cfg, slave = ""):
        """ Configure the default behavior of some controllers's features.
        
        Parameters
        ----------
        cfg : int
            Configuration options:
                0 - Perform auto motor detection, check and set motor type 
                    automatically when commanded to move. Do not scan for 
                    motors connected to controllers upon reboot.
                1 - Do not perform auto motor detection on move. Do not scan
                    for motors connected to controllers upon reboot.
                2 - Perform auto motor detection check and set motor type 
                    automatically when commanded to move. Scan for motors
                    connected to controller upon power-up or reset.
                3 - Do not perform auto motor detection on move. 
                    Scan for motors connected to controller upon power-up or
                    reset.
        """
        command = "ZZ" + str(cfg)
        self.pass_command(command, slave)
    
    def get_config(self, slave = ""):
        """ Query the configuration of a controller.
        
        Returns
        -------
        cfg : int
            The configuration options either 0, 1, 2, or 3 as defined above.
        """
        cfg = self.pass_command("ZZ?", slave)
        return cfg