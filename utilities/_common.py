import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.SSHCommands import SSHCommands

import argparse
import sys
import time
import getpass

def ssh(args=(), manual=''):
	parser = argparse.ArgumentParser(description='FortiMonitor')

	# add global arguments
	parser.add_argument('--host', required=True, help='FortiGate hostname or IP address')
	parser.add_argument('--user', default="admin", help='User name to log in as, default "admin"')
	parser.add_argument('--password', default="", help='Password to log in with, default empty')
	parser.add_argument('--askpass', default=False, action="store_true", help='Ask for password on standard input')
	parser.add_argument('--credfile', default=None, help='File to read the credentials from - 1st line username, 2nd line password')
	parser.add_argument('--port', default=22, type=int, help='SSH port, default 22')
	parser.add_argument('--time-format', default='human-with-offset', choices=['human-with-offset', 'human', 'timestamp', 'iso'], help='Format of the date and time')
	parser.add_argument('--time-source', default='device', choices=['device', 'local'], help='How to retrieve data and time')
	parser.add_argument('--debug', default=False, action="store_true", help='Enable debug outputs')
	parser.add_argument('--manual', default=False, action="store_true", help='Show manual')
	parser.add_argument('--ignore-ssh-key', default=False, action="store_true", help='Ignore SSH server key problems')
	parser.add_argument('--max-cycles', default=None, type=int, help='Maximum cycles to run')
	
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
	
	if args.credfile != None:
		with open(args.credfile, "r") as f:
			args.user     = f.readline().strip("\n")
			args.password = f.readline().strip("\n")
	
	elif args.askpass:
		args.password = getpass.getpass("Password for %s@%s: " % (args.user, args.host,))
	
	sshc = SSHCommands(args.host, args.user, args.password, args.port, args.ignore_ssh_key)

	# do not return global arguments values (they are still saved in SSHCommands object though)
	# exception is the "debug" parameter which we do not delete
	del args.host
	del args.user
	del args.password
	del args.credfile
	del args.port
	del args.ignore_ssh_key

	sshc.set_local_param('args', args)

	return (sshc, args)


def cycle(callback, args, min_interval, cycles_left=None, debug=True):
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
