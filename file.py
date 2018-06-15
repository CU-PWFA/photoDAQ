#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 16:04:44 2018

@author: robert
"""

import os
import globalVAR as Gvar
import numpy as np
import PyCapture2 as pc2
import base64
import subprocess


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


def get_dirName_from_dataset(root, dataSet):
    """ Return a string of the directory structure for a given data set number.
    
    Parameters
    ----------
    root : string
        The name of the root directory, "META" for example.
    dataSet : int
        The data set number.
        
    Returns
    -------
    path : string
        A string with the path from the top directory to the dataset.
    """
    dataSet = str(dataSet)
    year = int('20'+dataSet[0:2])
    month = Gvar.stringTIME(int(dataSet[2:4]))
    day = Gvar.stringTIME(int(dataSet[4:6]))
    path = (PATH + root + '/year_{}/month_{}/day_{}/'.format(year, month, day)
            + str(dataSet) + '/')
    return path


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

# Save functions
#------------------------------------------------------------------------------

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
    

def save_IMAGE(data, dataSet, shot):
    """ Save an image to a tiff file with LZW compression. 
    
    Parameters
    ----------
    data : dict
        The dictionary with image (PyCapture2.Image object) and meta dict.
    dataSet : int
        The data set number.
    shot : int
        The shot number.
    """
    if 'image' in data and 'meta' in data and hasattr(data['image'], 'save'):
        dirName = get_dirName('IMAGE', dataSet)
        fileName = get_fileName(str(data['meta']['Serial number']), dataSet, shot)
        imgFormat = pc2.IMAGE_FILE_FORMAT.TIFF
        data['image'].save(bytes(dirName + fileName, 'utf-8'), imgFormat)
        metaBYTE = str(data['meta']).encode()
        metaBASE = str(base64.b64encode(metaBYTE), 'ascii')
        subprocess.call('tiffset -s 270 '+metaBASE+' '+dirName + fileName, shell=True)
        return True
    else:
        print('Saving Error: Image data does not have the correct structure.')
        return False


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

# Load functions
#------------------------------------------------------------------------------

def load_meta(dataSet):
    """ Load the metadata for a given data set.
    
    Parameters
    ----------
    dataSet : int
        The data set number.
        
    Returns
    -------
    meta : dict
        The metadata dictionary read from the file. 
    """
    dirName = get_dirName_from_dataset('META', dataSet)
    fileName = 'meta' + '_' + str(dataSet) + '.npy'
    try:
        meta = np.load(dirName + fileName)
        return meta.item()
    except:
        print('Loading Error: The metadata file could not be opened.')
        return False


def load_TRACE(instr, dataSet, shot):
    """ Load the metadata for a given data set.
    
    Parameters
    ----------
    instr : string
        The instrument name.
    dataSet : int
        The data set number.
    shot : int
        The shot number.
        
    Returns
    -------
    trace : dict
        The trace dictionary.
    """
    dirName = get_dirName_from_dataset('TRACE', dataSet)
    shotNum = Gvar.stringTIME(shot, 3)
    fileName = instr + '_' + str(dataSet) + '_' + shotNum + '.npy'
    try:
        trace = np.load(dirName + fileName)
        return trace.item()
    except:
        print('Loading Error: The trace file could not be opened.')
        print('Looking in: ' + dirName + fileName)
        return False


def load_SET(instr, dataSet, shot):
    """ Load the metadata for a given data set.
    
    Parameters
    ----------
    instr : string
        The instrument name.
    dataSet : int
        The data set number.
    shot : int
        The shot number.
        
    Returns
    -------
    settings : dict
        The settings dictionary.
    """
    dirName = get_dirName_from_dataset('SET', dataSet)
    shotNum = Gvar.stringTIME(shot, 3)
    fileName = instr + '_' + str(dataSet) + '_' + shotNum + '.npy'
    try:
        settings = np.load(dirName + fileName)
        return settings.item()
    except:
        print('Loading Error: The settings file could not be opened.')
        return False
    
