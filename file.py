#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 16:04:44 2018

@author: robert
"""

import os
import globalVAR as Gvar
import numpy as np

PATH = ''

def get_dirName(root, dataSet):
    """ Return the string describing the path to the current dataset directory.
    
    Parameters
    ----------
    root : string
        The name of the root directory, "META" for example.
    dataSet : int
        The data set number. 
        
    Returns
    -------
    dirName : string
        The path and directory name.
    """
    datePath = Gvar.get_date_path()
    dirName = PATH + root + datePath + str(dataSet) + '/'
    return dirName


def get_fileName(instr, dataSet, shot):
    """ Return the string describing the filename for an instrument and shot.
    
    Parameters
    ----------
    instr : string
        String giving the instrument name or ID.
    dataSet : int
        The data set number.
    shot : int
        The shot number.
    
    Returns
    -------
    fileName : string
        The name of the file to save the data in.
    """
    shotNum = Gvar.stringTIME(shot, 3)
    fileName = instr + '_' + str(dataSet) + '_' + shotNum
    return fileName


def check_log():
    """ If it doesn't exist, create the dataset log file. """
    if not os.path.exists(PATH + 'META/'):
        os.makedirs(PATH + 'META/')
        with open(PATH + 'META/DataSet_log.txt', 'w') as file:
            file.writelines("# Data sets taken\n")
        file.close()


def add_to_log(dataSet):
    """ Add the data set to the log file.
    
    Parameters
    ----------
    dataSet : int
        The data set number.
    """
    with open(PATH + 'META/DataSet_log.txt', 'a') as file:
        file.write(str(dataSet) + '\n')
    file.close()


def make_dir_struct(root, dataSet):
    """ Create the date directory structure for a given root directory.
    
    Parameters
    ----------
    root : string
        The name of the root directory, "META" for example.
    dataSet : int
        The data set number. 
    """
    dirName = get_dirName(root, dataSet)
    if not os.path.exists(dirName):
        os.makedirs(dirName)


def save_meta(meta, dataSet):
    """ Save the metadata file.
    
    Parameters
    ----------
    meta : dict
        The metadata dictionary.
    dataSet : int
        The data set number.
    """
    # XXX save the metadata as a numpy file for now, may change to text later
    dirName = get_dirName('META', dataSet)
    fileName = 'meta' + '_' + str(dataSet)
    np.save(dirName + fileName, meta)
    
    
def save_TRACE(data, dataSet, shot):
    """ Save an oscilloscope trace to a numpy file. 
    
    Parameters
    ----------
    data : dict
        The dictionary with a t array, y array, and meta dictionary.
    dataSet : int
        The data set number.
    shot : int
        The shot number.
    """
    if 't' in data and 'y' in data and 'meta' in data:
        dirName = get_dirName('TRACE', dataSet)
        fileName = get_fileName(data['meta']['INSTR'], dataSet, shot)
        np.save(dirName + fileName, data)
        return True
    else:
        print('Saving Error: Trace data does not have the correct structure.')
        return False


def save_SET(data, dataSet, shot):
    """ Save the settings of an instrument as a numpy file. 
    
    Parameters
    ----------
    data : dict
        The dictionary with a t array, y array, and meta dictionary.
    dataSet : int
        The data set number.
    shot : int
        The shot number.
    """
    if 'meta' in data:
        dirName = get_dirName('SET', dataSet)
        fileName = get_fileName(data['meta']['INSTR'], dataSet, shot)
        np.save(dirName + fileName, data)
        return True
    else:
        print('Saving Error: Settings have no metadata.')
        return False

