#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 25 14:41:20 2019

@author: cu-pwfa
"""
import sys
sys.path.append('../')
import numpy as np
import file as f
import matplotlib.pyplot as plt
import h5py as h5

from matplotlib import rc
rc('mathtext', default='regular')

f.PATH = f.get_file_path()
path = f.PATH+'TRACE/year_2019/month_01/day_21/'
ivData = h5.File(path+'iv_set.h5', 'r')

time_domain = np.linspace(0, 0.4, 401) * 10**-6
for ind, time in enumerate(time_domain):
    print(ind)
    
    key = 'time: {}'.format(time)
    data = np.array(ivData[key])
    
    fig = plt.figure()    
    ax = fig.add_subplot(111)
    fnt = 14
    c='k'
    
    ax.scatter(data[0], -data[1] * 10**3, s=10, c='k')
    
    ax.spines['left'].set_position('zero')
    ax.spines['bottom'].set_position('zero')
    
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    plt.xlabel(r'$V$  (Volt)', color=c, fontsize=fnt, labelpad=100)
    plt.ylabel(r'$I$  (mA)', color=c, fontsize=fnt, labelpad=175)
    plt.title(r'time: {} $\mu s$'.format(round(time*10**6, 3)), fontsize=16)
    
    plt.tight_layout()
    #plt.show()
    plt.savefig(path+'IV_Curves/time_%s.png' % ind)
    plt.close()
