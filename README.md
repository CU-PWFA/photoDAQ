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
It makes the host try and read data an extra time from the oscilloscope, the second read times out making the oscilloscope replies really slow.
To fix in pyvisa-py -> usb.py change line 98 to read
```
lambda current: True
```