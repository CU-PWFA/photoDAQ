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
from PIL import Image
import ast
import libtiff
import time


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
    if root=='META':
        dirName = PATH + root + datePath
    else:
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
    fileName = str(instr) + '_' + str(dataSet) + '_' + shotNum
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
    if not os.path.isfile(PATH + 'META/DataSet_log.txt'):
        with open(PATH + 'META/DataSet_log.txt', 'w') as file:
            file.writelines("# Data sets taken\n")
        file.close()
        
        
def get_file_path():
    """ Load the path to the daq directory on this computer. 
    
    Returns
    -------
    data : string
        The path to the daq directory.
    """
    try:
        import var.var as var
        return var.path
    except:
        print('File Error: No var/var.py to specify the path to the daq.')
        return False


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
    dirName = get_dirName('IMAGE', dataSet)
    meta = data['meta']
    serial = meta['Serial number']
    fileName = get_fileName(serial, dataSet, shot)
    name = dirName + fileName + '.tiff' 
    
    raw = data['raw']
    width, height = meta['pixel']

    imageArray = np.frombuffer(bytes(raw), dtype=np.uint16).reshape(height, width) 

    tiff = libtiff.TIFF.open(name, mode='w')
    tiff.write_image(imageArray)
    tiff.close()  
    
    metaBYTE = str(meta).encode()
    metaBASE = str(base64.b64encode(metaBYTE), 'ascii')
    subprocess.call('tiffset -s 270 '+metaBASE+' '+name, shell=True)

def add_image_meta(fileName, meta):
    """ Save metadata into an existing tiff files description tag. 
    
    Parameters
    ----------
    fileName : string
        The full path and fileName of the tiff to save the image to.
    meta : dict
        The metadata dictionary for the image.
    """
    metaBYTE = str(meta).encode()
    metaBASE = str(base64.b64encode(metaBYTE), 'ascii')
    subprocess.call('tiffset -s 270 ' + metaBASE + ' ' + fileName, shell=True)


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
        serial = data['meta']['Serial number']
        fileName = get_fileName(serial, dataSet, shot)
        np.save(dirName + fileName, data)
        return True
    else:
        print('Saving Error: Settings have no metadata.')
        return False
    
def meta_IMAGE(dataset, serial, ts):
    """ Save the image meta data in a txt file. 
    
    Parameters
    ----------
    dataset : int
        The data set number.
    serial : int
        List of Cameras used in dataset by serial number
    ts : bool
        Records time stamp of each shot if True. 
        Does nothing if False.
    """
    metaName = get_dirName('META', dataset)+'meta_{}.txt'.format(dataset)
    f = open(metaName, 'r')
    contents = f.readlines()
    f.close()
    
    cnt = 0
    for ind in range(len(contents)):
        line = contents[ind]
        if line[0] == '#':
            cnt += 1
        if cnt == 3:
            contents.insert(ind, '    Camera :')
            for num in serial:
                ind+=1
                contents.insert(ind, '\n      {}'.format(num))
            contents.insert(ind+1, '\n\n')
            break
        
    if cnt != 3:
        contents.append('\n\n    Camera :')
        for num in serial:
            contents.append('\n      {}'.format(num))
        contents.append('\n\n')
    
    if ts:
        contents.append('# Time Stamp of Each Shot (year/month/day/hour/minute/second/microsecond)\n')
        dirName = get_dirName('IMAGE', dataset)
        for fileName in sorted( Gvar.list_files(dirName, 'tiff') ):
            im = Image.open(dirName+fileName)
            meta = im.tag[270][0]
            meta = base64.b64decode(meta) 
            meta = ast.literal_eval(str(meta, 'ascii'))
            
            contents.append('\nShot {}: {}'.format(meta['Shot number'], meta['Timestamp']))
    
    f = open(metaName, 'w')
    contents = ''.join(contents)
    f.write(contents)
    f.close()
    
def meta_TRACE(dataset, serial, ts):
    """Save the trace meta data in a txt file.
    
    Parameters
    ----------
    dataset : int
        The data set number
    serial : int
        List of O-scopes used in dataset by serial number
    ts : bool
        Records time stamp of each shot if True. 
        Does nothing if False.
    """
    metaName = get_dirName('META', dataset)+'meta_{}.txt'.format(dataset)
    f = open(metaName, 'r')
    contents = f.readlines()
    f.close()
      
    dirName = get_dirName('TRACE', dataset)      
    filName = sorted( Gvar.list_files(dirName, 'npy') )
    trace = load_TRACE(dirName+filName[0])
    chan = trace['meta']['Channel']
    
    cnt = 0
    for ind in range(len(contents)):
        line = contents[ind]
        if line[0] == '#':
            cnt += 1
        if cnt == 3:
            contents.insert(ind, '    Oscilliscope : ')
            contents.insert(ind+1, '\n      {}'.format(serial[0]))
            for key, elem in chan.items():
                ind+=1
                contents.insert(ind+1, '\n        {} : {}'.format(key, elem[1]))
            contents.insert(ind+2, '\n\n')
            break   
        
    if cnt != 3:
        contents.append('\n\n    Oscilliscope : ')
        contents.append('\n      {}'.format(serial[0]))
        for key, elem in chan.items():
            contents.append('\n        {} : {}'.format(key, elem[1]))
        contents.append('\n\n')
        
    if ts:
        contents.append('# Time Stamp of Each Shot (year/month/day/hour/minute/second/microsecond)\n')
        for file in filName:
            meta = load_TRACE(dirName+file)['meta']
            contents.append('\nShot {}: {}'.format(meta['Shot number'], meta['Timestamp']))
    
    f = open(metaName, 'w')
    contents = ''.join(contents)
    f.write(contents)      
    f.close()
    
def meta_SET(dataset, serial, ts):
    """Save the trace meta data in a txt file.
    
    Parameters
    ----------
    dataset : int
        The data set number
    serial : int
        List of O-scopes used in dataset by serial number
    ts : bool
        Records time stamp of each shot if True. 
        Does nothing if False.
    """
    metaName = get_dirName('META', dataset)+'meta_{}.txt'.format(dataset)
    f = open(metaName, 'r')
    contents = f.readlines()
    f.close()
    
    cnt = 0
    for ind in range(len(contents)):
        line = contents[ind]
        if line[0] == '#':
            cnt += 1
        if cnt == 3:
            contents.insert(ind, '    Power Supply : ')
            for val in serial:
                ind+=1
                contents.insert(ind, '\n      {}'.format(val))
            contents.insert(ind+1, '\n\n')
            break   
        
    if cnt != 3:
        contents.append('\n\n    Power Supply : ')
        for val in serial:
            contents.append('\n      {}'.format(val))
        contents.append('\n\n')
        
    if ts:
        dirName = get_dirName('SET', dataset)      
        filName = sorted( Gvar.list_files(dirName, 'npy') )
        contents.append('# Time Stamp of Each Shot (year/month/day/hour/minute/second/microsecond)\n')
        for file in filName:
            meta = load_TRACE(dirName+file)['meta']
            contents.append('\nShot {}: {}'.format(meta['Shot number'], meta['Timestamp']))
    
    f = open(metaName, 'w')
    contents = "".join(contents)
    f.write(contents)
    f.close()
    
def meta_TXT(desc, dataset):
    """Records meta data in txt file and then ends dataset
    """
    metaName = get_dirName('META', dataset)+'meta_{}.txt'.format(dataset)
    f = open(metaName, 'w')   
    f.write('# Description of Data Set\n\n   '+desc)
    f.write('\n\n# Devices Used')
                
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


def load_IMAGE(serial, dataSet, shot):
    """ Load an image from a given data set. 
    
    Parameters
    ----------
    serial : int
        The serial number of the instrument.
    dataSet : int
        The data set number.
    shot : int
        The shot number.
        
    Returns
    -------
    image : obj
        Pillow image object for the tiff.
    """
    dirName = get_dirName_from_dataset('IMAGE', dataSet)
    fileName = get_fileName(serial, dataSet, shot) + '.tiff'
    name = dirName + fileName
    image = Image.open(name)
    return image


def load_TRACE(fileName):
    """ Load a trace from a given data set.
    
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
    try:
        trace = np.load(fileName)
        return trace.item()
    except:
        print('Loading Error: The trace file could not be opened.')
        print('Looking in: ' + fileName)
        return False


def load_SET(instr, dataSet, shot):
    """ Load settings for a given data set.
    
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
    fileName = get_fileName(instr, dataSet, shot) + '.npy'
    try:
        settings = np.load(dirName + fileName)
        return settings.item()
    except:
        print('Loading Error: The settings file could not be opened.')
        return False
    

def decode_image_meta(image):
    """ Return the metadata dictionary from a pillow image object.
    
    Parameters
    ----------
    image : obj
        Pillow image object from a tiff.
        
    Returns
    -------
    meta : dict
        The meta data dictionary contained in the tiff image.
    """
    meta = image.tag_v2[270]
    # The second decodes goes from bytes to string
    meta = base64.b64decode(meta).decode()
    # Eval is insecure but this version is a little safer
    return ast.literal_eval(meta)

def convert_image(serial, dataSet, shot):
    """ Convert a 16bit image with 12bits of data to the 12bit data.
    
    The 16 bit image has 12 bit data in it and the 4 lsb are set to 0. This
    changes the file so the msb are set to zero meaning the pixel values are 
    the actual 12 bit values.
    
    Parameters
    ----------
    serial : int
        The serial number of the instrument.
    dataSet : int
        The data set number.
    shot : int
        The shot number.
    """
    image = load_IMAGE(serial, dataSet, shot)
    meta = decode_image_meta(image)
    data = image.getdata()
    data = np.reshape(np.array(np.array(data) / 16, dtype=np.uint16),
                      (image.height, image.width))
    im = Image.fromarray(data)
    # Save the new image
    dirName = get_dirName_from_dataset('IMAGE', dataSet)
    fileName = get_fileName(serial, dataSet, shot) + '.tiff'
    name = dirName + fileName
    im.save(name, compression='tiff_lzw')
    # Since pillow is apparently incabale of transferring tags
    add_image_meta(name, meta)
    
