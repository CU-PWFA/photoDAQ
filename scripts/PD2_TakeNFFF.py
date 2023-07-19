#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 13:24:03 2023

@author: Valentina
"""

import numpy as np
import os
import sys
import time
sys.path.insert(0, "..")

import daq
import detect
import file

META_PATH = ''

def main(desc):
    """ Take a give dataset and check all shots."""
    DAQ = daq.Daq(broadcast=False, print_normal=True)
#    ID = check_log()
#    add_to_log(ID)
#    global META_PATH
#    META_PATH = file.get_dirName('META', '') + str(ID) + '.txt'
#    create_meta(desc)

    # Connect all devices we want to use
    devices = connect_instruments(DAQ)
    if devices is None:
        DAQ.close_daq()
        return
    NF, FF, sdg, TC, gauge = devices
    DAQ.create_dir_struct()
    time.sleep(5)
    print('Finished waiting 5s for instruments to connect')
    # Config any instrument settings that we want to make sure are correct
    config_instruments(DAQ, NF, FF)

    # Take the initial dataset
    instrs = {
            NF.serial: NF,
            FF.serial: FF,
            gauge.serial: gauge
            }
#    append_meta('Initial laser parameters:\t{:s}'.format(str(DAQ.dataset)))
    take_laser(desc, DAQ, instrs, adv=False)
    DAQ.close_daq()

def connect_instruments(DAQ):
    """ Connect all the instruments needed for the datasets. """
    # Detect and connect cameras
    print('Detecting cameras')
    cameras = detect.camera()
    if '18085415' in cameras:
        NF = cameras['18085415']
    else:
        print('NF camera (serial 18085415) not detected')
        return
    if '18085362' in cameras:
        FF = cameras['18085362']
    else:
        print('FF camera (serial 18085362) not detected')
        return
    print('Connecting cameras')
    DAQ.connect_instr(NF)
    DAQ.connect_instr(FF)
    # Detect and connect the spectrometer
    # spec = detect.spectrometers()
    # Detect and connect the power meter
    # TODO implement the power meter into the DAQ
    # Detect and connect to the XPS controller
    # Detect and connect the timing instruments
    print('Detecting signal delay generator')
    sdg = detect.SRSDG645()
    if '006494' in sdg:
        sdg = sdg['006494']
    else:
        print('Signal delay generator not detected')
        return
    print('Connecting signal delay generator')
    DAQ.connect_instr(sdg)
    print('Detecting serial devices')

    serials = detect.serial_ports()
    if '5573631333835150F150' in serials:
        TC = serials['5573631333835150F150']
    else:
        print('Timing controller not detected')
        return
    DAQ.connect_instr(TC)
    print('Connecting timing controller')

    if '55736313338351603181' in serials:
        gauge = serials['55736313338351603181']
    else:
        print('Vacuum Gauge not detected')
        return
    DAQ.connect_instr(gauge)
    print('Connecting vacuum gauge')

    return NF, FF, sdg, TC, gauge

def config_instruments(DAQ, NF, FF):
    DAQ.send_command(NF, 'set_gain', 4.0)
    DAQ.send_command(FF, 'set_gain', 12.0)

    DAQ.send_command(NF, 'set_shutter', 21.0)
    DAQ.send_command(FF, 'set_shutter', 10.0)

    DAQ.send_command(NF, 'set_trigger_settings', False)
    DAQ.send_command(FF, 'set_trigger_settings', False)

    DAQ.send_command(NF, 'set_height', 1200)
    DAQ.send_command(NF, 'set_width', 1200)
    DAQ.send_command(FF, 'set_height', 768)
    DAQ.send_command(FF, 'set_width', 1024)

    DAQ.send_command(NF, 'set_offsetX', 804)
    DAQ.send_command(NF, 'set_offsetY', 110)
    DAQ.send_command(FF, 'set_offsetX', 512)
    DAQ.send_command(FF, 'set_offsetY', 384)
    
def take_laser(desc, DAQ, instrs, adv=True, j=0):
    steps = 10
    sweep = get_sweep(instrs)
    DAQ.desc = desc
    DAQ.start_dataset(steps, instrs, sweep)
    # Wait for the DAQ to finish
    for i in range(steps*2):
        if DAQ.taking_data:
            time.sleep(0.1)
        elif not DAQ.taking_data:
            print('DAQ finished')
            time.sleep(0.25)
            break
    verify_data(take_laser, desc, DAQ, instrs, adv, steps, j)
    
def verify_data(func, desc, DAQ, instrs, adv, steps, j=0):
    dataset = DAQ.dataset
    good = True
    for serial, instr, in instrs.items():
        root = instr.data_type
        path = file.get_dirName(root, dataset)
        ending = file.get_file_ending(root)
        if serial== '55736313338351603181':
            for i in range(steps):
                address= 'ttyACM0'
                filename = file.get_fileName(address, dataset, i)
                ending= '.npy'
                if not os.path.isfile(path + filename + ending):
                    print('File {:s} is missing'.format(path+filename+ending))
                    good = False
        else:
            for i in range(steps):
                filename = file.get_fileName(serial, dataset, i)
                if not os.path.isfile(path + filename + ending):
                    print('File {:s} is missing'.format(path+filename+ending))
                    good = False
    if not good and j < 10:
        j += 1
        print('Dataset {:s} is missing shots, retaking for the {:d} time'.format(str(dataset), j))
        TC = DAQ.instr[DAQ.TC_serial]
        DAQ.send_command(TC, 'reset', steps)
        time.sleep(0.1)
        DAQ.send_command(TC, 'start')
        time.sleep(steps*0.1+0.1)
        func(desc, DAQ, instrs, adv, j)
    elif not good and i >=10:
        print('Maximum retakes exceeded, saving last dataset')
        if adv:
            DAQ.adv_dataset(desc)
    else:
        print('Dataset {:s} is checked and has all {:d} shots'.format(str(dataset), steps))
        if adv:
            DAQ.adv_dataset(desc)
def get_sweep(instrs):
    """ Turn the sweep part of the DAQ off, we handle that manually. """
    sweep = {}
    for serial, instr in instrs.items():
        sweep[serial] = {'sweep': False}
    return sweep
            
if __name__ == "__main__":
    args = sys.argv
    if len(args) == 2:
        desc = args[1]
    
        main(desc)
    else:
        print("Uasge: python PD2_TakeData.py <description>")
