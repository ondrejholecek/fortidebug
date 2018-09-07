#!/usr/bin/env python2.7

import sys
import datetime
import re
import pytz
import argparse

def do(params):
	re_datetime       = re.compile("^\[(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)\]\s+(.*)$")
	re_split          = re.compile(params['split'])
	unix_epoch_start  = pytz.UTC.localize(datetime.datetime(1970, 1, 1, 0, 0, 0))

	in_progress = { 'block': None, 'count': 0, 'data': None }
	groups = {}
	
	while True:
		line = params['input'].readline()
		if len(line) == 0: break
		line = line.strip("\n")

		if params['debug']: print "Debug: read line '%s'" % (line,)
	
		g = re_datetime.search(line)
		if not g:
			print >>sys.stderr, "Not matching timestamp on line '%s'" % (line,)
			continue
	
		dt = params['timezone'].localize(datetime.datetime(
			int(g.group(1)), int(g.group(2)), int(g.group(3)),
			int(g.group(4)), int(g.group(5)), int(g.group(6))
		))
		uts = int((dt - unix_epoch_start).total_seconds())
	
		datapart = g.group(7)
		data = re_split.split(datapart)
		if params['debug']: print "Debug: data split into %i fields: %s" % (len(data), data,)
	
		## retrieve fields
		ocols = []
		for c in params['columns']:
			try:
				field = data[c['index']]
			except IndexError:
				print >>sys.stderr, "Field index %i out of range (max index %i)" % (c['index'], len(data)-1,)
				ocols = None
				break
	
			try:
				if c['type'] != None: field = c['type'](field)
			except ValueError:
				print >>sys.stderr, "Cannot convert '%s' to %s in line '%s'" % (field, c['type'], line,)
				ocols = None
				break
	
			ocols.append(field)
	
		if ocols == None: 
			continue
	
		##
		current_block = (uts / params['interval']) * params['interval']
		if current_block != in_progress['block']:
			if in_progress['block'] != None and params['operation'] == 'summarize':
				print_it(in_progress['block']+params['interval'], " ".join(str(s) for s in in_progress['data']), params)
	
			elif in_progress['block'] != None and params['operation'] == 'average':
				print_it(in_progress['block']+params['interval'], " ".join(str(int(round(float(s)/in_progress['count']))) for s in in_progress['data']), params)
	
			in_progress = { 'block': current_block, 'count': 1, 'data': ocols}
		
		else:
			for i in range(len(ocols)):
				in_progress['data'][i] += ocols[i]
			in_progress['count'] += 1
		
	
#		print uts, current_block, group_name, ocols
#		print uts, data

def print_it(ts, data, params):
	if params['timeformat'] == "unixts":
		print "%i %s" % (ts, data,)
	elif params['timeformat'] == "human":
		print "%s %s" % (pytz.UTC.localize(datetime.datetime.utcfromtimestamp(ts)).astimezone(params['timezone']).strftime("%Y-%m-%d %H:%M:%S"), data,)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Debug output simplifier')
	parser.add_argument('--file', default=None, help='Filename to read from instead of stdin')
	parser.add_argument('--timezone', default='Europe/Prague', help='Timezone to use (default "Europe/Prague")')
	parser.add_argument('--col', type=int, default=[], action='append', help='Column to use, 0 is the first one after timestamp (can repeat)')
	parser.add_argument('--interval', type=int, required=True, help='Amount of seconds to summarize')
	parser.add_argument('--operation', required=True, choices=['summarize', 'average'], help='What operation to use on columns')
	parser.add_argument('--timeformat', default='human', choices=['unixts', 'human'], help='How to display time and date')
	parser.add_argument('--split-by', default='[\s,:]+', help='Regular expression for splitting the line in columns')
	parser.add_argument('--debug', default=False, action='store_true', help='Enable debugging outputs')
	args = parser.parse_args()

	params = {
		'timezone': pytz.timezone(args.timezone),
		'columns' : [],
		'interval': args.interval,
		'operation': args.operation,
		'timeformat': args.timeformat,
		'split': args.split_by,
		'debug': args.debug,
	}

	for c in args.col:
		params['columns'].append({'index':c, 'type':int})
	
	if args.file == None:
		params['input'] = sys.stdin
	else:
		params['input'] = open(args.file, "r")

	do(params)







