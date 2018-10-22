# FortiDebug

This is a set of utilities to make FortiGate troubleshooting easier. 

## Utilities 

Most of the [utilities](https://github.com/ondrejholecek/fortidebug/wiki/Utilities) are command line based and connect to the FortiGate over SSH.

Different [utilities](https://github.com/ondrejholecek/fortidebug/wiki/Utilities) can execute various commads on FortiGate and usually create some kind of human understandable summary.  Some can represent the output in semi-graphical form more suitable for real-time troubleshooting and others can create an output prepared for further analysis with custom scripts.

If you are interested in automatic command execution based on (predefined or custom made) XML files, check the [script.py utility wiki page](https://github.com/ondrejholecek/fortidebug/wiki/utilities-script.py).

For the comprehensive list of the all the utilities and their description, please see [utilities wiki page](https://github.com/ondrejholecek/fortidebug/wiki/Utilities).

There are also some [auxiliary programs](https://github.com/ondrejholecek/fortidebug/wiki/Auxiliary) that can help with different format and timestamps conversions or with signing custom URL scripts for [script.py utility](https://github.com/ondrejholecek/fortidebug/wiki/utilities-script.py).

## Supported client systems

At this moment all the utilities should work correctly on:
- Windows 10 
- Linux Debian 9 (Stretch) and newer
- MacOS High Sierra (10.13.6) with [Homebrew](https://brew.sh/)

## Installation and usage

The project is hosted on [GitHub](https://github.com/ondrejholecek/fortidebug) and you can simply download or clone it. For detailed instructions see the [Installation page on wiki](https://github.com/ondrejholecek/fortidebug/wiki/Installation).

Most of the utilities are controlled in a similar way and they share the same basic parameters. To find how to use them together with desciption of the shared parameters, see the [Usage page on wiki](https://github.com/ondrejholecek/fortidebug/wiki/Usage).

Each utility also has its own page on Wiki where the local parameters, bahaviors and priciples are written. You can find the links to all utilities on the [Utilities wiki page](https://github.com/ondrejholecek/fortidebug/wiki/Utilities).

## Supported FortiGate hardware 

All FortiGate hardware should be supported. 

Some utilities need a definition of the platform (only [nic_utilization.py](https://github.com/ondrejholecek/fortidebug/wiki/utilization-nic_utilization.py) at this moment), which is currently very incomplete. It is not a problem to add a new definition, please just raise an "Issue" here.

## Supported FortiOS versions

Supported should be all FortiOS versions starting with 5.4, however it was not tested and there might
be some differencies in different versions that might make some utilities incompatible. Please raise
an "Issue" here if you find such problem.

## Author

The project is written and maintained by [Ondrej Holecek](https://www.holecek.eu/).

This is a private project that I write in my free time and it is not an official Fortinet product.



