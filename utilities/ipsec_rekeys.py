#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.IPSecGW import ParserIPSecGW
from _common import ssh, cycle, prepend_timestamp
from _common import rss

sshc, args = ssh([
	{ 'name':'--cycle-time', 'type':int, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--direction',  'type':str, 'default':None, 'action':'append', 'choices':['initiator','responder'], 'help':'Which direction to show (can repeat)' },
	{ 'name':'--status',  'type':str, 'default':None, 'action':'append', 'choices':['established','connecting'], 'help':'Which status to show (can repeat)' },
	{ 'name':'--phase',  'type':str, 'default':None, 'action':'append', 'choices':['1','2'], 'help':'Which IPSec phase to show counters for (can repeat)' },
	{ 'name':'--age',  'type':str, 'default':None, 'action':'append', 'choices':['current','total'], 'help':'Show current or total numbers (can repeat)' },
	{ 'name':'--use',  'type':str, 'default':None, 'action':'append', 'choices':['created','established'], 'help':'Show numbers of created or established SAs (can repeat)' },
	{ 'name':'--no-colors',  'default':False, 'action':'store_true', 'help':'Do not print color codes' },
	{ 'name':'--repeat-header', 'type':int, 'default':20,  'help':'How often to repeat header line (20 lines by default), 0 to disable' },
])

all_counters = ('IKE_SA_created_current', 'IKE_SA_established_current', 'IKE_SA_created_all', 'IKE_SA_established_all', 'IPSEC_SA_created_current', 'IPSEC_SA_established_current', 'IPSEC_SA_created_all', 'IPSEC_SA_established_all')

def do(sshc, known, status, direction, phase, age, use, colors, repeat_header):
	if os.name == 'nt': colors = False

	etime = ParserCurrentTime(sshc).get()
	latest = ParserIPSecGW(sshc).get()

	# select only the counters user is interested in
	counter_names = []
	for cntr in all_counters:
		accept = True
		
		if phase != None:
			if cntr.startswith("IKE_") and '1' not in phase: accept = False
			if cntr.startswith("IPSEC_") and '2' not in phase: accept = False

		if age != None:
			if cntr.endswith("_current") and 'current' not in age: accept = False
			if cntr.endswith("_all") and 'total' not in age: accept = False

		if use != None:
			if "_created_" in cntr and 'created' not in use: accept = False
			if "_established_" in cntr and 'established' not in use: accept = False

		if accept:
			counter_names.append(cntr)
		
	#counter_names= ('IKE_SA_created_current', 'IKE_SA_established_current', 'IKE_SA_created_all', 'IKE_SA_established_all', 'IPSEC_SA_created_current', 'IPSEC_SA_established_current', 'IPSEC_SA_created_all', 'IPSEC_SA_established_all')
	#counter_names= ('IKE_SA_created_current', 'IKE_SA_created_all', 'IKE_SA_established_current', 'IKE_SA_established_all', 'IPSEC_SA_created_current', 'IPSEC_SA_created_all', 'IPSEC_SA_established_current', 'IPSEC_SA_established_all')
	#counter_names= ('IKE_SA_created_all', 'IKE_SA_established_all', 'IPSEC_SA_created_all', 'IPSEC_SA_established_all')

	to_print = []

	for gw in latest:
		# do we want this one?
		if status != None and gw['status'] not in status: continue
		if direction != None and gw['direction'] not in direction: continue

		# retrieve current counters
		this = {}
		for t in counter_names:
			this[t] = gw[t]

		# retrieve previous counters
		try:
			prev = known[(gw['vdom'], gw['name'])]
		except KeyError:
			prev = {}
			for t in counter_names:
				prev[t] = 0

		# count difference
		diff = {}
		non_zero = []
		for t in counter_names:
			diff[t] = this[t] - prev[t]
			if diff[t] != 0: non_zero.append(t)

		# prepare lines to print
		if len(non_zero) > 0:
			line = "%-16s %-20s %-10s %-12s" % (gw['vdom'], gw['name'], gw['direction'], gw['status'])

			for t in counter_names:
				if colors:
					if diff[t] == 0: line += '\33[2m'
					elif diff[t] > 0: line += '\33[0;32;40m'
					elif diff[t] < 0: line += '\33[0;31;40m'

				if diff[t] == 0: 
					line += " %10i" % (0,)
				else:
					line += " %+10i" % (diff[t],)

				if colors: line += '\33[0m'

			# save number of appearences of this p1
			if (gw['vdom'], gw['name']) not in known['appeared']: 
				known['appeared'][(gw['vdom'], gw['name'])] = 0
			known['appeared'][(gw['vdom'], gw['name'])] += 1

			# add number of appearances to the output line
			if known['iters'] > 0:
				repeat_perc = int(round(float(known['appeared'][(gw['vdom'], gw['name'])] * 100) / float(known['iters'])))
			else:
				repeat_perc = 100

			if colors:
				if repeat_perc > 50: line += '\33[0;31;40m'
				elif repeat_perc > 20: line += '\33[0;33;40m'

			line += " %7i" % (repeat_perc,)

			if colors: line += '\33[0m'

			# save line to be printed later
			to_print.append(prepend_timestamp(line, etime, 'ipsec_rekeys'))

		# save ...
		known[(gw['vdom'], gw['name'])] = this

	# prepare header
	if known['header'] == None:
		header = ''
		if colors: header += '\033[1m'

		header += "%-16s %-20s %-10s %-12s" % ('vdom', 'name', 'direction', 'status',)
		for t in counter_names:
			if   t == 'IKE_SA_created_all'          : header += " %10s" % ('P1:CreAll',)
			elif t == 'IKE_SA_established_all'      : header += " %10s" % ('P1:EstAll',)
			elif t == 'IKE_SA_created_current'      : header += " %10s" % ('P1:CreCur',)
			elif t == 'IKE_SA_established_current'  : header += " %10s" % ('P1:EstCur',)
			elif t == 'IPSEC_SA_created_all'        : header += " %10s" % ('P2:CreAll',)
			elif t == 'IPSEC_SA_established_all'    : header += " %10s" % ('P2:EstAll',)
			elif t == 'IPSEC_SA_created_current'    : header += " %10s" % ('P2:CreCur',)
			elif t == 'IPSEC_SA_established_current': header += " %10s" % ('P2:EstCur',)

		header += " %7s" % ('repeat%',)
		if colors: header += '\033[0m'
		known['header'] = header

	# do not show the first round but show header
	known['iters'] += 1
	if known['iters'] == 1:
		known['appeared'] = {}
		print prepend_timestamp(known['header'], etime, 'ipsec_rekeys')
		return


	# print data 
	for p in to_print:
		if repeat_header != 0 and known['printed'] != 0 and known['printed'] % repeat_header == 0:
			print prepend_timestamp(known['header'], etime, 'ipsec_rekeys')

		print p
		known['printed'] += 1

	
if __name__ == '__main__':
	try:
		known = { 
			'iters': 0,
			'printed': 0,
			'header': None,
			'appeared': {},
		}

		cycle(do, {
			'sshc': sshc, 
			'known': known,
			'status': args.status,
			'direction': args.direction,
			'phase': args.phase,
			'age': args.age,
			'use': args.use,
			'colors': not args.no_colors,
			'repeat_header': args.repeat_header,
		}, args.cycle_time, cycles_left=[args.max_cycles], debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

