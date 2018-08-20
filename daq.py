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
import threading
import multiprocessing as mp
###############################################################################
#   
#   The main DAQ loop that controls acquisiton and parameters
#   
#   
###############################################################################

def main(instrInit, instrAdr, mod, nShots, desc):
    """ Runs the DAQ.
    
    Parameters
    ----------
    instrInit : list of strings
        List of the names of instruments used, must be keys in INSTR.
    instrAdr : list of ints
        The addresses of the instruments, will be passed to the constructor.
    mod : string
        Name of the script to be used for setup and measurment
    nShots : int
        Number of shots for the DAQ
    desc : string
        Description of the data set.
    """
    arg = [instrInit, instrAdr, mod, nShots, desc]
    daq = Daq() 
    dataSet = Gvar.getDataSetNum()
    file.add_to_log(dataSet)
    file.make_dir_struct('META', dataSet)
    
    # Create all the instrument classes
    instr = daq.instr
    
    for i in range(len(instrInit)):
        name = instrInit[i]
        daq.connect_instr(name, instrAdr[i])
        try:
            file.make_dir_struct(daq.INSTR[name]['dataType'], dataSet)
        except:
            print('The directory structure couldnt be made, instrument:', name)
    
    # Setup some statistics functions
    failed = 0
    # Take a series of measurements
    script = importlib.import_module('scripts.' + mod)
    getattr(script, 'setup')(instr)
    startTime = time.clock()
    measure = getattr(script, 'measure')
    for i in range(nShots):
        shot = i+1
        failed += do_measurement(instr, measure, shot, dataSet)
                
    endTime = time.clock()
    # Save the dataset metadata
    meta = Gvar.create_metadata(arg, startTime)
    file.save_meta(meta, dataSet)
    
    # Close all instruments to prepare for another dataset
    for name in instr:
        instr[name].close()
    
    daq.print_stat(shot, failed, startTime, endTime)
    # Handle any post processing that needs to occur
    post_process(instr, dataSet, shot)


class Daq():
    """ Main daq class, handles instrument and thread/process managment. """
    def __init__(self):
        # Store information about our various instruments
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
                            'dataType'  : 'TRACE'
                            }
                }
        self.instr = []
        self.procs = {}
        self.s_procs = {}
        self.p_procs = {}
        self.command_queue = {}
        self.save_queue = {}
        self.response_queue = {}
        self.max_out_queue_size = 10000
        self.max_command_queue_size = 10000
        self.max_response_queue_size = 1000
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
        # However you can't spawn if threads are already created - we'll live on the edge
        # Apparently forking a multithreaded process can cause deadlock because a process can get a lock and then die with it...
        # If the code starts freezing when instruments are disconnected - this might be the problem
        #mp.set_start_method('spawn')
        # Set the save path for the data
        file.PATH = file.get_file_path()
        # Create a new data set number
        file.check_log() # Make sure the log exists, if it doesn't, create it
        # Create the output queue for printing to stdout
        self.o_queue = mp.JoinableQueue(self.max_out_queue_size)
        # Start the output thread for printing output
        self.o_thread = threading.Thread(target=self.print_out, 
                                         args=(self.o_queue,))
        self.o_thread.setDaemon(True)
        self.o_thread.start()
        # Setup an initial dataset number
        self.dataset = Gvar.getDataSetNum()
        self.manager = mp.Manager()
    
    def connect_instr(self, name, adr):
        """ Create the process for the instrument and attempt to connect.
        
        Parameters
        ----------
        name : string
            The name of the instrument, must be a key in INSTR.
        adr : string
            The address of the instrument, will be passed to the constructor.
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
            
            args = (s_queue, self.o_queue)
            p_proc = mp.Process(target=self.post_process, args=args)
            
            # Create a thread to handle the response once the instrument connects
            args = (c_queue, r_queue, s_queue, proc, s_proc, p_proc)
            rthread = threading.Thread(target=self.init_response, args=args)
            rthread.setDaemon(True)
            rthread.start()
        else:
            msg = name + " is not a valid instrument name, see INSTR."
            self.o_queue.put(msg)
    
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
            if data['save']:
                meta = data['meta']
                save = getattr(file, 'save_' + meta["Data type"])
                if save(data, meta['Data set'], meta['Shot number']) == False:
                    msg = "Failed to save datafrom " + meta['Serial number']
                    o_queue.put(msg)
            out_queue.put(data)
            in_queue.task_done()
    
    @staticmethod
    def post_process(in_queue, o_queue):
        """ Base post process, clears queue. """
        while True:
            in_queue.get()
            in_queue.task_done()

    def disconnect_instr(self, serial):
        """ Deletes an object for a passed instrument type and address.
        
        Parameters
        ----------
        serial : str
            The serial number of the device, will be the key in self.threads.
        """
        self.send_command(self.command_queue[serial], 'close')
        self.instr.remove(serial)
        del self.command_queue[serial]
        del self.save_queue[serial]
        del self.response_queue[serial]
        #XXX This is dangerous if the proc is still doing something - also might corrupt o_queue
        self.procs[serial].terminate()
        #self.s_procs[serial].terminate()
        #self.p_procs[serial].terminate()
        del self.procs[serial]
        del self.s_procs[serial]
        del self.p_procs[serial]
    
    def print_out(self, o_queue):
        """ Print outputs from the output queue. 
        
        Parameters
        ----------
        o_queue : queue
            The output queue which contains strings.
        """
        while True:
            print(o_queue.get())
            o_queue.task_done()
            
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
        
    def add_p_proc(self, serial):
        """ Start up the saving process. 
        
        Parameters
        ----------
        serial : str
            The serial number of the device.
        """
        in_queue = self.save_queue[serial]
        args = (in_queue, self.o_queue)
        proc = mp.Process(target=self.post_process, args=args)
        self.p_procs[serial] = proc
        proc.start()
    
    def init_response(self, c_queue, r_queue, s_queue, proc, s_proc, p_proc):
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
        p_proc : queue
            The post process. 
        """
        response = r_queue.get()
        serial = response[0]
        name = response[1]
        msg = "Device " + str(serial) + " successfully connected and process started."
        self.o_queue.put(msg)
        # Add references to everything to self
        self.instr.append(serial)
        self.procs[serial] = proc
        self.s_procs[serial] = s_proc
        self.p_procs[serial] = p_proc
        self.command_queue[serial] = c_queue
        self.response_queue[serial] = r_queue
        self.save_queue[serial] = s_queue
        # Need to start them here so init_response catches the first response
        s_proc.start()
        p_proc.start()
        # Send the inital dataset number to the device and create the folders
        file.make_dir_struct(self.INSTR[name]['dataType'], self.dataset)
        self.send_command(c_queue, 'set_dataset', (self.dataset,))
        r_queue.task_done()
    
    def send_command(self, c_queue, command, args=None):
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
        # If its not picklable, it should raise an error here
        try:
            c_queue.put(com)
        except:
            print(str(sys.exc_info()[0]))
            raise
        

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
    
    
if __name__ == "__main__":
    main(sys.argv)
