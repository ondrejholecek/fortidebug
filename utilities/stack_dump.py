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
	{ 'name':'--process-name', 'required':True, 'help': 'Regular expression on the process name to dump stack for' },
], """
This program take the process name as a parameter and then every `--cycle-time` it print the current 
stack trace for this program. This stack trace contains the exact part of the code which is executing.

If there are multiple processes of the same name, the stack dump is printent for all of them.
""")

def do(sshc, process_re):
	etime = ParserCurrentTime(sshc).get()
	
	processes = ParserProcesses(sshc).get()
	for process in processes:
		if not process_re.search(process['cmd']): continue
		print simple_command_with_timestamp(sshc, etime, "fnsysctl cat /proc/%i/stack" % (process['PID'],),
			"'%s':%i:%s" % (process['cmd'], process['PID'], process['state'],) )
		sys.stdout.flush()

if __name__ == '__main__':
	try:
		cycle(do, {
			'sshc': sshc, 
			'process_re': re.compile(args.process_name),
		}, args.cycle_time, debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

