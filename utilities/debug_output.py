#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.Processes import ParserProcesses
from _common import ssh, cycle, simple_command_with_timestamp, prepend_timestamp

import re
import sys
import time

sshc, args = ssh([
	{ 'name':'--command',      'required':True, 'action':'append', 'help':'What command to keep running, can repeat' },
	{ 'name':'--vdom',         'default':None, 'help':'VDOM to use when executing the command' },
	{ 'name':'--mgmt-vdom',    'default':False, 'action':'store_true',  'help':'Use management VDOM to execute the command' },
	{ 'name':'--string',    'default':' \b', 'help':'String to send every --keepalive-time' },
	{ 'name':'--keepalive-time',   'type':int, 'default':30,  'help':'How often to send keepalive' },
	{ 'name':'--outfile',    'default':None, 'help':'Save the output also to this file' },
], """
""")

def start(sshc, commands, vdom, outs):
	etime = ParserCurrentTime(sshc).get()
	
	for command in commands:
		g = re.search('^<(.*?)>\s*(.*?)\s*$', command)
		if not g:
			this_vdom    = vdom
			this_command = command
		else:
			this_vdom    = g.group(1)
			this_command = g.group(2)
			if this_vdom.lower() == 'global': this_vdom = None

		out = sshc.clever_exec(this_command, this_vdom)
		for line in out.split("\n"):
			for out in outs:
				print >>out, prepend_timestamp(line, etime, this_command)
				out.flush()
	
	
def continuous_read(sshc, keepalive_time, keepalive_string, outs):
	last_ka = time.time()

	while True:
		data = ""
		while sshc.channel.recv_ready():
			tmp = sshc.channel.recv(128)
			if len(tmp) == 0: break
			data += tmp

		if len(data) > 0:
			for out in outs:
				out.write(data)
				out.flush()

		if (time.time() - last_ka) >= keepalive_time:
			sshc.channel.send(keepalive_string)
			last_ka = time.time()

		time.sleep(0.2)

if __name__ == '__main__':
	#
	vdom = None

	if args.mgmt_vdom == True and args.vdom != None:
		print "Error: options '--vdom' and '--mgmt-vdom' are mutually exclusive"
		sys.exit(0)
	elif args.mgmt_vdom == True:
		vdom = ''
	elif args.vdom != None:
		vdom = args.vdom

	#
	outs = []
	outs.append(sys.stdout)

	if args.outfile != None:
		f = open(args.outfile, "ab")
		outs.append(f)

	try:
		start(sshc, args.command, vdom, outs)
		continuous_read(sshc, args.keepalive_time, args.string.decode('string_escape'), outs)
	except KeyboardInterrupt:
		sshc.destroy()

