#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from _common import ssh, prepend_timestamp

import re
import datetime
import sys

sshc, args = ssh([
	{ 'name':'--cycle-time',   'type':int, 'default':1,  'help':'How long should each cycle take' },
], """
Just run the mpstat continuously with timestamp added at the beginning of each line.
""")

re_split = re.compile('^(.*?)(TIME.*?\r\n\r\n)(.*)$', re.DOTALL)
re_time  = re.compile('^(\d+):(\d+):(\d+)\s+(\S+)\s+all\s+', re.M)

def divide(data, info):
	g = re_split.search(data)
	if not g: return None

	return ([g.group(2)], g.group(3))

def result(data, info):
	g = re_time.search(data)
	if not g:
		print "Debug: invalid output format"
		return

	hour   = int(g.group(1))
	minute = int(g.group(2))
	second = int(g.group(3))
	ampm   = g.group(4)

	if hour == 12 and ampm == "AM":
		hour = 0
	elif hour == 12 and ampm == "PM":
		hour = 12
	elif ampm == "PM":
		hour += 12

	current = info['last_time'].replace(hour=hour, minute=minute, second=second)
	if current < info['last_time']: # next day
		current += datetime.timedelta(days=1)

	print prepend_timestamp(data, current, "mpstat")
	sys.stdout.flush()

	info['last_time'] = current

def finished(info):
	return None

def do(sshc, cycle_time):
	info = { 'info': { 'last_time': ParserCurrentTime(sshc).get() } }
	sshc.continuous_exec("diag sys mpstat %i" % (cycle_time,), divide, result, finished, info)

if __name__ == '__main__':
	try:
		do(sshc, args.cycle_time)
	except KeyboardInterrupt:
		sshc.destroy()

