#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 20 17:31:03 2019

@author: robert
"""

import instrInfo
import PyCapture2 as pc2
import visa
import seabreeze.spectrometers as sb
import os
import serial.tools.list_ports as prtlst


def all_instrs():
    """ Detect all the available instruments. 
    
    Returns
    -------
    instrs : array of instr objects
        All of the detected instruments connected to the system.
    """
    instrs = camera()
    # This syntax juast appends to the dictionary
    instrs = {**instrs, **pyvisa()}
    instrs = {**instrs, **spectrometer()}
    instrs = {**instrs, **SRSDG645()}
    instrs = {**instrs, **serial_ports()}
    return instrs


def camera():
    """ Detect all connected FLIR cameras. 
    
    Returns
    -------
    instrs : array of instr objects
        All of the detected Cameras in the system.
    """
    instrs = {}
    cams = pc2.BusManager().discoverGigECameras()
    for cam in cams:
        serial = str(cam.serialNumber)
        instr = instrInfo.Camera(serial)
        instr.model = str(cam.modelName, 'utf-8')
        instrs[serial] = instr
    return instrs


def pyvisa():
    """ Detect all instruments connected through visa. 
    
    Returns
    -------
    instrs : array of instr objects
        All of the detected visa instruments in the system.
    """
    instrs = {}
    rm = visa.ResourceManager('@py')
    visainstrs = rm.list_resources()
    for name in visainstrs:
        # This is the id for our TDS2024C oscilloscope
        if name == 'USB0::1689::934::C046401::0::INSTR':
            instr = instrInfo.TDS2024C(name)
            instrs[instr.serial] = instr
    return instrs


def spectrometer():
    """ Detect all oceanview spectrometers.
    
    Returns
    -------
    instrs : array of instr objects
        All of the detected spectrometers in the system.
    """
    instrs = {}
    spectrometers = sb.list_devices()
    for spec in spectrometers:
        serial = spec.serial
        if spec.model == 'HR4000':
            instr = instrInfo.HR4000(serial)
            instr.model = spec.model
            instrs[serial] = instr
    return instrs


def SRSDG645():
    """ Detect if the SRSDG645 is connected. 
    
    Returns
    -------
    instrs : array of instr objects
        Will have a single element if the SDG is detected.
    """
    instrs = {}
    ret = os.system("ping -c 1 169.254.248.180")
    if ret == 0:
        instr = instrInfo.SRSDG645('169.254.248.180')
        instr.model = 'DG645'
        instr.serial = '006494'
        instrs[instr.serial] = instr
    return instrs


def serial_ports():
    """ Find all the instruments connected to serial ports.
    
    Returns
    -------
    instrs : array of instr objects
        All of the detected serial instruments.
    """
    # Serial numbers come from the instr and should be unique
    instrs = {}
    pts = prtlst.comports()
    for pt in pts:
        serial = pt.serial_number
        vid = pt.vid
        pid = pt.pid
        if serial == '55736313338351603181':
            instr = instrInfo.FRG700(pt.device)
            instr.serial = serial
            instrs[instr.serial] = instr
        if serial == 'NT2009101400' or serial == 'A02014090305':
            instr = instrInfo.KA3005P(pt.device)
            instr.serial = serial
            instrs[instr.serial] = instr
        if vid == 1659 and pid == 8963:
            instr = instrInfo.FS304(pt.device)
            instr.serial = pt.device
            instrs[instr.serial] = instr
    return instrs

