#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 25 13:16:06 2019

@author: cu-pwfa
"""
import sys
sys.path.append('../')

import file as f
import h5py as h5
import numpy as np
import functions as fun
import matplotlib.pyplot as plt

save = True
plot_crnt = True
plot_bias = False

dataset = '1908020002'

f.PATH = f.get_file_path()
path = f.PATH+'TRACE/year_2019/month_08/day_02/'+dataset+'/'

if save:
    trace_set = h5.File(path+'trace_set.h5', 'w')

mid = 601
trig = 270
res = 1000

cnt=0
trk_2=0
trk_3=0

bias = np.empty((mid, 2499-trig))
crnt = np.empty((mid, 2499-trig))

tracePATH = f.get_dirName_from_dataset('TRACE', dataset)
traceFILES = sorted(fun.list_files(tracePATH, 'npy'))
for file in traceFILES:
    
    shot = int(file[19:23])
    if shot <= mid:
        sign = -1
    else:
        sign = 1
    
    trace = f.load_TRACE(tracePATH+file)
    chan = trace['meta']['Wavefront ID'][0:3]
    if chan == 'Ch2':
        indx = int(shot / 2)
        crnt[indx] = fun.return_trace(trace, sign * res, trig)[1::]
        time = fun.return_time(trace, trig)
                
        if plot_crnt:
            plt.plot(time * 1e6, crnt[indx] * 1e3)
        
    elif chan == 'Mat':
        indx = int( shot / 2. ) 
        volt = fun.return_trace(trace, -sign, trig)[1::]
        bias[indx] = volt
        
        if plot_bias:
            if shot == cnt * 100 + 1:                
                plt.plot(time * 1e6, bias[indx])
                
                plt.xlabel(r'time ($\mu$s)', fontsize=16)
                plt.ylabel('current (mA)', fontsize=16)
                
                plt.show()
                plt.close()
                
                cnt+=1

if save:  
    trace_set.create_dataset('bias', data=bias)
    trace_set.create_dataset('crnt', data=crnt)  
    trace_set.create_dataset('time', data=time)     
    
    trace_set.close()

if plot_crnt:
    fnt = 16
    
    plt.xlabel(r'time ($\mu$s)', fontsize=fnt)
    plt.ylabel('current (mA)', fontsize=fnt)
    
    #plt.show()
    plt.savefig(path+'trace_set.png')
    plt.close()
