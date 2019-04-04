#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 15:51:37 2018

@author: robert
"""

import sys
import file
import globalVAR as Gvar
import multiprocessing as mp
import numpy as np
import time
import threading

###############################################################################
#   
#   The main DAQ class that controls acquisiton and parameters
#   
#   
###############################################################################

class Daq():
    """ Main daq class, handles instrument and thread/process managment. 
    
    The Daq class is the central piece of the DAQ. It handles:
        - Initial file system setup for the DAQ
        - Process and thread creation and managment
        - Queue creation and managment
        - Connecting and disconnecting instruments
        - Sending commands to instruments
        - Recieving responses and data from instruments
    """
    TC_serial = '5573631333835150F150'
    def __init__(self, desc=None, broadcast=False, max_command_queue_size=100,
                 max_response_queue_size=1000, debug=False):
        """ Initialize the main DAQ class.
        
        The description is used for the first dataset, it can be changed post 
        initiation by directly editing the desc attribute.
        
        Broadcast should be set to true if the application needs access to the
        responses or data from the instruments. If it is set to true seperate
        output queues will be created for each instrument. 
        
        Parameters
        ----------
        desc : str
            Description of data set.
        broadcast : bool, optional
            True to broadcast instrument responses/data into an output queue.
        max_command_queue_size : int optional
            The maximum size of the command queue, default is 100.
        max_response_queue_size : int, optional
            The maximum size of the response and output queues, defaul is 1000.
        debug : bool, optional
            Defaults to false, if true will send print outputs to the terminal.
        """
        self.instr = {} # Dictionary of instrument objects {serial : instr}
                
        # Define attributes of the DAQ
        self.max_command_queue_size = max_command_queue_size
        self.max_response_queue_size = max_response_queue_size
        self.max_print_queue_size = 1000  # If more than 1000 messages back up something is wrong
        self.desc = desc
        self.broadcast = broadcast
        self.debug = debug
        self.taking_data = False
        # Setup the daq
        self.setup_daq()
    
    def setup_daq(self):
        """ Setup everything necessary to run the daq. """
        # It isn't safe to fork multithreaded processes
        # However you can't spawn if threads are already created
        # Apparently forking a multithreaded process can cause deadlock because a process can get a lock and then die with it...
        # If the code starts freezing when instruments are disconnected - this might be the problem
        #mp.set_start_method('spawn')
        
        # Set the save path for the data
        file.PATH = file.get_file_path()
        file.check_log()    # Make sure the log exists, if it doesn't, create it
        
        # Create the print queue to make stdout multiprocessing safe
        self.p_queue = mp.JoinableQueue(self.max_print_queue_size)
        if self.debug == False:
            sys.stdout = WriteStream(self.p_queue)
        
        # Setup an initial dataset number
        self.adv_dataset(self.desc)
    
    def connect_instr(self, instr):
        """ Create the process for the instrument and attempt to connect.
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument to be connected.
        """
        if instr.serial in self.instr:
            self.print_msg("Instrument "+instr.serial+" is already connected.")
        else:
            # Create all the response queues
            instr.command_queue = mp.JoinableQueue(self.max_command_queue_size)
            instr.response_queue = mp.JoinableQueue(self.max_response_queue_size)
            instr.dataset = self.dataset
            if self.broadcast:
                instr.output_queue = mp.JoinableQueue(self.max_response_queue_size)
            args = (instr,)
            proc = mp.Process(target=self.start_process, args=args)
            proc.start()
            
            # The timing controller needs an additional thread for the DAQ to use
            if instr.serial == self.TC_serial:
                instr.internal_queue =  mp.JoinableQueue(self.max_response_queue_size)
                self.TC_thread = threading.Thread(target=self.timing_thread, args=args)
                self.TC_thread.setDaemon(True)
                self.TC_thread.start()
            
            args = (instr,)
            r_proc = mp.Process(target=self.response_process, args=args)
            r_proc.start()
            # Don't create references to the processes until after the instrument object
            # is copied to the processes themselves
            instr.process = proc
            instr.response_process = r_proc
            # Adding this here prevents the code from attempting a second connection
            # before the first connection finishes
            self.instr[instr.serial] = instr
    
    @staticmethod
    def start_process(instr):
        """ Create the process class. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        instr.process_cls(instr)
    
    @staticmethod
    def response_process(instr):
        """ Pull data from the response queue and save it to memory. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument the process will control.
        """
        def output(rsp): 
            if o_queue is not None:
                o_queue.put(rsp)

        r_queue = instr.response_queue
        if hasattr(instr, 'internal_queue'):
            o_queue = instr.internal_queue
        else:
            o_queue = instr.output_queue
        while True:
            rsp = r_queue.get()
            response = rsp.response
            if response == 'connected':
                output(rsp)
                print("Instrument " + instr.serial + " connected and process started.")
            elif response == 'exit':
                output(rsp)
                print("Instrument " + instr.serial + " disconnected.")
                break
            elif response == 'output':
                output(rsp)
            elif response == 'save':
                output(rsp)
                # TODO implement saving data to file in a better way
                meta = rsp.meta
                #if meta["Data type"] == 'IMAGE':
                #    rsp.data = file.prep_IMAGE(data)
                
                save = getattr(file, 'save_' + meta["Data type"])
                if save(rsp, meta['Data set'], meta['Shot number']) == False:
                    print("Failed to save datafrom " + meta['Serial number'])
            elif response == 'connection_error':
                output(rsp)
                print("Instrument " + instr.serial + " failed to connect.")
                break
            r_queue.task_done()
            
    def timing_thread(self, instr):
        """ Timing thread for handling shot specific steps. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the timing control instrument.
        """
        o_queue = instr.output_queue
        i_queue = instr.internal_queue
        while True:
            rsp = i_queue.get()
            response = rsp.response
            if response == 'exit':
                o_queue.put(rsp)
                break
            elif response == 'connection_error':
                o_queue.put(rsp)
                break
            else:
                o_queue.put(rsp)
            # If we are taking data this will be set true and then the timing
            # controller will be triggered
            if self.taking_data:
                i = self.set
                self.shot += 1
                stop_points = self.sweep['stop_points']
                # Dataset finished
                if self.shot == stop_points[-1]:
                    self.taking_data = False
                # Check if we just finished a set
                elif self.shot == stop_points[i-1]:
                    n = stop_points[i] - stop_points[i-1]
                    self.sweep_step()
                    self.start_TC(n)
                    self.set += 1
                
            i_queue.task_done()
            

    def disconnect_instr(self, instr):
        """ Disconnects an instrument and removes it from the instr dict.
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument to disconnect.
        """
        if instr.serial in self.instr:
            self.send_command(instr, 'close')
            self.instr.pop(instr.serial)
        else:
            self.print_msg("Instrument "+instr.serial+" cannot be disconnected because it is not connected.")
            
    def close_daq(self):
        """ Disconnects all instruments and tells the printing thread to exit."""
        for serial in list(self.instr.keys()):
            self.disconnect_instr(self.instr[serial])
        
        # TODO add this information into a verbose version
#        threads = threading.enumerate()
#        for _t in threads:
#          print( _t.name)
#          print( _t.isAlive())
#          print()
    
    def send_command(self, instr, command, *args, **kwargs):
        """ Send a command to a instrument. 
        
        Parameters
        ----------
        instr : instr object
            The object representing the instrument to send a command to.
        command : string
            The name of a function in either the instrument or process class.
        *args : Variable length argument list
        **kwargs : Arbitrary keyword arguments
        """
        cmd = Cmd(command, *args, **kwargs)
        # If its not picklable, it should raise an error here
        try:
            instr.command_queue.put(cmd)
        except:
            self.print_msg('Command could not be placed in the queue:' 
                           + str(sys.exc_info()[0]))
            raise
        
    def save_meta(self, instrs):
        """Records the meta data in a text file.
        
        Parameters
        ----------
        shots : int
            The number of shots to take.
        instrs : dict
            Dictionary of instrument objects to take data with.
        """
        file.meta_TXT(self.desc, self.dataset)
        
        for serial, instr in instrs.items():
            dType = instr.data_type
            # TODO, implement this function in more detail
#            metaproc = getattr(file, 'meta_'+dType)
#            metaproc(self.dataset, instr)
        
    def adv_dataset(self, desc=None):
        """ Advances dataset number in all instruments and creates directories.
        
        Parameters
        ----------
        desc : string, optional
            The description for the dataset.
        """
        self.desc = desc
        self.dataset = Gvar.getDataSetNum()
        file.add_to_log(self.dataset)
        file.make_dir_struct('META', self.dataset)
        self.create_dir_struct()
    
    def create_dir_struct(self):
        """ Create a directory structure for all connected instruments. """
        for serial, instr in self.instr.items():
            file.make_dir_struct(instr.data_type, self.dataset)
            self.send_command(instr, 'set_dataset', self.dataset)
        
    def start_dataset(self, shots, instrs, sweep):
        """ Save a specified number of shots from the passed instruments.
        
        Parameters
        ----------
        shots : int
            The number of shots to take.
        instrs : dict
            Dictionary of instrument objects to take data with.
        sweep : dict
            The dictionary containing the sweep parameters.
        """        
        # Tell all the streaming instruments to start streaming
        for key, instr in instrs.items():
            self.send_command(instr, 'save_stream', shots)
        
        # For sweeps we need to synchronize the different devices

        # Setup the length of capture between parameter changes
        print(sweep)
        shot_array = np.arange(0, shots, dtype='int16') + 1
        stop_array = np.zeros(shots, dtype='bool')
        for serial, item in sweep.items():
            if item['sweep'] == False:
                continue
            item['shot_per_step'] = np.ceil(shots/item['step'])
            item['parameter_array'] = np.linspace(item['start'], item['stop'], item['step'])
            stop = (shot_array % item['shot_per_step']) == 0
            stop_array = np.logical_or(stop_array, stop)
        stop_points = np.array([i for i, j in enumerate(stop_array) if j]) + 1
        np.append(stop_points, shots)
        
        # If we don't have any sweeps, run through the shots
        if len(stop_points) == 0:
            self.start_TC(shots)
        
        # Set all initial parameters
        
        
        # Tell the timing thread to start taking data
        self.shot = 0
        self.set = 1
        sweep['stop_points'] = stop_points
        self.sweep = sweep
        self.taking_data = True
        
        # Take the first set and trigger the timing thread
        self.start_TC(stop_points[0])
    
        self.save_meta(instrs)
        
    def start_TC(self, shots):
        """ Start the timing controller and take the passed number of shots.
        
        Parameters
        ----------
        shots : int
            The number of shots to take.
        """
        if self.TC_serial not in self.instr.keys():
            print('No timing controller connected, cannot start synchronization.')
            return
        else:
            TC = self.instr[self.TC_serial]
        self.send_command(TC, 'reset', shots)
        self.send_command(TC, 'start_stream')
        time.sleep(0.5) # Give the devices time to start streaming
        self.send_command(TC, 'start')
        
    def sweep_step(self):
        """ Change any instrument parameters necessary for the sweep. """


class Cmd():
    """ Class used to create command objects. 
    
    The object is sent between processes through a queue, it must be picklable.
    """
    def __init__(self, command, *args, **kwargs):
        """ Create the command. 
        
        Parameters
        ----------
        command : string
            The name of the function to call in either the instrument or process.
        *args : Variable length argument list
        **kwargs : Arbitrary keyword arguments
        """
        self.command = command
        self.args = args
        self.kwargs = kwargs
        
class Rsp():
    """ Class used to create response objects. 
    
    The object is sent between processes through a queue, it must be picklable.
    """
    def __init__(self, response, data=None, meta=None):
        """ Create the response. 
        
        Parameters
        ----------
        response : string
            The response type, determines how the response is handled.
        data : dict, optional
            The data to send over the queue.
        meta : dict, optional
            Meta data to send over the queue.
        """
        self.response = response
        self.data = data
        self.meta = meta

class WriteStream(object):
    """ Multiprocessing safe stream object to replace default stdout stream. """
    def __init__(self, queue):
        """  """
        self.queue = queue
        
    def write(self, text):
        self.queue.put(text)
        
    def flush(self):
        pass