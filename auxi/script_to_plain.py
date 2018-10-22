#!/usr/bin/env python2.7

import bz2
import datetime
import json
import sys
import argparse
import pytz

class Script2Plain:
	def __init__(self, inp, out, out_tz, inp_compressed):
		self.inp = inp
		self.out = out
		self.out_tz = out_tz
		self.inp_compressed = inp_compressed

		if self.inp != None:
			self.input = open(self.inp, "rb")
		else:
			self.input = sys.stdin

		if self.out != None:
			self.output = open(self.out, "wb")
		else:
			self.output = sys.stdout

		if self.inp_compressed:
			self.readline = self.readline_bz2
		else:
			self.readline = self.readline_plain

		self.decom = None
		self.decom_rest = ""
		self.decom_buf  = ""

		self.params = {
			'hostname': None,
			'sn': None,
			'prompt_character': None,
		}

		self.last_cycle = None

		self.first_output_at = None
		self.last_output_at  = None
		self.commands = 0
	
	def readline_bz2(self):
		last = False

		while True:
			# if we have some lines in the buffer, process it with priority
			nl = self.decom_buf.find("\n")
			if nl != -1:
				line = self.decom_buf[:nl]
				self.decom_buf = self.decom_buf[nl+1:]
				return line

			# otherwise decompress more
			chunk = self.input.read(1024)
			if len(chunk) == 0 and len(self.decom_rest) == 0:
				last = True

			else:
				if self.decom == None:
					self.decom = bz2.BZ2Decompressor()
					if len(self.decom_rest) > 0:
						tmp = self.decom.decompress(self.decom_rest)
						if len(tmp) > 0: self.decom_buf += tmp
						self.decom_rest = ""
		
				try:
					tmp = ""
					tmp = self.decom.decompress(chunk)
				except EOFError:
					self.decom_rest = self.decom.unused_data + chunk
					self.decom = None
		
				if len(tmp) > 0: self.decom_buf += tmp

			if last: 
				if len(self.decom_rest) > 0:
					continue
				else:
					break

		if last:
			return None
		
	def readline_plain(self):
		line = self.input.readline()
		if len(line) == 0: return None

		while line[-1] in ('\r', '\n'):
			line = line[:-1]

		return line

	def next(self):
		chunk = self.readline()
		if chunk == None: 
			return False

		obj   = json.loads(chunk)
	
		r_type      = obj['info']['type']

		if r_type == 'automatic':
			self.params['sn'] = obj['output']['info']['serial']
			self.params['hostname'] = obj['output']['info']['hostname']
			self.params['prompt_character'] = obj['output']['info']['prompt_character']
			self.params['mgmt_vdom'] = obj['output']['info']['mgmt_vdom']
			self.params['time_offset'] = obj['output']['flags']['time_offset']
	
		elif r_type in ('simple', 'continuous'):
			sr_command   = obj['command']
			sr_context   = obj['context']
			sr_timestamp = obj['timestamp']
			sr_output    = obj['output']
			sr_cycle     = obj['cycle']
	
			# time
			dt = pytz.UTC.localize(datetime.datetime.utcfromtimestamp(sr_timestamp))
			dt = dt.astimezone(self.out_tz)
			current_date = dt.strftime("%Y-%m-%d")
			current_time = dt.strftime("%H:%M:%S")
			current_last_sync = dt.strftime("%a %b %m %H:%M:%S %Y")

			# save first and last output time for statistics
			if self.first_output_at == None: self.first_output_at = dt
			self.last_output_at = dt

			# context
			if sr_context == None:
				ctx = 'global'
			elif sr_context == '':
				ctx = self.params['mgmt_vdom']
			else:
				ctx = sr_context

			# new cycle - time and date
			if self.last_cycle != sr_cycle:
				print >>self.output, "%s (%s) %s exe date\r" % (self.params['hostname'], ctx, self.params['prompt_character'],)
				print >>self.output, "current date is: %s\r\n\r" % (current_date,)
	
				print >>self.output, "%s (%s) %s exe time\r" % (self.params['hostname'], ctx, self.params['prompt_character'],)
				print >>self.output, "current time is: %s\r" % (current_time,)
				print >>self.output, "last ntp sync:%s\r\n\r" % (current_last_sync,)
	
				self.last_cycle = sr_cycle

			if r_type == 'simple' or (r_type == 'continuous' and obj['info']['continuous_index'] == 0):
				print >>self.output, "%s (%s) %s %s\r" % (self.params['hostname'], ctx, self.params['prompt_character'], sr_command,)
				self.commands += 1 # stats

			print >>self.output, sr_output

		return True


parser = argparse.ArgumentParser(description='Script output conversion')
parser.add_argument('--input',  default=None, type=str, help='Input file name (stdin if not specified)')
parser.add_argument('--output', default=None, type=str, help='Output file name (stdout if not specified)')
parser.add_argument('--tz-output', default='UTC', type=str, help='Timezone expected on output, default "UTC"')
parser.add_argument('--timezones', default=False, action='store_true', help='List common timezones')
parser.add_argument('--no-compressed', default=False, action='store_true', help='Use if input is already uncompressed')
args = parser.parse_args()

# list timezones
if args.timezones:
	print "Common timezones:"
	for tz in pytz.common_timezones:
		print "- %s" % (tz,)
	sys.exit(0)

# output timezone
try:
	output_tz = pytz.timezone(args.tz_output)
except pytz.exceptions.UnknownTimeZoneError, e:
	print >>sys.stderr, "Timezone %s is unknown. Use --timezones to list the common timezones." % (str(e),)
	sys.exit(1)


s = Script2Plain(args.input, args.output, output_tz, not args.no_compressed)
try:
	while s.next(): pass
except KeyboardInterrupt:
	pass

try:
	line = ""
	line += "Statistics:\n"
	line += "    Remote hostname         : %s\n" % (s.params['hostname'],)
	line += "    Remote serial number    : %s\n" % (s.params['sn'],)
	line += "    Number of cycles        : %i\n" % (s.last_cycle,)
	line += "    Number of commands      : %i\n" % (s.commands,)
	line += "    First command output at : %s\n" % (s.first_output_at,)
	line += "    Last command output at  : %s\n" % (s.last_output_at,)
	sys.stderr.write(line)
except (IndexError, ValueError, TypeError):
	pass
