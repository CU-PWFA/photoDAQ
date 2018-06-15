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
import numpy as np

###############################################################################
#   
#   The main DAQ loop that controls acquisiton and parameters
#   
#   
###############################################################################

def main(arg):
    # Set the save path for the data
    file.PATH = "/media/robert/Data_Storage/daq/"
    # Create a new data set number
    file.check_log() # Make sure the log exists, if it doesn't, create it
    dataSet = Gvar.getDataSetNum()
    file.add_to_log(dataSet)
    file.make_dir_struct('META', dataSet)
    
    # Create all the instrument classes
    instrInit = arg[0]
    instrAdr  = arg[1]
    instr = {}
    
    for i in range(len(instrInit)):
        name = instrInit[i]
        if name in INSTR:
            module = importlib.import_module('devices.' + name)
            instr_class = getattr(module, name)
            instr[name] = instr_class(instrAdr[i])
            # Create the directories to store output in
            file.make_dir_struct(INSTR[name]['dataType'], dataSet)
    
    # Setup some statistics functions
    failed = 0
    # Take a series of measurements
    script = importlib.import_module('scripts.' + arg[2])
    getattr(script, 'setup')(instr)
    startTime = time.clock()
    for i in range(arg[3]):
        shot = i+1
        for attempt in range(10):
            try:
                ret = getattr(script, 'measure')(i)
            except:
                print('Attempt', attempt, 'of measurement', i, 'failed.')
                failed += 1
                continue
            break
        
        if ret:
            for name in instr:
                meta = ret[name]['meta']
                meta['INSTR'] = name
                meta['ID'] = instr[name].ID
                meta['Serial number'] = instr[name].serialNum
                meta['Timestamp'] = Gvar.get_timestamp()
                meta['Data set'] = dataSet
                meta['Shot number'] = shot
                save = getattr(file, 'save_' + INSTR[name]['dataType'])
                if save(ret[name], dataSet, shot) == False:
                    break;
                
    endTime = time.clock()
    # Save the dataset metadata
    meta = Gvar.create_metadata(arg, startTime)
    file.save_meta(meta, dataSet)
    
    # Close all instruments to prepare for another dataset
    for name in instr:
        instr[name].close()
    
    print_stat(shot, failed, startTime, endTime)
    # Handle any post processing that needs to occur
    post_process(arg, dataSet)

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
    print('Total measurement time:                  %0.2f s' % elapsed)
    

def post_process(instr, dataSet):
    """ Complete normal post processing on the dataset. 
    
    Parameters
    ----------
    arg : array-like
        The arguments passed to main.
    dataSet : int
        The data set number.
    """
    # First correct the images to remove the padding to 16bit
    
    
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
