# photoDAQ

## Repository for DAQ development

### Setup USB device access

For interfacing with USB devices, we use pyusb. 
Out of the box pyusb does not have access to the USB ports unless it is run as sudo, this can be changed by udev rule.
Open any file in /lib/udev/rules.d/ and add the line
```
ACTION=="add", SUBSYSTEMS=="usb", ATTRS{idVendor}=="171b", ATTRS{idProduct}=="2001", MODE="660", GROUP="plugdev"
```
Then you need to add your username to the plugdev group using
```
adduser username plugdev
```
Finally, force the udev system to restart and see the changes, the device will probably need to be unplugged.
```
sudo udevadm control --reload (that is minus minus reload)
```
```
sudo udevadm trigger
```
