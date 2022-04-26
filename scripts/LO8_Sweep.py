#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 10:47:06 2022

@author: Robert

Script for moving the 2.2m translation stage and taking images at each point.
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

def main(start, stop, incr, desc):
    """ Run the sweep, does not include <stop> in the positions. """
    start = float(start)
    stop = float(stop)
    incr = float(incr)
    positions = np.arange(start, stop, incr)
    N = len(positions)
    DAQ = daq.Daq(broadcast=False, print_normal=True)
    ID = check_log()
    add_to_log(ID)
    global META_PATH
    META_PATH = file.get_dirName('META', '') + str(ID) + '.txt'
    create_meta(desc)
    
    # Connect all devices we want to use
    devices = connect_instruments(DAQ)
    if devices is None:
        DAQ.close_daq()
        return
    NF, FF, stage_cam, xps, sdg, TC = devices
    DAQ.create_dir_struct()
    # Handle the XPS directly rather than through the DAQ
    print('Connecting XPS motor controller')
    xps_dev = xps.device_cls(xps.address)
    time.sleep(5)
    print('Finished waiting 5s for instruments to connect')
    # Config any instrument settings that we want to make sure are correct
    config_instruments(DAQ, NF, FF, stage_cam)
    
    # Take the initial dataset
    pos = move_stage(positions[0], xps_dev)
    instrs = {
            NF.serial: NF,
            FF.serial: FF,
            }
    append_meta('Initial laser parameters:\t{:s}'.format(str(DAQ.dataset)))
    take_laser('Initial laser parameters', DAQ, instrs)
    
    # Move the stage and take a dataset at each position
    instrs = {
            stage_cam.serial: stage_cam,
            #FF.serial: FF,
            }
    for i in range(N):
        pos = move_stage(positions[i], xps_dev)
        step_desc = 'Step:\t{:d}\t{:0.3f}'.format(i+1, pos)
        append_meta('Step:\t{:0.3f}\t{:s}'.format(pos, str(DAQ.dataset)))
        take_step(step_desc, DAQ, instrs)
        adjust_gain()
    
    # Take the final dataset
    instrs = {
            NF.serial: NF,
            FF.serial: FF,
            }
    append_meta('Final laser parameters:\t{:s}'.format(str(DAQ.dataset)))
    take_laser('Final laser parameters', DAQ, instrs, adv=False)
    DAQ.close_daq()

def check_log():
    """ Create a log for each day that assigns a unique ID to each sweep. """
    dirName = file.get_dirName('META', '')
    # If the sweep log file doesn't exist for today, make it
    if not os.path.isfile(dirName + 'sweep_log.txt'):
        with open(dirName + 'sweep_log.txt', 'w') as f:
            f.writelines("# Sweeps taken\n")
        f.close()
        return 1
    # If it does exist, figure out which sweep this is
    else:
        with open(dirName + 'sweep_log.txt','r') as f:
            data = f.readlines()  
        f.close()
        sweepPrev = data[-1]
        return int(sweepPrev)+1
        
def add_to_log(ID):
    dirName = file.get_dirName('META', '')
    with open(dirName + 'sweep_log.txt', 'a') as f:
        f.write(str(ID) + '\n')
    f.close()

def create_meta(desc):
    with open(META_PATH, 'w') as f:
        f.writelines("# Sweep meta data\n{:s}\n".format(desc))

def append_meta(msg):
    with open(META_PATH, 'a') as f:
        f.write(str(msg) + '\n')
    f.close()

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
    if '17583372' in cameras:
        print('Wide FOV camera detected on translation stage')
        stage_cam = cameras['17583372']
    elif '17571186' in cameras:
        print('MO camera detected on translation stage')
        stage_cam = cameras['17571186']
    else:
        print('Stage camera (serial 18085362 or serial 17571186) not detected')
        return
    print('Connecting cameras')
    DAQ.connect_instr(NF)
    DAQ.connect_instr(FF)
    DAQ.connect_instr(stage_cam)
    # Detect and connect the spectrometer
    # spec = detect.spectrometers()
    # Detect and connect the power meter
    # TODO implement the power meter into the DAQ
    # Detect and connect to the XPS controller
    print('Detecting XPS motor controller')
    xps = detect.XPS()
    if '18308053' in xps:
        xps = xps['18308053']
    else:
        print('XPS motor controller not detected')
        return
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
    print('Connecting timing controller')
    DAQ.connect_instr(TC)
    return NF, FF, stage_cam, xps, sdg, TC

def config_instruments(DAQ, NF, FF, stage_cam):
    DAQ.send_command(NF, 'set_gain', 4.0)
    DAQ.send_command(FF, 'set_gain', 6.0)
    DAQ.send_command(NF, 'set_shutter', 30.0)
    DAQ.send_command(FF, 'set_shutter', 1.0)
    DAQ.send_command(stage_cam, 'set_shutter', 1.0)
    DAQ.send_command(NF, 'set_trigger_settings', True)
    DAQ.send_command(FF, 'set_trigger_settings', True)
    DAQ.send_command(stage_cam, 'set_trigger_settings', True)
    DAQ.send_command(NF, 'set_height', 1200)
    DAQ.send_command(NF, 'set_width', 1200)
    DAQ.send_command(FF, 'set_height', 768)
    DAQ.send_command(FF, 'set_width', 1024)
    DAQ.send_command(NF, 'set_offsetX', 684)
    DAQ.send_command(NF, 'set_offsetY', 168)
    DAQ.send_command(FF, 'set_offsetX', 512)
    DAQ.send_command(FF, 'set_offsetY', 384)

    
    if stage_cam.serial == '17583372':
        DAQ.send_command(stage_cam, 'set_gain', 9.0)
        DAQ.send_command(stage_cam, 'set_height', 1536)
        DAQ.send_command(stage_cam, 'set_width', 1536)
        DAQ.send_command(stage_cam, 'set_offsetX', 284)
        DAQ.send_command(stage_cam, 'set_offsetY', 0)
        
    if stage_cam.serial == '17571186':
        DAQ.send_command(stage_cam, 'set_gain', 3.0)
        DAQ.send_command(stage_cam, 'set_height', 972)
        DAQ.send_command(stage_cam, 'set_width', 1296)
        DAQ.send_command(stage_cam, 'set_offsetX', 648)
        DAQ.send_command(stage_cam, 'set_offsetY', 488)
        
        

def take_laser(desc, DAQ, instrs, adv=True, j=0):
    steps = 100
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
    
def take_step(desc, DAQ, instrs, adv=True, j=0):
    steps = 10
    sweep = get_sweep(instrs)
    DAQ.desc = desc
    DAQ.start_dataset(steps, instrs, sweep)
    # Wait for the DAQ to finish
    for i in range(steps*2):
        if DAQ.taking_data:
            #print(DAQ.taking_data)
            time.sleep(0.1)
        elif not DAQ.taking_data:
            print('DAQ finished')
            time.sleep(0.25)
            break
    verify_data(take_step, desc, DAQ, instrs, True, steps, j)
    
def move_stage(position, xps):
    xps.move_stage1_abs(position)
    cur_pos = xps.get_stage1_position()
    return cur_pos

def adjust_gain():
    pass

if __name__ == "__main__":
    args = sys.argv
    if len(args) == 5:
        start = args[1]
        stop = args[2]
        incr = args[3]
        desc = args[4]
    
        main(start, stop, incr, desc)
    else:
        print("Uasge: python LO8_Sweep.py <start[mm]> <stop[mm]> <increment[mm]> <description>")