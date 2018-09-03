#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from _common import ssh, cycle, simple_command_with_timestamp

import re

sshc, args = ssh([
	{ 'name':'--cycle-time',   'type':int, 'default':5,  'help':'How long should each cycle take' },
], """
Just run the "diag sys session stat" and "diag sys session6 stats" comands every
`--cycle-time` seconds and add the timestamp at the beginning of each line.
""")

def do(sshc):
	etime = ParserCurrentTime(sshc).get()
	
	print simple_command_with_timestamp(sshc, etime, "diag sys session stat", "ipv4")
	print simple_command_with_timestamp(sshc, etime, "diag sys session6 stat", "ipv6")

if __name__ == '__main__':
	try:
		cycle(do, {
			'sshc': sshc, 
		}, args.cycle_time, debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

