#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.Interrupts import ParserInterrupts
from parsers.ProcessCPU import ParserProcessCPU
from _common import ssh, cycle, simple_command_with_timestamp, prepend_timestamp

import re
import sys

sshc, args = ssh([
	{ 'name':'--collect-time',   'type':float, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--max',   'type':int, 'default':45,  'help':'Maximum lines to show (45 by default)' },
	{ 'name':'--show-zeros',  'default':False, 'action':'store_true',  'help':'Include lines with zero runs' },
	{ 'name':'--summarize', 'default':False, 'action':'store_true',  'help':'Summarize ticks from all CPUs' },
	{ 'name':'--cpu', 'type':int, 'default':[], 'action':'append',  'help':'Summarize ticks from selected CPUs' },
	{ 'name':'--no-soft', 'default':False, 'action':'store_true',  'help':'Do not show softirqs' },
	{ 'name':'--no-hard', 'default':False, 'action':'store_true',  'help':'Do not show hardirqs' },
	{ 'name':'--desc',   'type':str, 'help':'Regex to filter interrupts by description' },
	{ 'name':'--hz',           'type':int, 'default':100,  'help':'CONFIG_HZ of device, do not change' },
], """
""", supports_script=True)

def difference_per_second(old, new, time_difference):
	if 'interrupts' not in old or 'interrupts' not in new: raise Exception('Invalid structures for calculating difference')
	if 'collected_on' not in old or 'collected_on' not in new: raise Exception('Invalid structures for calculating difference')
	if 'cpus' not in old or 'cpus' not in new: raise Exception('Invalid structures for calculating difference')
	if new['cpus'] != old['cpus']: raise Exception('Number of CPUs has changed')

	diff = {}
	for k in new['interrupts'].keys():
		if k not in old['interrupts']: continue

		diff[k] = {}
		for cpu in new['interrupts'][k]['ticks'].keys():
			diff[k][cpu] = int(round(float(new['interrupts'][k]['ticks'][cpu] - old['interrupts'][k]['ticks'][cpu])/time_difference))

		diff[k]['source'] = new['interrupts'][k]['source']

	return diff


def sort_interrupts(diff, cpus='each', ignore_zero=True):
	ss = []

	for k in diff.keys():
		if cpus == 'each':
			for cpu in diff[k].keys():
				if type(cpu) != int: continue
				ss.append( ((k, cpu), diff[k][cpu]) )

		elif cpus == 'total':
			ss.append( ((k, 'total'), diff[k]['total']) )

		elif type(cpus) == tuple:
			summary = 0
			for cpu in cpus:
				summary += diff[k][cpu]
			ss.append( ((k, cpus), summary) )
			
	ret = []
	for s in sorted(ss, key=lambda x: x[1], reverse=True):
		if ignore_zero and (s[1] == 0): continue
		ret.append(s)
	return ret

def do(sshc, cache, max_lines, display_type, hz, soft, hard, show_zeros, description):
	ints  = ParserInterrupts(sshc).get(soft=soft, hard=hard)
	usage = ParserProcessCPU(sshc).get([])
	etime = ParserCurrentTime(sshc).get()
	
	if 'last' not in cache:
		cache['last'] = {
			'interrupts': ints,
			'cpu' : usage,
		}
		return

	time_difference = ints['collected_on'] - cache['last']['interrupts']['collected_on']

	overall_cpus = {}
	for tmp in ['user', 'system', 'idle', 'iowait', 'irq', 'softirq']:
		overall_cpus[tmp] = int(round(((usage['global'][tmp] - cache['last']['cpu']['global'][tmp])*100)/(time_difference*hz)))

	diff = difference_per_second(cache['last']['interrupts'], ints, time_difference)
	diff_sorted_keys = sort_interrupts(diff, display_type, not show_zeros)
	if max_lines != 0: diff_sorted_keys = diff_sorted_keys[:max_lines]

	total_ticks_soft = sum([diff[x]['total'] for x in diff.keys() if diff[x]['source'] == 'soft'])
	total_ticks_hard = sum([diff[x]['total'] for x in diff.keys() if diff[x]['source'] == 'hard'])

	if os.name == 'nt':
		os.system('cls')
		print "Interrupt lines utilization    (written by Ondrej Holecek <oholecek@fortinet.com>)"
	else:
		print "\x1b[2J\x1b[H\033[1mInterrupt lines utilization    (written by Ondrej Holecek <oholecek@fortinet.com>)\033[0m"

	
	filters_applied = "Applied filters: "
	if type(display_type) == tuple: filters_applied += "CPU[" + ",".join([str(x) for x in sorted(display_type)]) + "] "
	elif display_type == 'total': filters_applied += "CPU[total] "
	elif display_type == 'each': filters_applied += "CPU[separate] "
	if max_lines != 0: filters_applied += "TOP[%i] " % (max_lines,)
	if soft and hard: filters_applied += "TYPE[soft,hard] "
	elif soft: filters_applied += "TYPE[soft] "
	elif hard: filters_applied += "TYPE[hard] "
	if show_zeros: filters_applied += "ZERO[yes] "
	else: filters_applied += "ZERO[no] "
	if description != None: filters_applied += "DESC[%s] " % (description,)

	print prepend_timestamp("Overall CPU utilization: %3.1f %% user, %3.1f %% system, %3.1f %% idle" % (
		overall_cpus['user'], overall_cpus['system'], overall_cpus['idle'],
	), etime, 'inttop')
	print prepend_timestamp("Overall CPU utilization: %3.1f %% iowait, %3.1f %% irq, %3.1f %% softirq" % (
		overall_cpus['iowait'], overall_cpus['irq'], overall_cpus['softirq'],
	), etime, 'inttop')
	print prepend_timestamp(filters_applied, etime, 'inttop')
	print prepend_timestamp("%-11s %5s %9s %10s %4s  %s" % ("LINE", "SOURCE", "CPU(s)", "RUNS", "PERC", "DESCRIPTION",), etime, 'inttop')

	if description != None:
		descr_re = re.compile(description)
	else:
		descr_re = None

	for k in diff_sorted_keys:
		((iname, itype), iticks) = k
		source = ints['interrupts'][iname]['source']
		desc = ints['interrupts'][iname]['description']
		if descr_re != None and descr_re.search(desc) == None: continue
		if len(desc) > 30: desc = desc[:25] + "[...]"
		if type(itype) == tuple: itype = 'selected'

		if source == 'soft':
			perc = (iticks*100)/total_ticks_soft
			source_a = 'S'
		elif source == 'hard':
			perc = (iticks*100)/total_ticks_hard
			source_a = 'H'

		print prepend_timestamp("%-16s %1s %9s %10i %4i  %s" % (iname, source_a, itype, iticks, perc, desc,), etime, 'inttop')
	
	cache['last'] = {
		'interrupts': ints,
		'cpu': usage,
	}
	sys.stdout.flush()
	return etime

if __name__ == '__main__':
	itype = 'each'
	if args.summarize: itype = 'total'
	elif len(args.cpu) > 0: itype = tuple(args.cpu)

	soft = True
	if args.no_soft: soft = False
	hard = True
	if args.no_hard: hard = False

	cache = {}
	try:
		cycle(do, {
			'sshc': sshc, 
			'cache': cache,
			'max_lines': args.max,
			'display_type': itype,
			'hz': args.hz,
			'soft': soft,
			'hard': hard,
			'show_zeros': args.show_zeros,
			'description': args.desc,
		}, args.collect_time, cycles_left=[args.max_cycles], debug=args.debug, interactive=args.interactive)
	except KeyboardInterrupt:
		sshc.destroy()

