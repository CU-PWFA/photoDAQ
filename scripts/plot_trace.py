#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 25 11:16:10 2019

@author: cu-pwfa
"""

import sys
sys.path.append('../')
import file as f
import matplotlib.pyplot as plt
import functions as fun

from matplotlib import rc
rc('mathtext', default='regular')

f.PATH = f.get_file_path()
path = f.PATH+'TRACE/year_2019/month_01/day_21/'

dataset = ['1901210020',
           '1901210022']

amp = 1000
for num in dataset:
    tracePATH = f.get_dirName_from_dataset('TRACE', num)
    traceFILES = sorted(fun.list_files(tracePATH, 'npy'))
    for fil in range(len(traceFILES)):
        trace = f.load_TRACE(tracePATH+traceFILES[int(fil)])
        chan = trace['meta']['Channel']
        for key in chan:
            if chan[key][0]:
                if key == 'CH1':
                    fun.return_trace(trace, amp, 'plot')                        

fnt=14
plt.xlabel(r'$t \  (\mu s)$', fontsize=fnt)
plt.ylabel(r'$I \ (mA)$', fontsize=fnt)

plt.tight_layout()
plt.show()
#plt.savefig(path+'trace_set.png')