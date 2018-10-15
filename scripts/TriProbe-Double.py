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

def line(X, m, b):
    npts = len(X)
    Y = np.empty(npts)
    for i in range(npts):
        Y[i] = m*X[i]+b
    return Y

f.PATH = f.get_file_path()

cnt = 0
shot = 1
lng = 57
dataset = '1810080036'

V_set = np.empty(lng)
I_set = np.empty(lng)

while shot<=113:
    SET = f.load_SET('ttyUSB0', dataset, shot)
    TRACE = f.load_TRACE('TDS2024C', dataset, shot)
    
    v2 = np.max(TRACE['y'])
    v3 = SET['voltage']
    
    I_set[cnt] = v2/10.
    V_set[cnt] = v3
    
    cnt+=1
    shot=2*cnt+1
    
V_p1 = 10
I_p1 = I_set[np.where(V_set==V_p1)][0]
    
Vo = V_set[(V_set <= V_p1)]
Io = I_set[0:len(Vo)]
m, b = np.polyfit(Vo, Io, 1)

I_e2 = I_p1 - b
G = I_e2/(2*I_p1)
R = 1./m
temp = round((G-G*G)*R*2*I_p1, 2)

O_set = line(Vo, m, b)

Vf = V_set[(V_set > V_p1)]
If = I_set[len(I_set)-len(Vf):len(I_set)]
m, b = np.polyfit(Vf, If, 1)
F_set = line(Vf, m, b)
    
fig = plt.figure()
ax = fig.add_subplot(111)
fnt = 14
c='k'

ax.plot(V_set, I_set, color=c)
ax.plot(Vo, O_set, color=c, ls='--')
ax.plot(Vf, F_set, color=c, ls='--')

ax.set_ylabel('$I_{13} \ (mA)$', color=c, fontsize=fnt)
ax.set_xlabel('$V_{d3} \ (V)$', color=c, fontsize=fnt)

#ax.set_ylim(0, np.max(I_set))

ax.spines['bottom'].set_color(c)
ax.spines['top'].set_color(c)
ax.tick_params(axis='x', colors=c, labelsize=fnt-2)
ax.tick_params(axis='y', colors=c, labelsize=fnt-2)
ax.set_title('Temp: {} eV'.format(temp), color=c, fontsize=fnt)

plt.legend()
plt.tight_layout()
path = f.get_dirName_from_dataset('TRACE', dataset)
plt.savefig(path+'/TriProbPlot-Double.png')