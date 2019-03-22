#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 13:37:27 2019

@author: robert
"""

class Instr():
    """ Class used to represent a single instrument.
    
    This object can be passed around to provide a reference to all entities
    related to a single instrument. New instrumentss can be added easily by simply
    extending this class and pointing to all the right files. 
    """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The address of the instrument, this is instrument specific.
        """
        self.serial = None          # Serial number of the device, unique identifier
        self.address = address      # Address necessary for connecting device
        self.device_type = None     # The type of device it is
        self.data_type = None       # The data type used to describe device data
        self.process = None         # Reference to the process object
        self.response_process = None# Reference to the response process object
        self.command_queue = None   # The queue for sending commands to the device
        self.response_queue = None  # The queue for recieving responses from the device
        self.output_queue = None    # Queue for GUI/post processing to draw from
        self.device_cls = None      # Reference to the class for the device
        self.process_cls = None     # Reference to the class for the device process
        self.window_cls = None      # Reference to the GUI window class
        self.model = None           # The model of the device
        self.sweep_params = {}      # Parameters that can be swept on the device
        self.stream = None          # Is the device a triggered data device
        
    def disconnect(self):
        """ Removes all references to the queues and processes. """
        self.process = None
        self.response_process = None
        self.command_queue = None
        self.response_queue = None
        self.output_queue = None


class Camera(Instr):
    """ Class for FLIR cameras. """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The serial number of the camera.
        """
        super().__init__(address)
        import processes.Camera
        import devices.Camera
        import windows.camera
        
        self.serial = address
        self.device_type = 'Camera'
        self.data_type = 'IMAGE'
        self.device_cls = devices.Camera.Camera
        self.process_cls = processes.Camera.Camera
        self.window_cls = windows.camera.CameraWindow
        self.stream = True

    
class KA3005P(Instr):
    """ Class for KA3005P power supply. """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The port name for the serial connection.
        """
        super().__init__(address)
        import processes.KA3005P
        import devices.KA3005P
        import windows.KA3005P
        
        self.device_type = 'KA3005P'
        self.data_type = 'SET'
        self.device_cls = devices.KA3005P.KA3005P
        self.process_cls = processes.KA3005P.KA3005P
        self.window_cls = windows.KA3005P.PSWindow
        self.model = 'KA3005P'
        self.stream = False
        self.sweep_params = {
                'voltage' : {
                        'display' : 'Voltage',
                        'min' : 0.0,
                        'max' : 30.0,
                        'command' : 'set_voltage'
                        },
                'current' : {
                        'display' : 'Current',
                        'min' : 0.0,
                        'max' : 5.0,
                        'command' : 'set_current'
                        },
                }


class TDS2024C(Instr):
    """ Class for TDS2024C oscilloscope. """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The pyVisa address for the oscilloscope.
        """
        super().__init__(address)
        import processes.TDS2024C
        import devices.TDS2024C
        
        self.device_type = 'TDS2024C'
        self.data_type = 'TRACE'
        self.device_cls = devices.TDS2024C.TDS2024C
        self.process_cls = processes.TDS2024C.TDS2024C
        self.window_cls = None
        self.serial = address.split('::')[3]
        self.model = 'TDS2024C'
        self.stream = False


class HR4000(Instr):
    """ Class for HR4000 spectrometer. """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The serial number of the spectrometer.
        """
        super().__init__(address)
        import processes.HR4000
        import devices.HR4000
        import windows.HR4000
        
        self.serial = address
        self.device_type = 'HR4000'
        self.data_type = 'SPEC'
        self.device_cls = devices.HR4000.HR4000
        self.process_cls = processes.HR4000.HR4000
        self.window_cls = windows.HR4000.SpecWindow
        self.model = 'HR4000'
        self.stream = True


class SRSDG645(Instr):
    """ Class for SRSDG645 signal delay generator. """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The ip address of the signal delay generator.
        """
        super().__init__(address)
        import processes.SRSDG645
        import devices.SRSDG645
        import windows.SRSDG645
        
        self.device_type = 'SRSDG645'
        self.data_type = 'SET'
        self.device_cls = devices.SRSDG645.SRSDG645
        self.process_cls = processes.SRSDG645.SRSDG645
        self.window_cls = windows.SRSDG645.DGWindow
        self.model = 'SRSDG645'
        self.stream = False
        self.sweep_params = {
                'chA' : {
                        'display' : 'Ch A Delay',
                        'min' : 0.0,
                        'max' : 0.1,
                        'command' : 'set_chA_delay',
                        'decimals' : 12
                        },
                'chB' : {
                        'display' : 'Ch B Delay',
                        'min' : 0.0,
                        'max' : 0.1,
                        'command' : 'set_chB_delay',
                        'decimals' : 12
                        },
                'chC' : {
                        'display' : 'Ch C Delay',
                        'min' : 0.0,
                        'max' : 0.1,
                        'command' : 'set_chC_delay',
                        'decimals' : 12
                        },
                'chD' : {
                        'display' : 'Ch D Delay',
                        'min' : 0.0,
                        'max' : 0.1,
                        'command' : 'set_chD_delay',
                        'decimals' : 12
                        },
                }


class FRG700(Instr):
    """ Class for FRG700 vacuum gauge controller. """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The serial address of the arduino.
        """
        super().__init__(address)
        import processes.FRG700
        import devices.FRG700
        import windows.FRG700
        
        self.device_type = 'FRG700'
        self.data_type = 'SET'
        self.device_cls = devices.FRG700.FRG700
        self.process_cls = processes.FRG700.FRG700
        self.window_cls = windows.FRG700.GaugeWindow
        self.model = 'FRG700'
        self.stream = True


class FS304(Instr):
    """ Class for the 304FS turbomolecular pump. """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The serial address of the turbo pump.
        """
        super().__init__(address)
        import processes.FS304
        import devices.FS304
        import windows.FS304
        
        self.device_type = 'FS304'
        self.data_type = 'SET'
        self.device_cls = devices.FS304.FS304
        self.process_cls = processes.FS304.FS304
        self.window_cls = windows.FS304.PumpWindow
        self.model = 'FS304'
        self.stream = False

        
class TC(Instr):
    """ Class for arduino timing control unit. """
    def __init__(self, address):
        """ Initialize all the object attributes. 
        
        Parameters
        ----------
        address : string
            The serial address of the arduino.
        """
        super().__init__(address)
        import processes.TC
        import devices.TC
        import windows.TC
        
        self.device_type = 'TC'
        self.data_type = 'SET'
        self.device_cls = devices.TC.TC
        self.process_cls = processes.TC.TC
        self.window_cls = windows.TC.TCWindow
        self.model = 'TC'
        self.stream = True