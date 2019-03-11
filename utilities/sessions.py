#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _common import ssh, prepend_timestamp

import sys

sshc, args = ssh([
	{ 'name':'--cycle-time',   'type':int, 'default':1,  'help':'How long should each cycle take' },
	{ 'name':'--action', 'type':str, 'choices':['dump'], 'default':'dump', 'help': 'What to do - "dump"' },
], """
""")

def divide(data, info):
	sessions = []

	while True:
		# find the next session
		i = data.find("\r\n\r\n")
		if i == -1: break

		ses = data[:i]
		data = data[i+4:]

		# remove empty lines at the beginning
		while ses[0] == '\r' or ses[0] == '\n':
			ses = ses[1:]

		# this line means the end of list
		i = ses.find('total session')
		if i != -1: 
			ses = ses[:i-1]
			info['done'] = True

		# save the session data
		sessions.append(ses)

	return (sessions, data)

def result_dump(session, info):
	print session
	print

def finished(info):
	if info['done']: return ''
	return None

def do(sshc, cycle_time, action):
	if action == 'dump':
		result = result_dump
	else: return

	info = { 'info': { 'done': False } }
	sshc.continuous_exec("diagnose sys session list", divide, result, finished, info)

if __name__ == '__main__':
	try:
		do(sshc, args.cycle_time, args.action)
	except KeyboardInterrupt:
		sshc.destroy()

