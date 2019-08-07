#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 20 17:10:19 2018

@author: michael
"""

import sys
sys.path.append('../')
import numpy as np
import file as f
import matplotlib.pyplot as plt
import numpy_indexed as npi
import h5py as h5
from scipy.stats import linregress
import functions as fun

from matplotlib import rc
rc('mathtext', default='regular')

dataset = '1908020002'

f.PATH = f.get_file_path()
path = f.PATH+'TRACE/year_2019/month_08/day_02/'+dataset+'/'

dataFile = h5.File(path+'trace_set.h5', 'r')
crnt = dataFile['crnt'][:]
bias = dataFile['bias'][:]
time = dataFile['time'][:]
dataFile.close()

shp = bias.shape[0]
for i in range(shp):
    plt.plot(time * 1e6, bias[i])
    
plt.show()
plt.close()

'''
shots = crnt.shape[0]
half = int(.5 * shots)
incr = 18

#ivData = h5.File(path+'iv_set.h5', 'w')

strt = 100
fnsh = strt + 1
for t_ind, t in enumerate(time[strt:fnsh]):
    t_ind = t_ind + strt
    
    cnt=0
    Crnt = np.empty(shots- (2*incr+1))
    Bias = np.empty(shots- (2*incr+1))
    for s in range(shots):
        if (s < half-incr) or (s > half+incr):
            Crnt[cnt] = crnt[s][t_ind] 
            Bias[cnt] = bias[s][0]
            cnt+=1
    
    Crnt[0:half-incr+1] = - np.log(np.abs(Crnt[0:half-incr+1])) + 2*np.log(np.abs(Crnt[half-incr]))
    Crnt[half-incr+1::] = np.log(np.abs(Crnt[half-incr+1::]))
    plt.scatter(Bias, Crnt, s=10)
    plt.title(r'time: {0} $\mu$s ({1})'.format(round(t * 1e6, 3), t_ind))
    plt.show()
    plt.close()

    #ivData.create_dataset('time: %s' % time, data=iv_data)
    
#ivData.close()
dataFile.close()
'''     
'''
Vp1 = 1
Vp2 = -1.6

numpts = 201
for i in [35]:#range(numpts):
    time = round(i*.01, 2)
    time_key = 'Time {}'.format(time)
    print(time_key)
    
    bias = []
    crnt = []
    for num in dataset:
        if num == '1901210023':
            amp = 10000
        else:
            amp = 1000
        tracePATH = f.get_dirName_from_dataset('TRACE', num)
        traceFILES = sorted(fun.list_files(tracePATH, 'npy'))
        for fil in range(len(traceFILES)):
            trace = f.load_TRACE(tracePATH+traceFILES[fil])
            chan = trace['meta']['Channel']
            for key in chan:
                if chan[key][0]:
                    ret = fun.trace_analysis(key, trace, time, amp=amp)
                    if key == 'CH2':
                        probe_1 = ret
                    elif key == 'CH1':
                        crnt.append(ret)
                    else:
                        probe_2 = ret
                        bias.append(probe_1-probe_2)
                    
    bias = np.array(bias)
    crnt = np.array(crnt)*1000
    
    V_set, I_set = npi.group_by(bias).mean(crnt)
    data = [I_set, V_set]
    
    #dataFile.create_dataset(time_key, data=data)
    
    Is1 = I_set[np.round(V_set, 1) > Vp1]
    Vs1 = V_set[np.round(V_set, 1) > Vp1]
    pRams1 = linregress(Vs1, Is1)
    
    Is2 = I_set[np.round(V_set, 1) < Vp2]
    Vs2 = V_set[np.round(V_set, 1) < Vp2]
    pRams2 = linregress(Vs2, Is2)
    
    Ip1 = I_set[fun.ind_closest_to_val(V_set, Vp1)]
    Ip2 = -I_set[fun.ind_closest_to_val(V_set, Vp2)]
    
    fig = plt.figure()    
    ax = fig.add_subplot(111)
    fnt = 14
    c='k'
    
    ax.plot(V_set, I_set)
    ax.scatter([Vp1, Vp2], [Ip1, -Ip2], s=50, c='r', label='$I_{p1}, I_{p2}$')
    
    ax.plot(Vs1, fun.line(Vs1, pRams1[0], pRams1[1]), c='k', ls='--')
    ax.plot(Vs2, fun.line(Vs2, pRams2[0], pRams2[1]), c='k', ls='--')
    
    ax.set_xlabel(r'$V$  (Volt)', color=c, fontsize=fnt, labelpad=115)
    ax.set_ylabel(r'$I$  (mA)', color=c, fontsize=fnt, labelpad=150)
    
    ax.spines['left'].set_position(('data', 0))
    ax.spines['bottom'].set_position(('data', 0))
    ax.spines['right'].set_position(('data', 0))
    ax.spines['top'].set_position(('data', 0))
    
    plt.legend(prop={'size': 14})
    plt.tight_layout()
    #plt.savefig(path+'IV_{}.png'.format(i))  
    plt.show()
    plt.close()
    
    fnt = 14
    plt.plot([time, time], [-1.25, .55], ls='--', c='k', label='{} ms'.format(time))
    plt.xlabel(r'$t$ (ms)', fontsize=fnt)
    plt.ylabel(r'$I$ (mA)', fontsize=fnt)
    
    plt.legend()
    #plt.savefig(path+'TS_{0}/TS_Current_{0}.png'.format(i))
    plt.show()
    plt.tight_layout()
    plt.close()
    

#dataFile.close()
'''   
