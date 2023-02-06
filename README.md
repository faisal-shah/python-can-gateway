Python utilities for bridging CAN devices

# pycangw.py
This is a generic bridge between two python-can devices.
```
usage: pycangw.py [-h] config

CAN gateway using python-can

The config file (JSON) is expected to be an array of
dictionaries - each of which represents one python-can
bus. Each dictionary will be passed to the Bus
constructor like so: can.Bus(**dict) .

positional arguments:
  config

options:
  -h, --help  show this help message and exit
```

# kv2socand
Creates a bridge between socketcand (via TCP port) and a kvaser device.
```
usage: kv2socand [-h] [-ch CHANNEL] [-addr ADDRESS] [-port PORT] [-dev DEVICE] [-log LOGLEVEL]

Autodetect socketcand, and create bridge with kvaser

options:
  -h, --help            show this help message and exit
  -ch CHANNEL, --channel CHANNEL
                        Kvaser channel
  -addr ADDRESS, --address ADDRESS
                        socketcand host address
  -port PORT, --port PORT
                        socketcand port
  -dev DEVICE, --device DEVICE
                        socketcand device (e.g. vcan0)
  -log LOGLEVEL, --loglevel LOGLEVEL
                        logging level
```

# socketcand_utils.py
Utilities for interacting with socketcand
## detect()
Detects the UDP broadcast from socketcand, and returns the SocketCAN devices, and host:port address where the server is running.

# client.py (don't use)
Implementation of the socketcand ASCII protocol, and bridge to a python-can device. I wrote this before I found out that python-can already had a (albeit bugy) socketcand interface. Fixed the bugs in python-can and upstreamed the changes - no need to use client.py now .

# Bridging WSL SocketCAN and Windows CAN device
WSL SocketCAN device <--socketcand--> TCP socket <--kv2socand--> Windows Kvaser Device

1. Run socketcand (SocketCAN daemon) in WSL. This creates a bridge between a WSL SocketCAN device, and a TCP socket.
2. Run kv2socand in Windows. This bridges the TCP socket with a Kvaser device.
3. Profit.

![image](https://user-images.githubusercontent.com/37458679/215551950-972b1778-e1c2-401c-8743-251763f6f84a.png)

Components in blue are additional software to install and run to establish the bridge.

## socketcand
Get it from here: [https://github.com/linux-can/socketcand](https://github.com/linux-can/socketcand)
Build and install:
```
# Build
$ autoupdate
$ ./autogen.sh
$ ./configure
$ make
# Install
$ sudo make install
# Run socketcand bridging vcan0 to loopback network interface, redirect output to /dev/null, and put in background
$ socketcand -l eth0 -i vcan0 > /dev/null >2&1 &
```

## kv2socand
Get it from here [https://github.com/faisal-shah/python-can-gateway](https://github.com/faisal-shah/python-can-gateway)
```
> python3 -m venv .venv
> .venv\Scripts\activate.bat
> pip install --proxy http://<user>:<pass>@<proxy host> -r requirements.txt
> python3 kv2socand -ch 1
INFO:__main__:Starting Gateway
INFO:can.interfaces.socketcand.socketcand:SocketCanDaemonBus: connected with address ('172.22.160.1', 53900)
INFO:can.kvaser:loaded kvaser's CAN library
INFO:can.kvaser:CAN Filters: None
INFO:can.kvaser:Got configuration of: {'single_handle': True, 'accept_virtual': True}
INFO:can.kvaser:Found 3 available channels
INFO:can.kvaser:0: Kvaser Leaf SemiPro HS, S/N 15018 (#1)
INFO:can.kvaser:1: Kvaser Virtual CAN Driver, S/N 0 (#1)
INFO:can.kvaser:2: Kvaser Virtual CAN Driver, S/N 0 (#2)
INFO:can.kvaser:Hardware filtering has been disabled
```

## Testing
Run ```candump vcan0``` (or whichever interface you are bridging) in WSL.
Run CanKing in windows, and use Messages->Traffic Generator to generate some CAN traffic.
It should show up in candump

Run ```cangen vcan0``` (or whichever interface you are bridging) in WSL. This will generate CAN traffic.
Observe CAN traffic in CanKing
