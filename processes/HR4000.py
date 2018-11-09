#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 18:03:07 2018

@author: robert
"""

from processes.process import Process

class HR4000(Process):
    def save_spectrum(self):
        """ Save spectrum 
        file=the filename in which you want to save
        """        
        np.save(file,self.get_spectrum)
    
    def show_spectrum_plot(self):
        """ Show the plot of spectral lines"""
        plt.plot(self.get_wavelength,self.get_intensity)
    
    def live_stream_spectro():
    pass

