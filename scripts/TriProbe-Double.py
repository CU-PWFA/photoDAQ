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
from scipy.optimize import curve_fit

from matplotlib import rc
rc('mathtext', default='regular')

def line(x, m, b):
    return m*x + b

f.PATH = f.get_file_path()
path = 'TRACE/year_2018/month_10/day_19/'

file = 'IV-Curve_SET_1-3.npy'
data = np.load(f.PATH+path+file).item()

crnt = data['Currnt']
volt = data['Voltage']

Vp1 = 3
Vp2 = -3

Ip1 = crnt[np.round(volt, 1)==Vp1]
Ip2 = -crnt[np.round(volt, 1)==Vp2]

I_set = crnt[(crnt > -Ip2) & (crnt < Ip1)]
V_set = volt[(crnt > -Ip2) & (crnt < Ip1)]
Ie2 = I_set + Ip2

log = np.log((Ip1+Ip2)/Ie2 - 1)
popt, pcov = curve_fit(line, V_set, log)

fig = plt.figure()
ax = fig.add_subplot(111)
fnt = 14

vplot = np.linspace(Vp2, Vp1, 100)
ax.scatter(V_set, log, s=10, c='b')
plt.plot(vplot, line(vplot, *popt), color='k')
ax.set_xlabel('Bias Voltage (V)', color=c, fontsize=fnt)
ax.set_ylabel('$\ln (\Gamma)$', color=c, fontsize=fnt)
ax.set_title('Temp: %0.2f eV' % (-1/popt[0]), color=c, fontsize=fnt)

plt.tight_layout()
#plt.show()
plt.savefig(f.PATH+path+'IV_TEMP_1-3.png')
