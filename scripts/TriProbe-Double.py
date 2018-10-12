#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 12 15:57:46 2018

@author: cu-pwfa
"""

import sys
sys.path.append('../')
import numpy as np
import matplotlib.pyplot as plt
import file as f

f.PATH = f.get_file_path()

cnt = 0
shot = 1
lng = 57
dataset = '1810080036'

V_set = np.empty(lng)
I_set = np.empty(lng)
while shot<=113:
    print(shot)
    SET = f.load_SET('ttyUSB0', dataset, shot)
    TRACE = f.load_TRACE('TDS2024C', dataset, shot)
    
    v2 = np.max(TRACE['y'])
    v3 = SET['voltage']
    
    I_set[cnt] = v2/10.
    V_set[cnt] = v3
    
    cnt+=1
    shot=2*cnt+1
    
fig = plt.figure()
ax = fig.add_subplot(111)
fnt = 14
c='k'

ax.plot(V_set, I_set, color=c)

ax.set_ylabel('$I_{13} \ (mA)$', color=c, fontsize=fnt)
ax.set_xlabel('$V_{d3} \ (V)$', color=c, fontsize=fnt)

ax.spines['bottom'].set_color(c)
ax.spines['top'].set_color(c)
ax.tick_params(axis='x', colors=c, labelsize=fnt-2)
ax.tick_params(axis='y', colors=c, labelsize=fnt-2)
ax.set_title('Triple Probe in Air Plasma', color=c, fontsize=fnt)

plt.legend()
plt.tight_layout()
path = f.get_dirName_from_dataset('TRACE', dataset)
plt.savefig(path+'/TriProbPlot-Double.png')