#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys

from parsers.CurrentTime import ParserCurrentTime
from parsers.Processes import ParserProcesses
from parsers.ProcessStat import ParserProcessStat
from _common import ssh, cycle

sshc, args = ssh([
	{ 'name':'--cycle-time', 'type':int, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--pid-group',  'type':int, 'default':50, 'help':'How many PIDs to query at once' },
], """
This program displays the processes running on each CPU (core). 

Be aware that the processes can jump between different cores during their lifetime,
and this collects the actual status only once per `cycle-time`, hence this is not
very accurate. 

However, it can be used to identify the process occupying the specific core all the time.
""", supports_script=True)

def do(sshc, pid_group_count):
	processes = ParserProcesses(sshc).get2()
	cpus = {}

	# this is to be able to send group of PIDs at once
	for i in range(0, len(processes), pid_group_count):
		try:
			pids = []
			for y in range(pid_group_count): pids.append(processes[i+y]['PID'])
		except IndexError:
			pids = []
			for p in processes[i:]:
				pids.append(p['PID'])

		for stat in ParserProcessStat(sshc).get(pids):
			if stat['current_CPU'] not in cpus: cpus[stat['current_CPU']] = []
			cpus[stat['current_CPU']].append("'%s'[%s](%i)" % (stat['name'], stat['state'], stat['PID'],))

	etime = ParserCurrentTime(sshc).get()
	
	for cpu in sorted(cpus.keys()):
		print "[%s] CPU#%i: %s" % (etime, cpu, " ".join(cpus[cpu]),)
		
	sys.stdout.flush()
	return etime

if __name__ == '__main__':
	try:
		cycle(do, {
			'sshc': sshc, 
			'pid_group_count': args.pid_group,
		}, args.cycle_time, cycles_left=[args.max_cycles], debug=args.debug, interactive=args.interactive)
	except KeyboardInterrupt:
		sshc.destroy()

