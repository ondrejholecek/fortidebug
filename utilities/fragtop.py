#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.Fragmentation import ParserFragmentation
from parsers.ProcessCPU import ParserProcessCPU
from _common import ssh, cycle, simple_command_with_timestamp, prepend_timestamp

import re
import sys
import time

sshc, args = ssh([
	{ 'name':'--collect-time',   'type':int, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--history',   'type':int, 'default':45,  'help':'Maximum lines to show (45 by default)' },
	{ 'name':'--hz',    'type':int, 'default':100,  'help':'CONFIG_HZ of device, do not change' },
	{ 'name':'--raw',   'default':False, 'action':'store_true',  'help':'Show raw difference (not divided by interval)' },
	{ 'name':'--no-cpu',   'default':False, 'action':'store_true',  'help':'Do not show CPU usage on each line' },
], """
""")

def do(sshc, cache, history, hz, raw, show_cpu):
	etime = ParserCurrentTime(sshc).get()
	frags = ParserFragmentation(sshc).get()
	usage = ParserProcessCPU(sshc).get([])
	
	if 'last' not in cache:
		cache['last'] = {
			'frags': frags,
			'cpu' : usage,
		}
		return

	time_difference = frags['collected_on'] - cache['last']['frags']['collected_on']

	overall_cpus = {}
	for tmp in ['user', 'system', 'idle', 'iowait', 'irq', 'softirq']:
		overall_cpus[tmp] = int(round(((usage['global'][tmp] - cache['last']['cpu']['global'][tmp])*100)/(time_difference*hz)))

	pdiff = {}
	for p in frags['frags']:
		if p not in frags['frags']:
			print >>sys.stderr, 'Error: fragmentation key %s missing in current statistics' % (p,)
			return
		elif p not in cache['last']['frags']['frags']:
			print >>sys.stderr, 'Error: fragmentation key %s missing in previous statistics' % (p,)
			return

		if raw:
			pdiff[p] = frags['frags'][p] - cache['last']['frags']['frags'][p]
		else:
			pdiff[p] = int(round((((frags['frags'][p] - cache['last']['frags']['frags'][p]))/(time_difference))))

	if os.name == 'nt':
		os.system('cls')
		print "Packet fragmentation    (written by Ondrej Holecek <oholecek@fortinet.com>)"
	else:
		print "\x1b[2J\x1b[H\033[1mPacket fragmentation   (written by Ondrej Holecek <oholecek@fortinet.com>)\033[0m"

	
	filters_applied = "Applied filters: "
	if raw: filters_applied += "CNTS[raw] "
	else: filters_applied += "CNTS[diff] "
	filters_applied += "HIST[%i] " % (history,)

	print prepend_timestamp("Overall CPU utilization: %3.1f %% user, %3.1f %% system, %3.1f %% idle" % (
		overall_cpus['user'], overall_cpus['system'], overall_cpus['idle'],
	), etime, 'fragtop')
	print prepend_timestamp("Overall CPU utilization: %3.1f %% iowait, %3.1f %% irq, %3.1f %% softirq" % (
		overall_cpus['iowait'], overall_cpus['irq'], overall_cpus['softirq'],
	), etime, 'fragtop')
	print prepend_timestamp(filters_applied, etime, 'fragtop')

	prehdr = "         |     Received fragments reassembly counters    |  Outgoing fragmentation counters  |"
	if show_cpu: prehdr += "   Historical CPU percentage    |"
	print prepend_timestamp(prehdr, etime, 'fragtop')
	hdr = " %7s | %9s | %9s | %9s | %9s | %9s | %9s | %9s |" % ("history", "fragments", "packets", "timeout", "error", "packets", "fragments", "unable",)
	if show_cpu: hdr += " %8s | %8s | %8s |" % ("system%", "irq%", "softirq%",)
	print prepend_timestamp(hdr, etime, 'fragtop')

	# current line
	current_line = " %7i " % ( int(round(time.time()-frags['collected_on'])),)
	for k in ('ReasmReqds', 'ReasmOKs', 'ReasmTimeout', 'ReasmFails', 'FragOKs', 'FragCreates', 'FragFails'):
		current_line += "| %9i " % (pdiff[k],)
	current_line += "|"
	if show_cpu: current_line += " %8i | %8i | %8i |" % (overall_cpus['system'], overall_cpus['irq'], overall_cpus['softirq'],)
	print prepend_timestamp(current_line, etime, 'fragtop')

	# older lines
	for odata in cache['history']:
		old_line = " %7i " % ( -int(round(time.time()-odata[0])),)
		for k in ('ReasmReqds', 'ReasmOKs', 'ReasmTimeout', 'ReasmFails', 'FragOKs', 'FragCreates', 'FragFails'):
			old_line += "| %9i " % (odata[1][k],)
		old_line += "|"
		if show_cpu: old_line += " %8i | %8i | %8i |" % (odata[2], odata[3], odata[4],)
		print prepend_timestamp(old_line, etime, 'fragtop')
		
	cache['history'].insert(0, (frags['collected_on'], pdiff, overall_cpus['system'], overall_cpus['irq'], overall_cpus['softirq'],) )
	if len(cache['history']) > history: cache['history'] = cache['history'][:history]
	cache['last']['frags'] = frags
	cache['last']['cpu'] = usage
	sys.stdout.flush()

if __name__ == '__main__':
	cache = {'history':[]}
	try:
		cycle(do, {
			'sshc': sshc, 
			'cache': cache,
			'history': args.history,
			'hz': args.hz,
			'raw': args.raw,
			'show_cpu': not args.no_cpu,
		}, args.collect_time, cycles_left=[args.max_cycles], debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

