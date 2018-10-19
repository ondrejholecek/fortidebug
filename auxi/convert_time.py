#!/usr/bin/env python2.7

import datetime
import pytz
import sys
import re
import argparse

unix_epoch_start  = pytz.UTC.localize(datetime.datetime(1970, 1, 1, 0, 0, 0))

class ConvertTime:
	FORMATS = {
		'human-with-offset': {
			'regex': re.compile('^[\[<]?(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})([+-])(\d{2}):(\d{2})[\]>]?(.*)$'),
		},
		'human': {
			'regex': re.compile('^[\[<]?(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})[\]>]?(.*)$'),
		},
		'timestamp': {
			'regex': re.compile('^[\[<]?(\d+)[\]>]?(.*)$'),
		},
		'iso': {
			'regex': re.compile('^[\[<]?(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([+-])(\d{2}):(\d{2})[\]>]?(.*)$'),
		},
	}

	def __init__(self, inp, out, input_format, output_format, params):
		self.inp = inp
		self.out = out
		self.input_format = input_format
		self.output_format = output_format
		self.params = params

	def guess_format(self, line):
		for fmt in self.FORMATS.keys():
			g = self.FORMATS[fmt]['regex'].search(line)
			if g != None: 
				self.input_format = fmt
				return

	def convert(self, line):
		
		g = self.FORMATS[self.input_format]['regex'].search(line)
		if g == None: return None

		original_dt  = None
		rest_of_line = None
		output_dt    = None

		### input
		if self.input_format in ('human-with-offset', 'iso'):
			d = datetime.datetime(int(g.group(1)), int(g.group(2)), int(g.group(3)), int(g.group(4)), int(g.group(5)), int(g.group(6)))
			tzdiff = int(g.group(8))*60 + int(g.group(9))
			if g.group(7) == '-': tzdiff = -tzdiff
			d_utc = pytz.UTC.localize(d - datetime.timedelta(minutes=tzdiff))

			original_dt  = d_utc
			rest_of_line = g.group(10)

		elif self.input_format == 'human':
			d = datetime.datetime(int(g.group(1)), int(g.group(2)), int(g.group(3)), int(g.group(4)), int(g.group(5)), int(g.group(6)))

			original_dt  = self.params['input_timezone'].localize(d)
			rest_of_line = g.group(7)

		elif self.input_format == 'timestamp':
			original_dt = datetime.datetime.fromtimestamp(int(g.group(1)), pytz.UTC)
			rest_of_line = g.group(2)
			

		### output
		if self.output_format == 'timestamp':
			output_dt = str(int((original_dt - unix_epoch_start).total_seconds()))

		elif self.output_format == 'human-with-offset':
			output_dt = str(original_dt.astimezone(self.params['output_timezone']))

		elif self.output_format == 'human':
			output_dt = str(original_dt.astimezone(self.params['output_timezone']).replace(tzinfo=None))

		elif self.output_format == 'iso':
			output_dt = str(original_dt.astimezone(self.params['output_timezone']).isoformat())

		### 
		if len(self.params['borders']) >= 2:
			converted = "%s%s%s%s" % (self.params['borders'][0], output_dt, self.params['borders'][1], rest_of_line,)
		else:
			converted = "%s%s" % (output_dt, rest_of_line,)

		return converted

	def process(self):
		while True:
			line = self.inp.readline()
			if len(line) == 0: break
			while line[-1] in ('\n', '\r'):
				line = line[:-1]

			if self.input_format == None:
				self.guess_format(line)

			if self.input_format == None:
				# unknown format, just write the original line
				print >>sys.stderr, "Input format unknown, printing original line"
				print >>self.out, line

			else:
				converted = self.convert(line)
				if converted == None:
					print >>sys.stderr, "Datetime format '%s' not recognized, printing original line" % (self.input_format,)
					print >>self.out, line
				else:
					print >>self.out, converted



parser = argparse.ArgumentParser(description='Time conversion')
parser.add_argument('--input',  default=None, type=str, help='Input file name (stdin if not specified)')
parser.add_argument('--output', default=None, type=str, help='Output file name (stdout if not specified)')
parser.add_argument('--tz-input', default='UTC', type=str, help='Timezone expected on input (if not specified otherwise), default "UTC"')
parser.add_argument('--tz-output', default='UTC', type=str, help='Timezone expected on output, default "UTC"')
parser.add_argument('--timezones', default=False, action='store_true', help='List common timezones')
parser.add_argument('--format-input', default=None, choices=['human-with-offset', 'human', 'timestamp', 'iso'], help='Input time format, try to guess if not specified')
parser.add_argument('--format-output', default='human-with-offset', choices=['human-with-offset', 'human', 'timestamp', 'iso'], help='Output time format, "human-with-offset" by default')
parser.add_argument('--borders', default='', type=str, help='Two characters that will border the output time')
args = parser.parse_args()

if args.timezones:
	print "Common timezones:"
	for tz in pytz.common_timezones:
		print "- %s" % (tz,)
	sys.exit(0)

# timezones
try:
	input_tz  = pytz.timezone(args.tz_input)
	output_tz = pytz.timezone(args.tz_output)
except pytz.exceptions.UnknownTimeZoneError, e:
	print >>sys.stderr, "Timezone %s is unknown. Use --timezones to list the common timezones." % (str(e),)
	sys.exit(1)

# input & output parameters
if args.input == None:
	input_fd = sys.stdin
else:
	input_fd = open(args.input, "rb")

if args.output == None:
	output_fd = sys.stdout
else:
	output_fd = open(args.output, "wb")


#
ct = ConvertTime(input_fd, output_fd, args.format_input, args.format_output, { 
	'borders'         : args.borders,
	'input_timezone'  : input_tz,
	'output_timezone' : output_tz 
})

try:
	ct.process()
except KeyboardInterrupt:
	pass

input_fd.close()
output_fd.close()
