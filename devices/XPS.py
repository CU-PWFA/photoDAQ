#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 11:37:40 2021

@author: jamie

Source module: https://github.com/pyepics/newportxps
"""


from devices.device import Device
from newportxps import NewportXPS
from collections import OrderedDict

class XPS(Device):
    """ Class to control XPS controller. """
    
    def __init__(self, ip, set_default=True):
        """ Create the object for the XPS controller. """
        
        self.connectXPS(ip)
        # Initialize dictionaries of group names and stage names.
        self.group_names()
        self.stage_names()
        
    def connectXPS(self, ip):
        """Connect to the XPS controller.
        
        Parameters
        ----------
        ip : string
            The ip address of the XPS controller.
        """
        self.xps = NewportXPS(ip,username='Administrator', password='Administrator')
        self.xps.read_systemini()
        
    def group_names(self):
        """ Create dictionary of group names. 
        
            Default names are Group1, Group2, etc... """
            
        group_list=[]
        for gname, info in self.xps.groups.items():
            group_list.append(gname)
            count = 1
            self.dict_groupnames = {}
        #print(group_list) #debugging
    
        for i in group_list:
            self.dict_groupnames[count] = i
            count+=1
    
    def stage_names(self):
        """ Create dictionary of stage names.
        
            Default names are Group1.Pos, Group2.Pos, ..."""
        
        stage_list = []
        for sname, info in self.xps.stages.items():
            stage_list.append(sname)
            count = 1
            self.dict_stagenames = {}
        #print(stage_list) #debugging
    
        for i in stage_list:
            self.dict_stagenames[count] = i
            count+=1

    def initialize_group1(self):
        self.xps.initialize_group(str(self.dict_groupnames[1]))

    def initialize_group2(self):
        self.xps.initialize_group(str(self.dict_groupnames[2]))
    
    def home_group1(self):
        self.xps.home_group(str(self.dict_groupnames[1]))

    def home_group2(self):
        self.xps.home_group(str(self.dict_groupnames[2]))

    def get_single_groupstatus(self, group):
        out = OrderedDict()
        err, stat = self.xps._xps.GroupStatusGet(self.xps._sid, group)
        self.xps.check_error(err, msg="GroupStatus '%s'" % (group))

        err, val = self.xps._xps.GroupStatusStringGet(self.xps._sid, stat)
        self.xps.check_error(err, msg="GroupStatusString '%s'" % (stat))

        out[group] = val
        return out
    
    def get_single_status(self, group):
        """
        get the status for a single group as a string
        """
        out = None
        for groupname, status in self.get_single_groupstatus(group).items():
            out = status
        return out
    
    def get_group1_status(self):
        return self.get_single_status(str(self.dict_groupnames[1]))

    def get_group2_status(self):
        return self.get_single_status(str(self.dict_groupnames[2]))

    def get_stage1_position(self):
        return self.xps.get_stage_position(str(self.dict_stagenames[1]))

    def get_stage2_position(self):
        return self.xps.get_stage_position(str(self.dict_stagenames[2]))
    
    def move_stage1_abs(self, pos):
        """ move stage 1 to the absolute position 'pos' """
        self.xps.move_stage(str(self.dict_stagenames[1]), pos, 0)
    
    def move_stage1_rel(self, pos):
        """ move stage 1 to the absolute position 'pos' """
        self.xps.move_stage(str(self.dict_stagenames[1]), pos, 1)

    def move_stage2_abs(self, pos):
        """ move stage 2 to the absolute position 'pos' """
        self.xps.move_stage(str(self.dict_stagenames[2]), pos, 0)
    
    def move_stage2_rel(self, pos):
        """ move stage 2 to the absolute position 'pos' """
        self.xps.move_stage(str(self.dict_stagenames[2]), pos, 1)
    
    def reboot(self):
        """ Reboot the XPS controller """
        self.xps.reboot()