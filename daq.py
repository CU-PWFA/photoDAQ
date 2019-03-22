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
#            meta = data['meta']
#            if meta["Data type"] == 'IMAGE':
#                data['raw'] = file.prep_IMAGE(data)
#            if data['save']:
#                save = getattr(file, 'save_' + meta["Data type"])
#                if save(data, meta['Data set'], meta['Shot number']) == False:
#                    msg = "Failed to save datafrom " + meta['Serial number']
#                    o_queue.put(msg)
#            out_queue.put(data)
#            in_queue.task_done()

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
        
        for serial, instr in instrs:
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
        # First tell all the streaming instruments to start streaming
        for key, instr in instrs.items():
            self.send_command(self.command_queue[key], 'save_stream', (shots,))
        
        # Prep any sweep 
        print(sweep)
        self.save_meta()


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