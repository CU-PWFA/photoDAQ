#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  7 17:05:32 2018

@author: cu-pwfa
"""

import instruments as ik

for i in range(10000):
    try:
        srs = ik.srs.SRSDG645.open_tcpip('169.254.248.180', i)
        print(i)
    except:
        print('%s failed' % str(i))
