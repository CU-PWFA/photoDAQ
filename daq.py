#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 15:51:37 2018

@author: robert
"""

import sys
import file
import importlib
import globalVAR as Gvar
import time

###############################################################################
#   
#   The main DAQ loop that controls acquisiton and parameters
#   
#   
###############################################################################

def main(arg):
    setup_daq()
    dataSet = Gvar.getDataSetNum()
    file.add_to_log(dataSet)
    file.make_dir_struct('META', dataSet)
    
    # Create all the instrument classes
    instrInit = arg[0]
    instrAdr  = arg[1]
    instr = {}
    
    for i in range(len(instrInit)):
        name = instrInit[i]
        connect_instr(name, instrAdr[i], instr)
        try:
            file.make_dir_struct(INSTR[name]['dataType'], dataSet)
        except:
            print('The directory structure couldnt be made, instrument:', name)
    
    # Setup some statistics functions
    failed = 0
    # Take a series of measurements
    script = importlib.import_module('scripts.' + arg[2])
    getattr(script, 'setup')(instr)
    startTime = time.clock()
    measure = getattr(script, 'measure')
    for i in range(arg[3]):
        shot = i+1
        failed += do_measurement(instr, measure, shot, dataSet)
                
    endTime = time.clock()
    # Save the dataset metadata
    meta = Gvar.create_metadata(arg, startTime)
    file.save_meta(meta, dataSet)
    
    # Close all instruments to prepare for another dataset
    for name in instr:
        instr[name].close()
    
    print_stat(shot, failed, startTime, endTime)
    # Handle any post processing that needs to occur
    post_process(instr, dataSet, shot)

def print_stat(i, failed, startTime, endTime):
    """ Print some information about the data set run.
    
    Parameters
    ----------
    shot : int
        The number of shots.
    failed : int
        The number of measurements that had to be retried.
    startTime : float
        The time measurement taking started.
    endTime : float
        The time the measurements stopped taking.
    """
    print('Total number of attempted measurements:  %d' % (i+failed))
    print('Number of successful measurements:       %d' % i)
    print('Total number of failed measurements:     %d' % failed)
    elapsed = endTime - startTime
    print('Total measurement time:                  %0.3f s' % elapsed)
    

def setup_daq():
    """ Setup everything necessary to run the daq. """
    # Set the save path for the data
    file.PATH = file.get_file_path()
    # Create a new data set number
    file.check_log() # Make sure the log exists, if it doesn't, create it
    
    
def connect_instr(name, adr, instr):
    """ Create an object for a passed instrument type and address.
    
    Parameters
    ----------
    name : string
        The name of the instrument, must be a key in INSTR.
    adr : string
        The address of the instrument, will be passed to the constructor.
    instr : dict
        The instrument dictionary to add the object to, is returned.
    """
    if name in INSTR:
        module = importlib.import_module('devices.' + name)
        instr_class = getattr(module, name)
        device = instr_class(adr)
        device.type = name
        try:
            instr[str(device.serialNum)] = device
        except:
            print('Could not connect to device:', name)
        return instr
def disconnect_instr(name, instr, device):
    """ Deletes an object for a passed instrument type and address.
    
    Parameters
    ----------
    name : string
        The name of the instrument, must be a key in INST.
    instr : dict
        The instrument dictionary to remove the object from, is returned.
    device : custom class of instrument. Device to be disconnected
    """
    if name in INSTR:
        device.close()
        del instr[str(device.serialNum)]
    return instr
        
        

def do_measurement(instr, measure, shot, dataSet, attempts=10):
    """ Carry out a single measurement and save the data from it. 
    
    Parameter
    ---------
    instr : dict
        The instrument dictionary.
    measure : func
        The function to call each measurement.
    shot : int
        The shot number.
    dataSet : int
        The data set number.
    attempts : int, optional
        The number of times to attempt each measurement.
        
    Returns
    -------
    failed : int
        The number of failed measurements.
    """
    failed = 0
    for attempt in range(10):
        try:
            ret = measure(shot)
        except:
            print('Attempt', attempt, 'of measurement', shot, 'failed.')
            failed += 1
            continue
        break
        
    if ret:
        for name in instr:
            meta = ret[name]['meta']
            meta['INSTR'] = instr[name].type
            meta['ID'] = instr[name].ID
            meta['Serial number'] = instr[name].serialNum
            meta['Timestamp'] = Gvar.get_timestamp()
            meta['Data set'] = dataSet
            meta['Shot number'] = shot
            save = getattr(file, 'save_' + INSTR[instr[name].type]['dataType'])
            if save(ret[name], dataSet, shot) == False:
                break;
    return failed


def post_process(instr, dataSet, shot):
    """ Complete normal post processing on the dataset. 
    
    Parameters
    ----------
    arg : array-like
        The arguments passed to main.
    dataSet : int
        The data set number.
    shot : int
        The number of shots.
    """
    print('Begin post processing')
    startTime = time.clock()
    # Run through every instrument and run any postprocessing necessary
    for name in instr:
        if instr[name].type == 'Camera':    
            # Correct the images to remove the the 4 lsb (added to get 16bits)
            serial = instr[name].serialNum
            for i in range(shot):
                file.convert_image(serial, dataSet, i+1)
    endTime = time.clock()
    elapsed = endTime - startTime
    print('Total post processing time:              %0.3f s' % elapsed)
    
    
# Store information about our various instruments
INSTR = {
        'KA3005P' : {
                'IOtype'    : 'out',
                'dataType'  : 'SET'
                },
        'TDS2024C' : {
                'IOtype'    : 'in',
                'dataType'  : 'TRACE'
                },
        'Camera'    : {
                'IOtype'    : 'in',
                'dataType'  : 'IMAGE'
                }
        }

if __name__ == "__main__":
    main(sys.argv)
