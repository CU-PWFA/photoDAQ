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
    for name in instrInit:
        if name in INSTR:
            module = importlib.import_module('devices.' + name)
            instr_class = getattr(module, name)
            instr[name] = instr_class(instrAdr[name])
            # Create the directories to store output in
            file.make_dir_struct(INSTR[name]['dataType'], dataSet)
    
    # Take a series of measurements
    script = importlib.import_module('scripts.' + arg[2])
    getattr(script, 'setup')(instr)
    startTime = Gvar.get_timestamp()
    for i in range(arg[3]):
        shot = i+1
        ret = getattr(script, 'measure')(i)
        for name in instr:
            meta = ret[name]['meta']
            meta['INSTR'] = name
            meta['ID'] = instr[name].ID
            meta['Timestamp'] = Gvar.get_timestamp()
            meta['Data set'] = dataSet
            meta['Shot number'] = shot
            save = getattr(file, 'save_' + INSTR[name]['dataType'])
            if save(ret[name], dataSet, shot) == False:
                break;
                
    # Save the dataset metadata
    meta = Gvar.create_metadata(arg, startTime)
    file.save_meta(meta, dataSet)
    
    # Close all instruments to prepare for another dataset
    for name in instr:
        instr[name].close()


# Store information about our various instruments
INSTR = {
        'KA3005P' : {
                'IOtype'    : 'out',
                'dataType'  : 'SET'
                },
        'TDS2024C' : {
                'IOtype'    : 'in',
                'dataType'  : 'TRACE'
                }
        }
if __name__ == "__main__":
    main(sys.argv)
