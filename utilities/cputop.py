#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.Processes import ParserProcesses
from parsers.ProcessCPU import ParserProcessCPU
from _common import ssh, prepend_timestamp

import time
import sys
import re

sshc, args = ssh([
	{ 'name':'--max',          'type':int, 'default':25, 'help':'How many lines of output to show (0 for all)' },
	{ 'name':'--sort-by',      'default':'total', 'choices':['total', 'user', 'system', 'pid'], 'help':'How to sort the output' },
	{ 'name':'--collect-time', 'type':int, 'default':1,    'help':'How long to collect data in each cycle' },
	{ 'name':'--pid-group',    'type':int, 'default':1000, 'help':'How many PIDs to query at once' },
	{ 'name':'--process-name', 'default':None, 'help': 'Regular expression on the process name' },
	{ 'name':'--cpu',          'type':int, 'default':None, 'action':'append', 'help':'CPU number to show processes on (can repeat)' },
	{ 'name':'--state',        'type':str, 'default':None, 'action':'append', 'help':'Process state to show (can repeat)' },
	{ 'name':'--hz',           'type':int, 'default':100,  'help':'CONFIG_HZ of device, do not change' },
], """
This is very similar to FortiGate's "diag sys top" program, with following differencies:
- also the kernel threads are shown
- the cpu the process was last seen running on is shown
- cpu utilization is split between "kernel" and "userland" utilization for each process
- it displays the "global" utilization (percentage of all possible CPU ticks)
- and it also displays "of counsumed" utilization (percentage out of the running processes)
- it DOES NOT display any memory statistics

Different sorting algorithms can be applied (see help for `--sort-by` option).

It is possible to only shown the processes in the specific state (see help for `--state` option),
or processes running on a specific CPU (see help for `--cpu` option).
""")

def do(sshc, pid_group_count, collect_time, max_lines, sort_by, process_name, cpus, states, hz):
	# filter only desired process (or all if process == None)
	if process_name != None: process_re = re.compile(process_name)
	else: process_re = None

	processes = []
	for process in ParserProcesses(sshc).get():
		if process_re == None or process_re.search(process['cmd']):
			processes.append(process)
	
	# save information about applied filters
	filters_applied = "Applied filters: "
	if cpus != None         : filters_applied += "CPU[%s] " % (",".join(str(cpu) for cpu in cpus))
	if states != None       : filters_applied += "STATE[%s] " % (",".join(str(state) for state in states))
	if process_name != None : filters_applied += "NAME[%s] " % (process_name,)
	if max_lines != 0       : filters_applied += "TOP[%i] " % (max_lines,)
	if sort_by != None      : filters_applied += "SORT[%s] " % (sort_by,)

	#
	previous = None
	while True:
		etime = ParserCurrentTime(sshc).get()
	
		# this is to be able to send group of PIDs at once
		current = []
		for i in range(0, len(processes), pid_group_count):
			try:
				pids = []
				for y in range(pid_group_count): pids.append(processes[i+y]['PID'])
			except IndexError:
				pids = []
				for p in processes[i:]:
					pids.append(p['PID'])
	
			current.append(ParserProcessCPU(sshc).get(pids))
	
		if previous != None:
			overall_cpus = {'user':0, 'system':0, 'idle':0, 'iowait':0, 'irq':0, 'softirq':0}
			util = {}
			for i in range(len(previous)):
				diff_overall, diff_processes, diff_time = ParserProcessCPU(sshc).diff(previous[i], current[i])
				for pid in diff_processes.keys():
					if cpus != None and diff_processes[pid]['last_cpu'] not in cpus: 
						continue
					if states != None and diff_processes[pid]['last_state'] not in states: 
						continue

					util[pid] = {}
					util[pid]['name']       = diff_processes[pid]['name']
					util[pid]['pid']        = pid
					util[pid]['last_cpu']   = diff_processes[pid]['last_cpu']
					util[pid]['last_state'] = diff_processes[pid]['last_state']

					if diff_overall['user'] != 0:
						util[pid]['user']   = (float(diff_processes[pid]['user'])*100) / diff_overall['user']
					else:
						util[pid]['user']   = float(0.0)

					if diff_overall['system'] != 0:
						util[pid]['system'] = (float(diff_processes[pid]['system'])*100) / diff_overall['system']
					else:
						util[pid]['system'] = float(0.0)

					if diff_time != 0:
						util[pid]['global_user']   = (float(diff_processes[pid]['user'])*100) / (diff_time*hz)
						util[pid]['global_system'] = (float(diff_processes[pid]['system'])*100) / (diff_time*hz)
					else:
						util[pid]['global_user'] = float(0.0)
						util[pid]['global_system'] = float(0.0)

					util[pid]['total']  = util[pid]['user'] + util[pid]['system']

				# overall - we will count an average
				for tmp in ['user', 'system', 'idle', 'iowait', 'irq', 'softirq']:
					overall_cpus[tmp] += (float(diff_overall[tmp])*100) / (diff_time*hz)

			for tmp in overall_cpus.keys(): # max average and convert to percentages
				if len(previous) > 0: overall_cpus[tmp] = overall_cpus[tmp] / len(previous)
				else: overall_cpus[tmp] = 0

			print_formatted(util, overall_cpus, max_lines, etime, sort_by, filters_applied)

		previous = current
		time.sleep(collect_time)

def print_formatted(util, overall_cpus, top, last_time, sortby, filters_applied):
	cnt = 0

	print "\x1b[2J\x1b[H\033[1mCPU per process utilization    (written by Ondrej Holecek <oholecek@fortinet.com>)\033[0m"
	print prepend_timestamp("Overall CPU utilization: %3.1f %% user, %3.1f %% system, %3.1f %% idle" % (
		overall_cpus['user'], overall_cpus['system'], overall_cpus['idle'],
	), last_time, 'pcpu')
	print prepend_timestamp("Overall CPU utilization: %3.1f %% iowait, %3.1f %% irq, %3.1f %% softirq" % (
		overall_cpus['iowait'], overall_cpus['irq'], overall_cpus['softirq'],
	), last_time, 'pcpu')
	print prepend_timestamp(filters_applied, last_time, 'pcpu')
	print prepend_timestamp("                                 OF CONSUMED      GLOBAL    ", last_time, 'pcpu')
	print prepend_timestamp("   PID NAME             STATE   USER  SYSTEM    USER  SYSTEM  CPU#", last_time, 'pcpu')
	for pid in sorted(util.keys(), key=lambda x: util[x][sortby], reverse=True):
		line = "%6i %-20s %s  " % (pid, util[pid]['name'], util[pid]['last_state'],)

		part = "%3.1f" % (util[pid]['user'],)
		if len(part) < 5: part = "%s%s" % (" "*(5-len(part)), part,)
		line += part + " "

		part = "%3.1f" % (util[pid]['system'],)
		if len(part) < 7: part = "%s%s" % (" "*(7-len(part)), part,)
		line += part + " "

		part = "%3.1f" % (util[pid]['global_user'],)
		if len(part) < 7: part = "%s%s" % (" "*(7-len(part)), part,)
		line += part + " "

		part = "%3.1f" % (util[pid]['global_system'],)
		if len(part) < 7: part = "%s%s" % (" "*(7-len(part)), part,)
		line += part + " "

		line += "  %3i" % (util[pid]['last_cpu'],)

		print prepend_timestamp(line, last_time, 'pcpu')

		cnt += 1
		if top != 0 and cnt >= top: break

	sys.stdout.flush()

if __name__ == '__main__':
	try:
		do(sshc, args.pid_group, args.collect_time, args.max, args.sort_by, args.process_name, args.cpu, args.state, args.hz)
	except KeyboardInterrupt:
		sshc.destroy()

