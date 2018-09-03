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
	{ 'name':'--max-age',  'type':int, 'default':None, 'help':'Show only VPNs not older that this in seconds' },
])

def do(sshc, known_sessions, status, direction, max_age):
	etime = ParserCurrentTime(sshc).get()
	
	matched_sessions = {}

	latest_sessions = ParserIPSecGW(sshc).get()
	for gw in latest_sessions:
		if gw['cookie_local'] == None or gw['cookie_remote'] == None: continue
		if status != None and gw['status'] not in status: 
			#print "ignored [status] for '%s'" % (gw['name'],)
			continue
		if direction != None and gw['direction'] not in direction: 
			#print "ignored [direction] for '%s'" % (gw['name'],)
			continue

		cookie = "%s/%s" % (gw['cookie_local'], gw['cookie_remote'],)
		src = "%s:%i" % (gw['source_ip'], gw['source_port'],)
		dst = "%s:%i" % (gw['destination_ip'], gw['destination_port'],)
		session = "%-16s %-20s %-34s %-22s -> %-22s %14s %14s" % (gw['vdom'], gw['name'], cookie, src, dst, gw['direction'], gw['status'],)

		if session not in known_sessions:
			if max_age == None or gw['created_ago'] <= max_age: 
				print prepend_timestamp("{new}     " + session + " %10i" % (gw['created_ago'],), etime, 'ikegw')

			known_sessions[session] = {'created_ago': gw['created_ago'], 'name': gw['name']}
		
		matched_sessions[session] = True

	# manage removed sessions
	for known in known_sessions.keys():
		if known not in matched_sessions:
			if max_age == None or gw['created_ago'] <= max_age: 
				print prepend_timestamp("{deleted} " + known + " %10i" % (known_sessions[known]['created_ago'],), etime, 'ikegw')

			del known_sessions[known]
	

if __name__ == '__main__':
	try:
		known_sessions = {}

		cycle(do, {
			'sshc': sshc, 
			'known_sessions': known_sessions,
			'status': args.status,
			'direction': args.direction,
			'max_age': args.max_age,
		}, args.cycle_time, debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

