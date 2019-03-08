#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.PacketDistribution import ParserPacketDistribution
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
	{ 'name':'--percentage',   'default':False, 'action':'store_true',  'help':'Show percentage for each type instead of real number' },
], """
""")

def do(sshc, cache, history, hz, raw, percentage):
	etime = ParserCurrentTime(sshc).get()
	packets = ParserPacketDistribution(sshc).get()
	usage = ParserProcessCPU(sshc).get([])
	
	if 'last' not in cache:
		cache['last'] = {
			'packets': packets,
			'cpu' : usage,
		}
		return

	time_difference = packets['collected_on'] - cache['last']['packets']['collected_on']

	overall_cpus = {}
	for tmp in ['user', 'system', 'idle', 'iowait', 'irq', 'softirq']:
		overall_cpus[tmp] = int(round(((usage['global'][tmp] - cache['last']['cpu']['global'][tmp])*100)/(time_difference*hz)))

	pdiff = {}
	for p in packets['packets']:
		if p not in packets['packets']:
			print >>sys.stderr, 'Error: packet distribution key %s missing in current statistics' % (p,)
			return
		elif p not in cache['last']['packets']['packets']:
			print >>sys.stderr, 'Error: packet distribution key %s missing in previous statistics' % (p,)
			return

		if raw:
			pdiff[p] = packets['packets'][p] - cache['last']['packets']['packets'][p]
		else:
			pdiff[p] = int(round((((packets['packets'][p] - cache['last']['packets']['packets'][p]))/(time_difference))))

	total = sum(pdiff[x] for x in pdiff.keys())
	if percentage:
		for p in pdiff.keys():
			pdiff[p] = int(round((float(pdiff[p])*100)/total))


	if os.name == 'nt':
		os.system('cls')
		print "Packet size distribution   (written by Ondrej Holecek <oholecek@fortinet.com>)"
	else:
		print "\x1b[2J\x1b[H\033[1mPacket size distribution   (written by Ondrej Holecek <oholecek@fortinet.com>)\033[0m"

	
	filters_applied = "Applied filters: "
	if raw: filters_applied += "CNTS[raw] "
	else: filters_applied += "CNTS[diff] "
	if percentage: filters_applied += "PERC[yes] "
	else: filters_applied += "PERC[no] "
	filters_applied += "HIST[%i] " % (history,)

	print prepend_timestamp("Overall CPU utilization: %3.1f %% user, %3.1f %% system, %3.1f %% idle" % (
		overall_cpus['user'], overall_cpus['system'], overall_cpus['idle'],
	), etime, 'pkttop')
	print prepend_timestamp("Overall CPU utilization: %3.1f %% iowait, %3.1f %% irq, %3.1f %% softirq" % (
		overall_cpus['iowait'], overall_cpus['irq'], overall_cpus['softirq'],
	), etime, 'pkttop')
	print prepend_timestamp(filters_applied, etime, 'pkttop')

	# header
	skeys = sorted(pdiff.keys())
	hdr = " history "
	for k in skeys:
		left = k[0]
		right = k[1]
		c = ""
		if left == None:
			c = " <= %i" % (right,)
		elif right == None:
			c = " >= %i" % (left,)
		else:
			c = "<%i, %i>" % (left, right,)
			
		hdr += "| %12s " % (c,)
	hdr += "| %12s |" % ('total pkts',)
	print prepend_timestamp(hdr, etime, 'pkttop')

	# current line
	current_line = " %7i " % ( int(round(time.time()-packets['collected_on'])),)
	for k in skeys:
		current_line += "| %12i " % (pdiff[k],)
	current_line += "| %12i |" % ( total, )
	print prepend_timestamp(current_line, etime, 'pkttop')

	# older lines
	for odata in cache['history']:
		old_line = " %7i " % ( -int(round(time.time()-odata[0])),)
		for k in skeys:
			old_line += "| %12i " % (odata[1][k],)
		old_line += "| %12i |" % (odata[2],)
		print prepend_timestamp(old_line, etime, 'pkttop')
		

	cache['history'].insert(0, (packets['collected_on'], pdiff, total) )
	if len(cache['history']) > history: cache['history'] = cache['history'][:history]
	cache['last']['packets'] = packets
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
			'percentage': args.percentage,
		}, args.collect_time, cycles_left=[args.max_cycles], debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

