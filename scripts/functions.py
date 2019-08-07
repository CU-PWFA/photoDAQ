#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 10:45:04 2019

@author: michael
"""
from os import listdir
import matplotlib.pyplot as plt
import numpy as np


def getName(root, dataset, name):
    yr = '20'+dataset[0][0:2]
    mn = dataset[0][2:4]
    dy = dataset[0][4:6]
    path = root+'/year_{}/month_{}/day_{}/'.format(yr, mn, dy)
    
    st_1 = int(dataset[0][6:10])
    st_2 = int(dataset[-1][6:10])
    name = name.format(st_1, st_2)
    
    return path+name

def list_files(directory, extension):
    return (f for f in listdir(directory) if f.endswith('.' + extension))

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
    x = -b/(2.*a)
    return a*x*x+b*x+c

def line(x, m, b):
    return m*x + b

def ind_closest_to_val(arr, val):
    arr_chk = arr-val
    return np.argmin(abs(arr_chk))

def trace_analysis(key, trace, time, amp=1000):
    if key == 'CH2':
        y = trace['y']
        return np.mean(y)
    
    elif key == 'CH1':
        t = trace['t']
        y = trace['y']
        
        y_before_trig = y[t<=0]
        for ind, val in enumerate(y_before_trig):
            sig = np.std(y_before_trig[:-ind])
            if sig <= 0.001:
                break
        grnd = np.mean(y_before_trig[:-ind])
        y = y - grnd
        
        y_before_trig_len = len(y_before_trig)
        y_before_trig_rev = y_before_trig[::-1]
        for ind, y_val in enumerate(y_before_trig_rev):
            indx = y_before_trig_len - ind
            if (abs(y[indx]) <= 0.01) and (np.mean(y[:indx]) <= 0.01):
                ind_begin = indx
                break
            ind_begin=0
        
        y_red = y[ind_begin:]
        t_red = np.arange(len(y_red))
        
        t_inc = float(trace['meta']['Wavefront ID'][31:38])
        t_red = t_red*t_inc*1000
        
        y_red = y_red[t_red<=2]
        crnt = -y_red/amp
        t_red = t_red[t_red<=2]
        
        plt.plot(t_red, crnt*1000)
        
        return -y_red[ind_closest_to_val(t_red, time)]/amp
    
    else:
        y = trace['y']
        return np.mean(y)

def return_time(trace, trig):
    t = trace['t'][1::] 
    time = t[trig::] - t[trig]
    
    return time

    
def return_trace(trace, amp, trig):
    y = trace['y']
    crnt = - y[trig::] / amp

    return crnt
    

def average_trace(trace, sign, trig):
    y = sign * trace['y'][trig::]
    
    return np.array([np.mean(y), np.std(y)])