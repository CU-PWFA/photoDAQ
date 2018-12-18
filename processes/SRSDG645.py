#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 16:45:39 2018

@author: cu-pwfa
"""

from processes.process import Process
import threading
import file
import globalVAR as Gvar

class SRSDG645(Process):
    
    def save_settings(self):
        """Save the current settings on the SDG."""
        settings = {'T0' : {'delay' : [],
                            'output' : []},
                    
                    'AB' : {'delay' : [],
                            'output' : []},
    
                    'CD' : {'delay' : [],
                            'output' : []},
                                       
                    'EF' : {'delay' : [],
                            'output' : []},
                                       
                    'GH' : {'delay' : [],
                            'output' : []},
                                       
                    }
        
        sdg = self.device
        SRS = sdg.srs
        for i in range(5):
            out_value = str(i)
            ch1_value = str(i*2)
            ch2_value = str(i*2 + 1)
            
            out = sdg.outputs[out_value]
            ch1 = sdg.channels[ch1_value]
            ch2 = sdg.channels[ch2_value]
            
            ch1_setting = SRS.query('DLAY?'+ch1_value)
            ch1_reference = sdg.channels[ch1_setting[0]]
            ch1_delay = float(ch1_setting[2:len(ch1_setting)])
            
            ch2_setting = SRS.query('DLAY?'+ch2_value)
            ch2_reference = sdg.channels[ch2_setting[0]]
            ch2_delay = float(ch2_setting[2:len(ch2_setting)])
            
            output = SRS.query('LAMP?'+out_value)
            
            settings[out]['delay'] = [ [ch1_reference, ch1, ch1_delay], [ch2_reference, ch2, ch2_delay] ]
            settings[out]['output'] = [out, float(output)]
            
        meta = self.create_meta()
        data = {'save' : True,
                'meta' : meta,
                'saveType' : 'settings',
                'data' : settings }
        
        self.r_queue.put(data)
        
    def set_settings(self, settings, save=False):
        sdg = self.device
        for key in settings.keys():
            delay = settings[key]['delay']
            output = settings[key]['output']
            for Dlay in delay:
                sdg.set_delay(Dlay)
            sdg.set_output(output)
        
        if save:
            meta = self.create_meta()
            data = {'save' : True,
                    'meta' : meta,
                    'saveType' : 'settings',
                    'data' : settings } 
            
            self.r_queue.put(data)
            
    def start_trigger_thread(self):
        """ Create and start a thread to monitoring timestamps of external trigger."""
        metaName = file.get_dirName('META', self.dataset)+'meta_{}.txt'.format(self.dataset)
        f = open(metaName, 'r')
        contents = f.readlines()
        f.close()
        
        contents.append('\n# Time Stamp of Each Shot (year/month/day/hour/minute/second/microsecond)\n')
        f = open(metaName, 'w')
        contents = "".join(contents)
        f.write(contents)
        f.close()    
        
        trig_thread = threading.Thread(target=self.trigger_for_timestamp)
        trig_thread.start()
    
    def trigger_for_timestamp(self):
        """ Print time stamps coupled to the SDG trigger to the dataset meta file."""
        srs = self.device
        while True:
            resp = srs.get_status()
            if resp[0] == '5':
                ts = Gvar.get_timestamp()
                meta = self.create_meta()
                
                data = {'save' : True,
                        'meta' : meta,
                        'saveType' : 'trigger',
                        'data'  : {} }
                
                data['data']['shot'] = 'Shot %s : ' % self.shot
                data['data']['Time Stamp'] = ts
                
                self.shot+=1
                self.r_queue.put(data)
               
    def get_datatype(self):
        """Return the type of data. """
        return "DELAY"
            
    def get_type(self):
        """ Return the instrument type. """
        return "SRSDG645"