#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 15:51:37 2018

@author: robert
"""

import os
import sys
import file
import importlib
import globalVAR as Gvar
import time
import threading
import multiprocessing as mp
import PyCapture2 as pc2
import visa
import serial.tools.list_ports as prtlst
import serial as ser
import seabreeze.spectrometers as sb
###############################################################################
#   
#   The main DAQ class that controls acquisiton and parameters
#   
#   
###############################################################################

class Daq():
    """ Main daq class, handles instrument and thread/process managment. """
    def __init__(self, desc=None):
        # Store information about our various instruments
        """
        Parameters
        ----------
        desc : str
            Description of data set
        """
        # TODO I don't think IOtype is used at all anymore
        # SET saves an arbitrary dictionary, good for simple stuff
        self.INSTR = {
                'KA3005P'   : {
                            'IOtype'    : 'out',
                            'dataType'  : 'SET'
                            },
                'TDS2024C'  : {
                            'IOtype'    : 'in',
                            'dataType'  : 'TRACE'
                            },
                'Camera'    : {
                            'IOtype'    : 'in',
                            'dataType'  : 'IMAGE'
                            },
                'HR4000'    : {
                            'IOtype'    : 'in',
                            'dataType'  : 'SPEC'
                            },
                'SRSDG645'  : {
                            'IOtype'    : 'in',
                            'dataType'  : 'DELAY'
                            },
                'FRG700'    : {
                            'IOtype'    : 'in',
                            'dataType'  : 'SET'
                            }
                }
        self.instr = {}
        self.procs = {}
        self.s_procs = {}
        self.command_queue = {}
        self.save_queue = {}
        self.response_queue = {}
        self.max_out_queue_size = 10000
        self.max_command_queue_size = 10000
        self.max_response_queue_size = 1000
        self.desc = desc
        # Setup the daq
        self.setup_daq()
        
    def print_stat(self, i, failed, startTime, endTime):
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
    
    def setup_daq(self):
        """ Setup everything necessary to run the daq. """
        # It isn't safe to fork multithreaded processes
        # However you can't spawn if threads are already created
        # Apparently forking a multithreaded process can cause deadlock because a process can get a lock and then die with it...
        # If the code starts freezing when instruments are disconnected - this might be the problem
        #mp.set_start_method('spawn')
        # Set the save path for the data
        file.PATH = file.get_file_path()
        file.check_log() # Make sure the log exists, if it doesn't, create it
        # Create the output queue for printing to stdout
        self.o_queue = mp.JoinableQueue(self.max_out_queue_size)
        # Start the output thread for printing output
        self.o_thread = threading.Thread(target=self.print_out, 
                                         args=(self.o_queue,),
                                         name='OutputThread')
        self.o_thread.setDaemon(True)
        self.o_thread.start()
        # Setup an initial dataset number
        self.dataset = Gvar.getDataSetNum()
        file.add_to_log(self.dataset)
        self.manager = mp.Manager()
        file.make_dir_struct('META', self.dataset)
    
    def connect_instr(self, name, adr):
        """ Create the process for the instrument and attempt to connect.
        
        Parameters
        ----------
        name : string
            The name of the instrument, must be a key in INSTR.
        adr : string
            The address of the instrument, will be passed to the constructor.
            
        Returns
        -------
        s_queue : queue
            The broadcast queue of the instrument, connected is sent when the 
            instrument is successfully connected.
        """
        if name in self.INSTR:
            c_queue = mp.JoinableQueue(self.max_command_queue_size)
            r_queue = mp.JoinableQueue(self.max_response_queue_size)
            s_queue = mp.JoinableQueue(self.max_response_queue_size)
            args = (name, adr, c_queue, r_queue, self.o_queue)
            proc = mp.Process(target=self.start_process, args=args)
            proc.start()
            
            args = (r_queue, s_queue, self.o_queue)
            s_proc = mp.Process(target=self.save_process, args=args)
            
            # Create a thread to handle the response once the instrument connects
            args = (c_queue, r_queue, s_queue, proc, s_proc)
            rthread = threading.Thread(target=self.init_response, args=args)
            rthread.setDaemon(True)
            rthread.start()
            return s_queue
        else:
            msg = name + " is not a valid instrument name, see INSTR."
            self.o_queue.put(msg)
            return None
    
    @staticmethod
    def start_process(name, adr, c_queue, r_queue, o_queue):
        """ Create the process class. 
        
        Parameters
        ----------
        name : string
            The name of the instrument, must be a key in INSTR.
        adr : string
            The address of the instrument, will be passed to the constructor.
        c_queue : mp.Queue
            The command queue to place commands in.
        r_queue : mp.Queue
            The response queue to place responses in.
        """
        module = importlib.import_module('processes.' + name)
        proc_class = getattr(module, name)
        proc_class(name, adr, c_queue, r_queue, o_queue)
        
    @staticmethod
    def save_process(in_queue, out_queue, o_queue):
        """ Pull data from the response queue and save it to memory. 
        
        Parameters
        ----------
        in_queue : mp.Queue
            The input queue that data comes in on.
        out_queue : np.Queue
            The output queue to stick the data in after operating on it.
        """
        while True:
            data = in_queue.get()
            if data == '__exit__':
                out_queue.put(data)
                break
            meta = data['meta']
            if meta["Data type"] == 'IMAGE':
                data['raw'] = file.prep_IMAGE(data)
            if data['save']:
                save = getattr(file, 'save_' + meta["Data type"])
                if save(data, meta['Data set'], meta['Shot number']) == False:
                    msg = "Failed to save datafrom " + meta['Serial number']
                    o_queue.put(msg)
            out_queue.put(data)
            in_queue.task_done()

    def disconnect_instr(self, name, serial):
        """ Deletes an object for a passed instrument type and address.
        
        Parameters
        ----------
        serial : str
            The serial number of the device, will be the key in self.threads.
        """
        self.send_command(self.command_queue[serial], 'close')
        print('Disconnect', serial)
        self.instr[name].remove(serial)
        # Delete all the references to the processes, they should all shutdown on their own
        del self.command_queue[serial]
        del self.save_queue[serial]
        del self.response_queue[serial]
        #XXX This is dangerous if the proc is still doing something - also might corrupt o_queue
        #self.procs[serial].terminate()
        #self.s_procs[serial].terminate()
        del self.procs[serial]
        del self.s_procs[serial]
    
    def print_out(self, o_queue):
        """ Print outputs from the output queue. 
        
        Parameters
        ----------
        o_queue : queue
            The output queue which contains strings.
        """
        while True:
            msg = o_queue.get()
            if msg == '__exit__':
                break # Provides a way for the thread to complete.
            else:
                print(msg)
            time.sleep(0.01)
            o_queue.task_done()
            
    def turn_off_daq(self):
        """ Kills all threads and processes in DAQ."""
        for key in list(self.instr.keys()):
            N = len(self.instr[key])
            for i in range(N):
                self.disconnect_instr(key, self.instr[key][N-i-1])
        
        # Terminate the output thread, although daemon is true so it should be killed
        self.o_queue.put('__exit__')
        
#        threads = threading.enumerate()
#        for _t in threads:
#          print( _t.name)
#          print( _t.isAlive())
#          print()
        
            
    def add_s_proc(self, serial):
        """ Start up the saving process. 
        
        Parameters
        ----------
        serial : str
            The serial number of the device.
        """
        save_queue = mp.JoinableQueue(self.max_response_queue_size)
        in_queue = self.response_queue[serial]
        args = (in_queue, save_queue, self.o_queue)
        proc = mp.Process(target=self.save_process, args=args)
        self.save_queue[serial] = save_queue
        self.s_procs[serial] = proc
        proc.start()
    
    def init_response(self, c_queue, r_queue, s_queue, proc, s_proc):
        """ Initial response function for an instrument, adds queues to dict. 
        
        Parameters
        ----------
        c_queue : queue
            The command queue for the process.
        r_queue : queue
            The response queue for the process.
        s_queue : queue
            The save queue for the process.
        proc : queue
            The process itself. 
        s_proc : queue
            The save process. 
        """
        response = r_queue.get()
        serial = response[0]
        name = response[1]
        msg = "Device " + str(serial) + " successfully connected and process started."
        self.o_queue.put(msg)
        # Add references to everything to self
        if name in self.instr:
            self.instr[name].append(serial)
        else:
            self.instr[name] = [serial]
        # Need to start them here so init_response catches the first response
        s_proc.start()
        # Send the inital dataset number to the device and create the folders
        file.make_dir_struct(self.INSTR[name]['dataType'], self.dataset)
        self.send_command(c_queue, 'set_dataset', (self.dataset,))
        self.procs[serial] = proc
        self.s_procs[serial] = s_proc
        self.command_queue[serial] = c_queue
        self.response_queue[serial] = r_queue
        self.save_queue[serial] = s_queue
        r_queue.task_done()
        s_queue.put("__Connected__")
    
    # This is the wrong way to use args and kwargs, it remains for backward compatibility
    def send_command(self, c_queue, command, args=None, kwargs=None):
        """ Send a command object to a c_queue. 
        
        Parameters
        ----------
        c_queue : queue
            The command queue for the process.
        command : string
            The name of a function in either the instrument or process class.
        args : tuple, optional
            Arguments to pass to the function, must be picklable.
        """
        com = {"command" : str(command)}
        com["args"] = ()
        if args is not None:
            com["args"] = args
        com["kwargs"] = {}
        if kwargs is not None:
            com["kwargs"] = kwargs
        # If its not picklable, it should raise an error here
        try:
            c_queue.put(com)
        except:
            print(str(sys.exc_info()[0]))
            raise
        
    def save_meta(self):
        """Records the meta data in a text file."""
        file.meta_TXT(self.desc, self.dataset)
        
        #ts = True
        for name in self.instr:
            if name != 'SRSDG645':
                if self.instr[name]:
                    dType = self.INSTR[name]['dataType']
                    metaproc = getattr(file, 'meta_'+dType)
                    metaproc(self.dataset, self.instr[name])
                    #ts = False
            elif name == 'SRSDG645':
                if self.instr[name]:
                    dType = self.INSTR[name]['dataType']
                    metaproc = getattr(file, 'meta_'+dType)
                    metaproc(self.dataset, self.instr[name])
        
    def adv_dataset(self, desc=None):
        """ Advances dataset number."""
        self.desc = desc
        self.dataset = Gvar.getDataSetNum()
        file.add_to_log(self.dataset)
        file.make_dir_struct('META', self.dataset)
        
        for key in self.instr:
            file.make_dir_struct(self.INSTR[key]['dataType'], self.dataset)
        
        for key in self.command_queue:              
            self.send_command(self.command_queue[key], 'set_dataset', (self.dataset,))
            
    def waitQ(self, queue, delay=0.05):
        """ """
        Qsize = queue.qsize()
        while Qsize != 0:
            time.sleep(delay)
            Qsize = queue.qsize()
        time.sleep(delay)
        
    def get_available_instr(self):
        """ Find and return all instruments that can be connected.
        
        Returns
        -------
        instr : array
            Array of instruments available to be connected to the DAQ.
        """
        instr = {}
        # First scan for cameras
        cams = pc2.BusManager().discoverGigECameras()
        for cam in cams:
            instr[cam.serialNumber] = {
                    'name' : 'Camera',
                    'adr' : cam.serialNumber,
                    'model' : str(cam.modelName, 'utf-8')
                    }
        # Scan for USB devices using pyVisa
        rm = visa.ResourceManager('@py')
        visaDevices = rm.list_resources()
        for name in visaDevices:
            if name == 'USB0::1689::934::C046401::0::INSTR':
                instr['C046401'] = {
                    'name' : 'TDS2024C',
                    'adr' : name,
                    'model' : 'TDS2024C'
                        }
        # Find all serial over USB ports
        pts = prtlst.comports()
        for pt in pts:
            if 'USB' in pt[1]: # check 'USB' string in device description
                # Ping for the device ID to see what it is
                dev = ser.Serial(pt[0],
                                    baudrate=9600,
                                    bytesize=8,
                                    parity='N',
                                    stopbits=1,
                                    timeout=1)
                dev.write(b"*IDN?")
                ID = dev.read(16).decode("utf-8")
                if ID == 'KORADKA3005PV2.0':
                    adr = pt[0].split('/')[-1]
                    instr[adr] = {
                    'name' : 'KA3005P',
                    'adr' : adr,
                    'model' : 'KA3005P'
                        }
            if 'ACM' in pt[1]: # check for non-usb devices
                dev = ser.Serial(pt[0],
                                    baudrate=9600,
                                    bytesize=8,
                                    parity='N',
                                    stopbits=1,
                                    timeout=4)
                dev.write(b"*IDN?")
                ID = dev.readline(7).decode("utf-8").strip()
                if ID == 'FRG700':
                    adr = pt[0].split('/')[-1]
                    instr[adr] = {
                    'name' : 'FRG700',
                    'adr' : adr,
                    'model' : 'FRG700'
                        }
        # Find all the connected spectrometers
        devices = sb.list_devices()
        for dev in devices:
            instr[dev.serial] = {
                    'name' : dev.model,
                    'adr' : dev.serial,
                    'model' : dev.model
                        }
        # Ping the signal delay generator
        ret = os.system("ping -c 1 169.254.248.180")
        if ret == 0:
            instr[5025] = {
                    'name' : 'SRSDG645',
                    'adr' : 5025,
                    'model' : 'SRSDG645'
                        }
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
    for attempt in range(attempts):
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

