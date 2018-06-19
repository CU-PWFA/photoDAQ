# photoDAQ

## Repository for DAQ development

### Setup USB device access

For interfacing with USB devices, we use pyusb (NOTE: a lot of USB devices can be controlled just using pyserial, for these devices you can ignore this). 
Out of the box pyusb does not have access to the USB ports unless it is run as sudo, this can be changed by udev rule.
Open any file in /lib/udev/rules.d/ and add the line (I save in 10-local.rules)
```
ACTION=="add", SUBSYSTEMS=="usb", ATTRS{idVendor}=="171b", ATTRS{idProduct}=="2001", MODE="660", GROUP="plugdev"
```
Then you need to add your username to the plugdev group using
```
adduser username plugdev
```
Finally, force the udev system to restart and see the changes, the device will probably need to be unplugged.
```
sudo udevadm control --reload
```
```
sudo udevadm trigger
```

### Setup USB serial devices

The only thing we need to do for USB serial devices is find the port they are on.
Run the command
```
dmesg | grep tty
```
to find the device list. 
The part that says "ttyACMX" says that the device is on port X.

### Permissions

The user needs to be added to dialout, plugdev, and tty. Use the command
```
sudo usermod -a -G <group> <username>
```
The user will need to logout and log back in for the changes to take effect.

### pyvisa

To see if everything is installed correctly for pyvisa use
```
python -m visa info
``` 

### pyvisa-py bug

There is a bug in pyvisa-py that is fixed in the latest development version but not the latest release.
It makes the host try and read data an extra time from the oscilloscope, the second read times out making the oscilloscope reply really slow.
To fix in pyvisa-py -> usb.py change line 98 to read
```
lambda current: True
```

### pyCapture

When installing pyCapture in an enviornment, you need to run python as root. However, the root user doesn't know you are in an enviornment and doesn't install the package in the enviornment. Just point sudo to the correct python and it all works fine, from the the directory where pyCapture was extracted I use the command
```
sudo ~/anaconda3/envs/CU-PWFA/bin/python setup.py install
```

### Setup ethernet for the cameras

The cameras are setup to operate in LLO (Link-Local Only mode). Once the camera is connected, the small LED on the back will begin to blink. If it blinks three times in a row about every second, then the camera is in LLO mode, if it doesn't blink three times it is in another mode. The wired connection in linux needs to be setup as an LLO connection in order to recognize the camera. Click on the connections button in the top right corner, then go to edit connections. In the menu that pops up select the etherent connection the camera is connected to and click edit. Go to the IPv4 tab and change the method to Link-Local Only and flyCap2 should detect the camera.

The recieve memory buffer needs to be increased to prevent the annoying image inconsistency error. To do this run the command
```
sudo sysctl -w net.core.rmem_max=1048576 net.core.rmem_default=1048576
```
To make the changes persist after a reboot add the following lines to etc/sysctl.conf
```
#net.core.rmem_max=1048576
#net.core.rmem_default=1048576
```
