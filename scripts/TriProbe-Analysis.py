#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 12 09:41:06 2018

@author: cu-pwfa
"""

import sys
sys.path.append('../')
import numpy as np
import matplotlib.pyplot as plt
import file as f

from matplotlib import rc
rc('mathtext', default='regular')

def parabFIT(x_ray, y_ray):
    x1, x2, x3 = x_ray    
    X = np.array([[x1*x1, x1, 1],
                  [x2*x2, x2, 1],
                  [x3*x3, x3, 1]])
    X_inv = np.linalg.inv(X)
    Y = y_ray
    return np.dot(X_inv, Y)

def parabMIN(params):
    a, b, c = params
    return -b/(2.*a)

def parabPLOT(params, npts=100000):
    a, b, c = params
    pRab = lambda x: a*x*x + b*x + c
    
    x_min = parabMIN(params)
    x_val = np.arange(x_min-.5*npts, x_min+.5*npts)
    y_val = np.empty(len(x_val))
    for i, x in enumerate(x_val):
        y_val[i] = pRab(x)
        
    return np.array([x_val, y_val])

def func(v2, v3, t):
    phi = 11604.2587/t
    num = 1. - np.exp(-phi*v2)
    den = 1. - np.exp(-phi*v3)
    return num/den - 0.5

def func_root(func, t0, params):
    v2, v3 = params
    FUN = lambda t: func(v2, v3, t)
    val = FUN(t0)
    sign_prev = np.sign(val)
    sign_crnt = sign_prev
    while sign_crnt == sign_prev:
        t0+=1
        val = FUN(t0)
        sign_crnt = np.sign(val)
    t_ray = np.array([t0-1, t0, t0+1])
    v_ray = np.array([FUN(t0-1), FUN(t0), FUN(t0+1)])**2
    
    params = parabFIT(t_ray, v_ray)
    return parabMIN(params)

f.PATH = f.get_file_path()

cnt = 0
shot = 0
lng = 57
dataset = '1810080036'

T_set = np.empty(lng)
V2_set = np.empty(lng)
V3_set = np.empty(lng)

while shot<=112:
    print(shot)
    SET = f.load_SET('ttyUSB0', dataset, shot)
    TRACE = f.load_TRACE('TDS2024C', dataset, shot)
    
    v2 = np.max(TRACE['y'])
    v3 = SET['voltage']
    
    V2_set[cnt] = v2
    V3_set[cnt] = v3

    T_set[cnt] = func_root(func, 1, [v2, v3])*.000086174
    cnt+=1
    shot=2*cnt
    
T_avg = np.mean(T_set)

fig = plt.figure()
ax1 = fig.add_subplot(111)
fnt = 14
c0='k'
c1='b'
c2='r'

lns1 = ax1.plot(V3_set, T_set, label='Plasma Temperature', c=c1)
#lns11 = ax1.plot(V3_set, [T_avg]*lng, label='Average Temperature', c=c1, ls='--')

ax1.set_xlabel('$V_{d3} \ (V)$', color=c0, fontsize=fnt)
ax1.set_ylabel('Temp (eV)', color=c1, fontsize=fnt)

ax1.spines['bottom'].set_color(c0)
ax1.spines['top'].set_color(c0)
ax1.tick_params(axis='x', colors=c0, labelsize=fnt-2)
ax1.tick_params(axis='y', colors=c1, labelsize=fnt-2)
ax1.set_title('Triple Probe in Air Plasma', color=c0, fontsize=fnt)

ax2 = ax1.twinx()
lns2 = ax2.plot(V3_set, V2_set, label='Floating Potential', c=c2)
#ax2.set_ylim(np.min(T_set), np.max(T_set))
ax2.set_ylabel('$V_{d2} \ (V)$', color=c2, fontsize=fnt)
ax2.tick_params(axis='y', colors=c2, labelsize=fnt-2)

lns = lns1+lns2
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, loc=0)

plt.tight_layout()
path = f.get_dirName_from_dataset('TRACE', dataset)
plt.savefig(path+'/TriProbPlot.png')
