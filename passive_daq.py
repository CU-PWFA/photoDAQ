import numpy as np
import time

devices = {}

def setupScope(instr):
	global PS
	global OS
	global voltages
	PS = instr['KA3005P']
	OS = instr['TDS2024C']

	N = 160;
	voltages = np.linspace(4.00, 30.00, N)
	PS.turn_on
	OS.acquire_off()
	OS.set_acquisition_stop("SEQuence")
	OS.set_acquisition_mode("AVErage")
	OS.set_average_num(4)

def measureScope(i):
	PS.set_voltage(voltages[i])
	time.sleep(0.1) # Give the power supply enough time to set the voltage
	OS.acquire_on()
	time.sleep(1)
	t, y, pre = OS.retrieve_current_waveform()
	ret = {
	        'KA3005P' : {
	                'meta'      : {},
	                'voltage'   : voltages[i]
	                },
	        'TDS2024C' : {
	                't'         : t,
	                'y'         : y,
	                'meta'      : pre
	                }
	        }
	return ret


def setupCam(instr):
	global devices
	devices = instr
	for name in instr:
	    if instr[name].type == 'Camera':
	        cam = instr[name]
	        cam.start_capture()
        
def measureCam(i):
	ret = {}
	for name in devices:
	    if devices[name].type == 'Camera':
	        cam = devices[name]
	        image = cam.retrieve_buffer()
	        ret[name] = {
	                    'meta'  : {},
	                    'image' : image
	                    }
	return ret