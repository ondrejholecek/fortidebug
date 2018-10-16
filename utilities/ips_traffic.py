#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.IPSSessionsStat import ParserIPSSessionsStat
from parsers.IPSSummary import ParserIPSSummary
from _common import ssh, cycle, prepend_timestamp

import re
import sys

sshc, args = ssh([
	{ 'name':'--cycle-time',   'type':int, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--repeat-header',  'default':0, 'type':int,  'help':'After how many lines to repeat header' },
	{ 'name':'--empty-line',  'default':False, 'action':'store_true',  'help':'Print empty line after each cycle' },
	{ 'name':'--sessions-in-use',  'default':False, 'action':'store_true',  'help':'Show all sessions in use at each moment' },
	{ 'name':'--recent-pps',  'default':False, 'action':'store_true',  'help':'Show recent packets per second' },
	{ 'name':'--recent-bps',  'default':False, 'action':'store_true',  'help':'Show recent bits per second' },
	{ 'name':'--tcp-sessions-in-use',  'default':False, 'action':'store_true',  'help':'Show TCP sessions in use at each moment' },
	{ 'name':'--udp-sessions-in-use',  'default':False, 'action':'store_true',  'help':'Show UDP sessions in use at each moment' },
	{ 'name':'--icmp-sessions-in-use',  'default':False, 'action':'store_true',  'help':'Show ICMP sessions in use at each moment' },
	{ 'name':'--ip-sessions-in-use',  'default':False, 'action':'store_true',  'help':'Show IP sessions in use at each moment' },
	{ 'name':'--tcp-sessions-active',  'default':False, 'action':'store_true',  'help':'Show TCP sessions active at each moment' },
	{ 'name':'--udp-sessions-active',  'default':False, 'action':'store_true',  'help':'Show UDP sessions active at each moment' },
	{ 'name':'--icmp-sessions-active',  'default':False, 'action':'store_true',  'help':'Show ICMP sessions active at each moment' },
	{ 'name':'--ip-sessions-active',  'default':False, 'action':'store_true',  'help':'Show IP sessions active at each moment' },
	{ 'name':'--tcp-sessions-per-second',  'default':False, 'action':'store_true',  'help':'Show TCP sessions per second' },
	{ 'name':'--udp-sessions-per-second',  'default':False, 'action':'store_true',  'help':'Show UDP sessions per second' },
	{ 'name':'--icmp-sessions-per-second',  'default':False, 'action':'store_true',  'help':'Show ICMP sessions per second' },
	{ 'name':'--ip-sessions-per-second',  'default':False, 'action':'store_true',  'help':'Show IP sessions per second' },
	{ 'name':'--all-sessions-per-second',  'default':False, 'action':'store_true',  'help':'Show all sessions per second' },
	{ 'name':'--all-counters',  'default':False, 'action':'store_true',  'help':'Show all known counters' },
	{ 'name':'--only-total',  'default':False, 'action':'store_true',  'help':'Do not show per IPSE counters' },
], """
This utility continuously parses the output of "diag ips session stat" and displays various IPS session statistics.

It can show (everything per engine + summary):
- TCP/UDP/ICMP/IP sessions currently in use
- TCP/UDP/ICMP/IP sessions currently active
- based on "totals" it can calculate the average number of sessions per second (this was verified with FortiTester)
  (be aware that this is an average, so the totals might not much exactly for small number of sessions)
- recent packets per seconds as reported by the IPS engine - this is counted in both directions together (this was
  also verified with FortiTester)
- recent bits per seconds as reported by the IPS engine (this was verified with FortiTester)

Run it with "-h" parameter to find all possible options - the option names are pretty self-explanatory.

You can enable each counter independently (by default all are disabled!), or you can use "--all-counters" to enable 
all known counters (in that case you may also want to use "--empty-line" parameter to print an empty line after each 
cycle to make the output more human readable).

Note: For some reason (not only but mainly when somebody else is debugging on the save device) the output of the 
command it not always correct/showing all the IPS engines. The program can recognize the problem, because it knows 
how many IPS engines there are running. In that case the error is printed, but if it is only occasional, it is 
not really a problem.
""")

def do(sshc, info):
	etime = ParserCurrentTime(sshc).get()
	
	# calculate the expected number of processing engines
	# (this is to recognize when the sessions output is incomplete, which can happen when somebody else is debugging for example)
	if info['engines'] == None:
		ipssum = ParserIPSSummary(sshc).get()
		engines = 0
		for ipse in ipssum:
			if ipse['cfg'] == False:
				engines += 1
		info['engines'] = engines

	#
	ipss = ParserIPSSessionsStat(sshc).get()
	if (len(ipss.keys()) != info['engines']):
		print >>sys.stderr, "Error in collected outputs - expected %i engines but got %i, isn't somebody else also debugging?" % (info['engines'], len(ipss.keys()),)
		return { "error" : True }


	if info['cycles'] == 0 or (info['repeat_header'] > 0 and (info['cycles'] % info['repeat_header'] == 0)): 
		show_header(ipss, etime, only_total=info['only_total'])

	if info['show']['sessions_in_use']:
		show_numbers(ipss, etime, 'ses_in_use', lambda x: x['sessions']['total']['inuse'], only_total=info['only_total'])
	if info['show']['recent_pps']:
		show_numbers(ipss, etime, 'rec_packps', lambda x: x['pps'], only_total=info['only_total'])
	if info['show']['recent_bps']:
		show_numbers(ipss, etime, 'rec_bitps', lambda x: x['bps'], human=True, only_total=info['only_total'])
	if info['show']['tcp_sessions_in_use']:
		show_numbers(ipss, etime, 'tcp_in_use', lambda x: x['sessions']['tcp']['inuse'], only_total=info['only_total'])
	if info['show']['udp_sessions_in_use']:
		show_numbers(ipss, etime, 'udp_in_use', lambda x: x['sessions']['udp']['inuse'], only_total=info['only_total'])
	if info['show']['icmp_sessions_in_use']:
		show_numbers(ipss, etime, 'icmp_in_use', lambda x: x['sessions']['icmp']['inuse'], only_total=info['only_total'])
	if info['show']['ip_sessions_in_use']:
		show_numbers(ipss, etime, 'ip_in_use', lambda x: x['sessions']['ip']['inuse'], only_total=info['only_total'])
	if info['show']['tcp_sessions_active']:
		show_numbers(ipss, etime, 'tcp_active', lambda x: x['sessions']['tcp']['active'], only_total=info['only_total'])
	if info['show']['udp_sessions_active']:
		show_numbers(ipss, etime, 'udp_active', lambda x: x['sessions']['udp']['active'], only_total=info['only_total'])
	if info['show']['icmp_sessions_active']:
		show_numbers(ipss, etime, 'icmp_active', lambda x: x['sessions']['icmp']['active'], only_total=info['only_total'])
	if info['show']['ip_sessions_active']:
		show_numbers(ipss, etime, 'ip_active', lambda x: x['sessions']['ip']['active'], only_total=info['only_total'])
	if info['show']['tcp_sessions_per_second'] and info['previous'] != None:
		tmp = diff_per_interval(ipss, info['previous'], lambda x: x['sessions']['tcp']['total'])
		show_numbers(tmp, etime, 'tcp_s_p_sec', lambda x: x['result'], only_total=info['only_total'])
	if info['show']['udp_sessions_per_second'] and info['previous'] != None:
		tmp = diff_per_interval(ipss, info['previous'], lambda x: x['sessions']['udp']['total'])
		show_numbers(tmp, etime, 'udp_s_p_sec', lambda x: x['result'], only_total=info['only_total'])
	if info['show']['icmp_sessions_per_second'] and info['previous'] != None:
		tmp = diff_per_interval(ipss, info['previous'], lambda x: x['sessions']['icmp']['total'])
		show_numbers(tmp, etime, 'icmp_s_p_sec', lambda x: x['result'], only_total=info['only_total'])
	if info['show']['ip_sessions_per_second'] and info['previous'] != None:
		tmp = diff_per_interval(ipss, info['previous'], lambda x: x['sessions']['ip']['total'])
		show_numbers(tmp, etime, 'ip_s_p_sec', lambda x: x['result'], only_total=info['only_total'])
	if info['show']['all_sessions_per_second'] and info['previous'] != None:
		tmp = diff_per_interval(ipss, info['previous'], lambda x: x['sessions']['calculated_total']['total'])
		show_numbers(tmp, etime, 'all_s_p_sec', lambda x: x['result'], only_total=info['only_total'])
	
	
	info['cycles']   += 1
	info['previous'] = ipss

	if info['empty_line']: print ""

def show_header(data, etime, only_total=False):
	line = "%-12s" % ("counter",)

	if not only_total:
		for ipse in sorted(data.keys()):
			col = "IPSE#%i" % (ipse,)
			line += " %8s" % (col,)

	line += " %12s" % ("total",)
	print prepend_timestamp(line, etime, "ips_traffic")

def diff_per_interval(cur, prev, value_fce):

	r = {}
	for ipse in sorted(cur.keys()):
		if ipse not in prev: continue

		timediff = cur[ipse]['collected_on'] - prev[ipse]['collected_on']
		r[ipse] = {
			'result': int(round(float(value_fce(cur[ipse]) - value_fce(prev[ipse])) / timediff)),
		}

	return r
		
def show_numbers(data, etime, counter, value_fce, human=False, only_total=False):
	line = "%-12s" % (counter,)
	total = 0

	for ipse in sorted(data.keys()):
		value = value_fce(data[ipse])
		if not only_total:
			if not human:
				line += " %8i" % (value,)
			else:
				line += " %8s" % (get_human(value),)
		total += value

	if not human:
		line += " %12i" % (total,)
	else:
		line += " %12s" % (get_human(total),)

	print prepend_timestamp(line, etime, "ips_traffic")

def get_human(number):
	m = 1000

	if number < m:
		return "%ib" % (number,)
	elif number < (m*m):
		return "%.2fk" % (float(number)/m)
	elif number < (m*m*m):
		return "%.2fm" % (float(number)/m/m)
	elif number < (m*m*m*m):
		return "%.2fg" % (float(number)/m/m/m)
	elif number < (m*m*m*m*m):
		return "%.2ft" % (float(number)/m/m/m/m)
	
	else:
		return "%i?" % (number,)

if __name__ == '__main__':
	info = {
		'cycles': 0,
		'repeat_header': None,
		'empty_line': False,
		'previous' : None,
		'engines'  : None,
		'only_total': False,
		'show' : {
			'sessions_in_use'          : False,
			'recent_pps'               : False,
			'recent_bps'               : False,
			'tcp_sessions_in_use'      : False,
			'udp_sessions_in_use'      : False,
			'icmp_sessions_in_use'     : False,
			'ip_sessions_in_use'       : False,
			'tcp_sessions_active'      : False,
			'udp_sessions_active'      : False,
			'icmp_sessions_active'     : False,
			'ip_sessions_active'       : False,
			'tcp_sessions_per_second'  : False,
			'udp_sessions_per_second'  : False,
			'icmp_sessions_per_second' : False,
			'ip_sessions_per_second'   : False,
			'all_sessions_per_second'  : False,
		},
	}

	info['repeat_header'] = args.repeat_header
	info['empty_line']    = args.empty_line
	info['only_total']    = args.only_total

	if args.sessions_in_use:
		info['show']['sessions_in_use'] = True
	if args.recent_pps:
		info['show']['recent_pps'] = True
	if args.recent_bps:
		info['show']['recent_bps'] = True
	if args.tcp_sessions_in_use:
		info['show']['tcp_sessions_in_use'] = True
	if args.udp_sessions_in_use:
		info['show']['udp_sessions_in_use'] = True
	if args.icmp_sessions_in_use:
		info['show']['icmp_sessions_in_use'] = True
	if args.ip_sessions_in_use:
		info['show']['ip_sessions_in_use'] = True
	if args.tcp_sessions_active:
		info['show']['tcp_sessions_active'] = True
	if args.udp_sessions_active:
		info['show']['udp_sessions_active'] = True
	if args.icmp_sessions_active:
		info['show']['icmp_sessions_active'] = True
	if args.ip_sessions_active:
		info['show']['ip_sessions_active'] = True
	if args.tcp_sessions_per_second:
		info['show']['tcp_sessions_per_second'] = True
	if args.udp_sessions_per_second:
		info['show']['udp_sessions_per_second'] = True
	if args.icmp_sessions_per_second:
		info['show']['icmp_sessions_per_second'] = True
	if args.ip_sessions_per_second:
		info['show']['ip_sessions_per_second'] = True
	if args.all_sessions_per_second:
		info['show']['all_sessions_per_second'] = True

	if args.all_counters:
		for k in info['show'].keys():
			info['show'][k] = True

	try:
		cycle(do, {
			'sshc': sshc, 
			'info': info,
		}, args.cycle_time, cycles_left=[args.max_cycles], debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

