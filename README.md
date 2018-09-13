# FortiMonitor

This is a set of utilities to make FortiGate troubleshooting easier. 

Most of the utilities are command line based and connect to the FortiGate over SSH.

## Utilities 

If you are interested in automatic command execution based on (possibly predefined) XML files, check the [script.py utility wiki page](https://github.com/ondrejholecek/fortimonitor/wiki/utilities-script.py).

For the comprehensive list of the all the utilities and their description, please see [utilities wiki page](https://github.com/ondrejholecek/fortimonitor/wiki/Utilities).

## Supported client systems

At this moment (Sep 7, 2018) all the utilities were tested and work correctly on (all 64bit):
- MacOS High Sierra (10.13.6) with [Homebrew](https://brew.sh/)
- Linux Debian 10 (Buster)
- Linux Debian 9 (Stretch)
- Windows 10 

Note that Debian 8 (Jessie) does not have the right version of Paramiko and it is quite challenging
to make this program running there. I would rather suggest to upgrade to supported Debian version.

## Supported FortiGate hardware and fireware

All FortiGate hardware should be supported, however some utilities need a definition of the platform,
which is currently very incomplete. Please raise an "Issue" here to ask for the right definition.

Supported should be all FortiOS versions starting with 5.4, however it was not tested and there might
be some differencies in different versions that might make some utilities incompatible. Please raise
an "Issue" here if you find such problem.

## Usage

Basicaly all the programs you may want to use are located in "utilities" directory. All of them accept "-h" parameter
to display the options that can be used. Following options are shared by most of the programs:

```
--host HOST                 FortiGate hostname or IP address
--user USER                 User name to log in as, default "admin"
--password PASSWORD         Password to log in with, default empty
--credfile CREDFILE         File to read the credentials from 
--port PORT                 SSH port, default 22
--time-format {human-with-offset,human,timestamp,iso}  Format of the date and time
--time-source {device,local}                           How to retrieve data and time
--debug                     Enable debug outputs
--manual                    Show manual
--ignore-ssh-key            Ignore SSH server key problems
--max-cycles MAX_CYCLES     Maximum cycles to run
```

### Logging in 
You can either provide the username and password on command line with parameters `--user` and `--password` or you can
save them in a file and use `--credfile` option. The file should consist of two lines, the first one being the username 
and the second the password.

### Timestamps
Most of the programs automatically prepend every output line with a timestamp to make it easy to save the output into a text
file and analyze it later. 

By default, the timestamp is printed in human readable format with the timezone offset (e.g. `2018-09-04 11:33:27+02:00`) but
it can be changed using `--time-format` parameter to the humand readable without offset or a unix timestamp which is better
usable in subsequent scripts.

The time on the FortiGate device is used by default and the timezone is calculated based on the different from the local
time on your computer (that means the local computer time must be correct). Alternatively you can choose to use local time
directly with the `--time-source` option. 

### Security
The programs expect that the public SSH key of the FortiGate is already present in the "known hosts" file (that happens when
you connect to the FortiGate for first time using the standard SSH client. If you don't care about the remote key validity
(or you are running this on Windows) the `--ignore-ssh-key` parameter can be used.

### Limiting the number of cycles

Most of the utilities  accept `--max-cycles` option which limits the number of cycles to go through. 

By default this is unlimited, so the program will run "forever".

### More options

There are another parameters that vary depending on what program you are running. All utilities accept `-h` option that show
both the shared and the local options.

Some utilities also accept `--manual` parameter which prints a more detailed information about the utility.




