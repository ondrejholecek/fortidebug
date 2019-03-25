import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.SSHCommands import SSHCommands
from lib.ScriptCommands import ScriptCommands

import argparse
import sys
import time
import getpass
import re
import datetime
import signal

def ssh(args=(), manual='', supports_script=False):
	parser = argparse.ArgumentParser(description='FortiDebug')

	# add common global arguments
	parser.add_argument('--time-format', default='human-with-offset', choices=['human-with-offset', 'human', 'timestamp', 'iso'], help='Format of the date and time')
	parser.add_argument('--time-source', default='device', choices=['device', 'local'], help='How to retrieve data and time')
	parser.add_argument('--debug', default=False, action="store_true", help='Enable debug outputs')
	parser.add_argument('--manual', default=False, action="store_true", help='Show manual')
	parser.add_argument('--max-cycles', default=None, type=int, help='Maximum cycles to run')

	# arguments used when real SSH connection is to be established
	sshcon = parser.add_argument_group('SSH connection parameters')
	sshcon.add_argument('--host', default=None, help='FortiGate hostname or IP address')
	sshcon.add_argument('--user', default="admin", help='User name to log in as, default "admin"')
	sshcon.add_argument('--password', default="", help='Password to log in with, default empty')
	sshcon.add_argument('--askpass', default=False, action="store_true", help='Ask for password on standard input')
	sshcon.add_argument('--credfile', default=None, help='File to read the credentials from - 1st line username, 2nd line password')
	sshcon.add_argument('--port', default=22, type=int, help='SSH port, default 22')
	sshcon.add_argument('--ignore-ssh-key', default=False, action="store_true", help='Ignore SSH server key problems')
	sshcon.add_argument('--hostname-extension', default=None, type=str, help='Extend the hostname for purposes of matching command prompt (chassis)')
	sshcon.add_argument('--prompt-character', default=None, type=str, help='Override the prompt character ("#" or "$") (chassis)')

	# arguments used when source is file from script.py utility
	srcfile = parser.add_argument_group('ScriptFile source parameters')
	srcfile.add_argument('--src-file', default=None, help='Script out to read from instead of directly connecting via SSH')
	srcfile.add_argument('--interactive', default=False, action='store_true', help='Break after each cycle')
	
	# add local arguments
	local = parser.add_argument_group('local parameters')
	for arg in args:
		name = arg['name']
		del arg['name']
		local.add_argument(name, **arg)

	args = parser.parse_args()

	if args.manual:
		print manual
		sys.exit(0)

	if ((args.src_file != None) and (args.host != None)) \
	 or ((args.src_file == None) and (args.host == None)):
		print >>sys.stderr, "One of \"--src-file\" or \"--host\" must be specified"
		sys.exit(1)

	if (args.src_file != None) and not supports_script:
		print >>sys.stderr, 'This utility does not support reading the input from script file'
		sys.exit(1)
		
	if args.host != None:	
		if args.credfile != None:
			with open(args.credfile, "r") as f:
				args.user     = f.readline().strip("\n")
				args.password = f.readline().strip("\n")
		
		elif args.askpass:
			args.password = getpass.getpass("Password for %s@%s: " % (args.user, args.host,))
		
		sshc = SSHCommands(args.host, args.user, args.password, args.port, args.ignore_ssh_key, hostname_extension=args.hostname_extension, prompt_character=args.prompt_character)
	
		# do not return global arguments values 
		# (they are still saved in SSHCommands object though)
		# exception is the "debug" parameter which we do not delete
		del args.host
		del args.user
		del args.password
		del args.credfile
		del args.port
		del args.ignore_ssh_key
	
		sshc.set_local_param('args', args)
		return (sshc, args)

	elif args.src_file != None:
		scriptc = ScriptCommands(args.src_file)
		scriptc.set_local_param('args', args)
		return (scriptc, args)



def cycle(callback, args, min_interval, cycles_left=None, debug=True, interactive=False):
	if interactive:
		cycle_file(callback, args, debug=debug)
	
	else:
		cycle_ssh(callback, args, min_interval, cycles_left=cycles_left, debug=debug)

def cycle_ssh(callback, args, min_interval, cycles_left=None, debug=True):
	while True:
		cycle_start = time.time()

		callback(**args)

		# timing
		cycle_end   = time.time()
		cycle_sleep = min_interval - (cycle_end-cycle_start)
		if cycle_sleep < 0: cycle_sleep = 0
	
		if debug: print "Debug: Last cycle took %0.1f seconds, sleeping for %0.1f seconds" % (cycle_end-cycle_start, cycle_sleep,)
		sys.stdout.flush()

		if cycles_left != None and cycles_left[0] != None:
			cycles_left[0] -= 1
			if cycles_left[0] == 0: 
				if debug: print "Debug: Maximum number of cycles reached, exiting"
				break

		time.sleep(cycle_sleep)
	
def cycle_file(callback, args, debug=True):
	regexps = {
		'quit': re.compile('^quit\(\)?$'),
		'next': re.compile('^next\((\d+)\)$'),
		'time': re.compile('^time\((\d\d\d\d-\d\d-\d\d )?(\d\d:\d\d:\d\d)\)$'),
		'key': re.compile('^key\(([\d.]+)\)?$'),
		'help': re.compile('^help\(\)?$'),
	}
	last_command = 'next(1)'
	skip_cycles = 0
	wait_for_time = None
	run_continuously = { 'run': None }

	while True:
		etime = callback(**args)
		if etime is None: continue

		if wait_for_time != None:
			if (wait_for_time-etime.dt).total_seconds() > 0: continue
			else: wait_for_time = None

		if skip_cycles > 0:
			skip_cycles -= 1
			continue

		if run_continuously['run'] != None:
			time.sleep(run_continuously['run'])
			continue

		# ask user for interaction
		while True:
			if os.name != 'nt': sys.stdout.write('\033[1;32m')
			sys.stdout.write("[interactive] %s $ " % (last_command,))
			sys.stdout.flush()
			try:
				line = sys.stdin.readline()
				if len(line) == 0: raise KeyboardInterrupt()
				line = line.strip()
			except KeyboardInterrupt:
				sys.stdout.write("\n")
				raise
			finally:
				if os.name != 'nt': sys.stdout.write('\033[0m')
	
			# if line is empty, use the last command
			if len(line) == 0: line = last_command

			# ALIASes
			if line == 'n': line = 'next(1)'
			elif line == 'q' or line == 'quit': line = 'quit()'
			elif line == 'help': line = 'help()'

			# parse interactive input
			match_name = None
			match_g    = None
			for regexp in regexps.keys():
				g = regexps[regexp].search(line)
				if g != None:
					match_name = regexp
					match_g    = g.groups()
	
			if match_name == None: 
				sys.stdout.write('Invalid command: %s\n' % (line,))
				continue

			elif match_name == 'quit':
				raise KeyboardInterrupt()

			elif match_name == 'next':
				skip_cycles = int(match_g[0])-1

			elif match_name == 'time':
				if etime is None:
					sys.stdout.write('Time shift cannot be before first record is shown\n')
					continue

				f_date = None
				f_time = match_g[1].strip()
				f_tz   = etime.as_datetime().tzinfo

				if match_g[0] == None:
					f_date = etime.as_datetime().strftime("%Y-%m-%d")
				else:
					f_date = match_g[0].strip()

				tmp = datetime.datetime.strptime("%s %s" % (f_date, f_time,), '%Y-%m-%d %H:%M:%S')
				wait_for_time = tmp.replace(tzinfo=f_tz)
				break # do not save to last command
				
			elif match_name == 'key':
				run_continuously['run'] = float(match_g[0])

				def sigint(sig, sframe):
					run_continuously['run'] = None
					signal.signal(signal.SIGINT, run_continuously['original_handler'])
				run_continuously['original_handler'] = signal.signal(signal.SIGINT, sigint)

			elif match_name == 'help':
				print "Interactive mode supports following functions:"
				print "next(%i)                    ... show next $i cycles without waiting for user input" 
				print "time(YYYY-mm-dd HH:MM:SS)   ... skip forward to the output at or after the specified date and time"
				print "time(HH:MM:SS)              ... same as above, but consideres the same date as current one"
				print "key(%f)                     ... show cycles with %f seconds sleep between them until CTRL+C is pressed"
				print "quit()                      ... quit"
				print
				print "Following aliases are define to make it easier to use:"
				print "quit, q         ... quit()"
				print "n               ... next(1)"
				print
				print "Pressing enter on the empty line repeats the last command (where it makes sense)."
				continue

			last_command = line
			break


def simple_command_with_timestamp(sshc, etime, command, info="", vdom=None):
		out = sshc.clever_exec(command, vdom)
		return prepend_timestamp(out, etime, info)

def prepend_timestamp(data, etime, info=""):
		lines = []
		for line in data.split("\n"):
			if len(line) == 0: continue
			lines.append("[%s] (%s) %s" % (etime, info.replace(" ", "_"), line,))
		
		return "\n".join(lines)

def rss():
	import psutil
	import os
	return psutil.Process(os.getpid()).memory_full_info().rss
