#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.Processes import ParserProcesses
from _common import ssh, cycle, simple_command_with_timestamp

import re
import sys

sshc, args = ssh([
	{ 'name':'--cycle-time',   'type':int, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--command',      'required':True,  'help':'What command to keep running' },
	{ 'name':'--vdom',         'default':None, 'help':'VDOM to use when executing the command' },
	{ 'name':'--mgmt-vdom',    'default':False, 'action':'store_true',  'help':'Use management VDOM to execute the command' },
], """
Execute specific command every `--cycle-time`. 

If there are VDOMs enabled on the device, then by default the command is execute in 'global' context,
but a specific VDOM can be used with `--vdom` option or `--mgmt-vdom` to use the management VDOM automatially.
""")

def do(sshc, command, vdom):
	etime = ParserCurrentTime(sshc).get()
	
	print simple_command_with_timestamp(sshc, etime, command, info=command, vdom=vdom)
	sys.stdout.flush()

if __name__ == '__main__':
	vdom = None

	if args.mgmt_vdom == True and args.vdom != None:
		print "Error: options '--vdom' and '--mgmt-vdom' are mutually exclusive"
		sys.exit(0)
	elif args.mgmt_vdom == True:
		vdom = ''
	elif args.vdom != None:
		vdom = args.vdom

	try:
		cycle(do, {
			'sshc': sshc, 
			'command': args.command,
			'vdom': vdom,
		}, args.cycle_time, debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

