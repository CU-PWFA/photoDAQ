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
import PyCapture2 as pc2
import queue
import threading

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
    """ Main daq class, handles instrument and thread managment. """
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
        self.setup_daq()
        self.instr = {}
        self.threads = {}
        self.rthreads = {}
        self.command_queue = {}
        self.response_queue = {}
        self.max_command_queue_size = 10000
        self.max_response_queue_size = 1000
    
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
        # Set the save path for the data
        file.PATH = file.get_file_path()
        # Create a new data set number
        file.check_log() # Make sure the log exists, if it doesn't, create it
    
    def connect_instr(self, name, adr):
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
        if name in self.INSTR:
            module = importlib.import_module('devices.' + name)
            instr_class = getattr(module, name)
            device = instr_class(adr)
            device.type = name
            try:
                self.instr[str(device.serialNum)] = device
            except:
                print('Could not connect to device:', name)
                return
            self.create_thread(str(device.serialNum))
            
    def create_thread(self, serial):
        """ Create a thread for the device and the corresponding queues.
        
        Parameters
        ----------
        serial : str
            The serial number of the device, will be the key in self.threads.
        """
        c_queue = queue.Queue(self.max_command_queue_size)
        r_queue = queue.Queue(self.max_response_queue_size)
        thread = threading.Thread(target=self.command, 
                                   args=(serial, c_queue, r_queue))
        thread.setDaemon(True) #Thread dies if the main process dies
        thread.start()
        #Make the response thread
        rthread = threading.Thread(target=self.response, args=(serial, r_queue))
        rthread.setDaemon(True)
        rthread.start()
        # Make the threads and queues accessible from the class.
        self.command_queue[serial] = c_queue
        self.response_queue[serial] = r_queue
        self.threads[serial] = thread
        self.rthreads[serial] = rthread

    def disconnect_instr(self, serial):
        """ Deletes an object for a passed instrument type and address.
        
        Parameters
        ----------
        serial : str
            The serial number of the device, will be the key in self.threads.
        """
        device = self.instr[serial]
        device.close()
        del self.instr[serial]
        
    def command(self, serial, c_queue, r_queue):
        """ Command function for an instrument, runs the request loop. 
        
        Parameter
        ---------
        serial : string
            The serial number of the instrument, used for error messages.
        c_queue : queue
            The command queue for the instrument to retrieve commands from.
        r_queue : queue
            The response queue to place responses in.
        """
        while True:
            command = c_queue.get()
            ret = self.try_command(serial, command)
            if command.response and ret is not None:
                # Build the response
                response = Response(ret, command.callback, command.callargs)
                r_queue.put(response)
            c_queue.task_done()
            time.sleep(command.wait)
    
    def try_command(self, serial, command):
        """ Attempts to execute a command and handles retrying and errors.
        
        Parameters
        ----------
        serial : string
            The serial number of the instrument, used for error messages.
        command : obj
            Instance of the command class representing the command.
        """
        for attempt in range(command.attempts):
            ret = None
            try:
                ret = command.run()
            # Add exceptions that should be handled here
            except pc2.Fc2error as err:
                msg = ("An exception was encountered in thread: " + serial +', '
                       + str(err))
                print(msg)
                continue
            except: 
                msg = ("An exception was encountered in thread: " + serial +', '
                       + str(sys.exc_info()[0]))
                print(msg)
                raise
            return ret
        return ret
    
    def response(self, serial, r_queue):
        """ Response function for an instrument, runs the response loop. 
        
        Parameters
        ----------
        serial : string
            The serial number of the instrument, used for error messages.
        r_queue : queue
            The response queue to retrieve responses from.
        """
        while True:
            response = r_queue.get()
            print('Response')
            response.callback(response.ret, *response.args)
            r_queue.task_done()


class Command():
    """ A class for creating commands to place in the queue. 
    
    You must create a new instance of this class for every command. """
    def __init__(self, func=None, args=None, response=True, callback=None,
                 callargs=None, wait=0.05, attempts=10):
        """ Constructor for the command. 
        
        Parameters
        ----------
        func : function
            The function to execute in the thread.
        args : tuple
            The arguments to pass to the function.
        response : bool, optional
            Whether to return a response from the instrument or not.
        callback : function
            A call back to be placed in the response.
        wait : float
            Time to wait after execution. 
        """
        if args is not None:
            self.args = args
        else:
            self.args = ()
        if callargs is not None:
            self.callargs = callargs
        else:
            self.callargs = ()
        self.response = response
        # Set the functions if they are not none
        if func is not None:
            self.func = func
        if callback is not None:
            self.callback = callback
        self.wait = wait
        self.attempts= attempts
    
    def func(self):
        """ Function that will be called. """
        pass
    
    def run(self):
        """ Call the function with self.args. """
        return self.func(*self.args)
    
    def callback(self):
        """ Callback function for after the response. """
        pass
    

class Response():
    """ A class for creating responses to place in the queue. """
    def __init__(self, ret, callback, args):
        """ Constructor for the response. """
        self.callback = callback
        self.ret = ret
        self.args = args
        

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
