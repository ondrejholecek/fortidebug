#!/usr/bin/env python2.7

import paramiko
import time
import re
import random

# DEBUG vvv
def rss():
	import psutil
	import os
	return psutil.Process(os.getpid()).memory_full_info().rss
# ^^^

class SSHCommands:
	def __init__(self, hostname, username, password, port, ignore_ssh_key=False, ic_sleep=0.01, show_debug_outputs=False, hostname_extension=None):
		self.ssh_hostname = hostname
		self.ssh_username = username
		self.ssh_password = password
		self.ssh_port     = port
		self.ssh_ignore_key = ignore_ssh_key
		self.intercommand_sleep = ic_sleep

		self.re_status_hostname = re.compile("^Hostname:\s*(.*)$", re.M)
		self.re_status_vdoms    = re.compile("^Virtual domain configuration:\s*(.*)$", re.M)
		self.re_status_mgmtvdom = re.compile("^Current virtual domain:\s*(.*)$", re.M)
		self.re_status_version  = re.compile('(\S)\s+Version:\s+(.*?)\s+v(\d+)\.(\d+)\.(\d+),build(\d+),(\d+)') # does not start with ^ because the is prompt
		                                                                                                        # and we also use it to get the prompt char.
		self.re_status_serial   = re.compile('^Serial-Number:\s*(.*)$', re.M)

		self.local_params = {}
		self.info = {}
		self.info['hostname']      = None
		self.info['vdoms_enabled'] = None
		self.info['prompt']        = None
		self.info['mgmt_vdom']     = None
		self.info['device']        = None
		self.info['serial']        = None
		self.info['version']       = {
			'major': None,
			'minor': None,
			'patch': None,
			'build': None,
			'compilation': None,
		}
		self.info['connected_on']  = time.time()
		self.info['nonce']         = random.randint(1000000, 9999999)
		self.info['hostname_extension'] = hostname_extension
	
		self.client  = None
		self.channel = None

		self.connect()
		self.basics()
		self.open_channel(show_debug_outputs)
	
	def get_info(self):
		return self.info

	def set_local_param(self, name, value):
		self.local_params[name] = value
	
	def get_local_param(self, name):
		return self.local_params[name]

	def destroy(self):
		if self.channel != None: self.channel.close()
		if self.client != None: self.client.close()

	def connect(self):
		self.client = paramiko.SSHClient()
		if self.ssh_ignore_key:
			self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
		else:
			self.client.load_system_host_keys()

		self.client.connect(self.ssh_hostname, username=self.ssh_username, password=self.ssh_password, port=self.ssh_port)
	
	def open_channel(self, show_debug_outputs):
		self.channel = self.client.invoke_shell(width=300, height=9999999)
		if self.info['vdoms_enabled']:
			self.channel.send("config global\n")
		self.read_until_prompt()

		# improve debugging outputs
		self.channel.send("diagnose debug console retry-log-msg enable\n")
		self.read_until_prompt()

		if show_debug_outputs:
			# reset debugging and enable debug outputs
			self.channel.send("diagnose debug reset\n")
			self.read_until_prompt()
			self.channel.send("diagnose debug duration 0\n")
			self.read_until_prompt()
			self.channel.send("diagnose debug enable\n")
			self.read_until_prompt()

	def basics(self):
		tmp = self.basic_exec("get system status")

		# some special cases
		if 'Reached maximum number of logged in administrators.' in tmp:
			raise Exception("Reached maximum number of logged in administrators. Log in manually and clear them.")

		#
		g = self.re_status_version.search(tmp)
		if not g: 
			raise Exception("Cannot find version in 'get system status' output")
		else:
			self.info['prompt_character'] = g.group(1)
			self.info['device'] = g.group(2)
			self.info['version']['major'] = int(g.group(3))
			self.info['version']['minor'] = int(g.group(4))
			self.info['version']['patch'] = int(g.group(5))
			self.info['version']['build'] = int(g.group(6))
			self.info['version']['compilation'] = int(g.group(7))

		g = self.re_status_serial.search(tmp)
		if not g: 
			raise Exception("Cannot find serial number in 'get system status' output")
		else:
			self.info['serial'] = g.group(1)

		g = self.re_status_hostname.search(tmp)
		if not g: 
			raise Exception("Cannot find hostname in 'get system status' output")
		else:
			self.info['hostname'] = g.group(1)

		g = self.re_status_mgmtvdom.search(tmp)
		if not g: 
			raise Exception("Cannot find management vdom in 'get system status' output")
		else:
			self.info['mgmt_vdom'] = g.group(1)

		g = self.re_status_vdoms.search(tmp)
		if not g: 
			raise Exception("Cannot find vdoms configuration in 'get system status' output")

		if 'enable' in g.group(1):
			self.info['vdoms_enabled'] = True
		elif 'disable' in g.group(1):
			self.info['vdoms_enabled'] = False
		else:
			raise Exception("Cannot find out whether VDOMs are enabled in 'get system status' output")
			
		hostname = self.info['hostname']
		if self.info['hostname_extension'] != None:
			hostname += self.info['hostname_extension']

		if self.info['vdoms_enabled']:
			self.info['prompt'] = "%s (global) %s " % (hostname, self.info['prompt_character'],)
		else:
			self.info['prompt'] = "%s %s " % (hostname, self.info['prompt_character'],)

	def basic_exec(self, command):
		stdin, stdout, stderr = self.client.exec_command(command)
		return stdout.read(102400)

	def read_until_prompt(self):
		data = ""
		while True:
			data += self.channel.recv(1024)
			if data[-len(self.info['prompt']):] == self.info['prompt']:
				break

		return data[:-len(self.info['prompt'])]
	
	def send_command(self, command):
		self.channel.send(command + "\n")

		rd = 0
		while rd < len(command)+3:
			tmp = self.channel.recv(len(command)+3-rd)
			rd += len(tmp)

	def clever_exec(self, command, vdom=None):
		if vdom != None and self.info['vdoms_enabled']:
			if len(vdom) == 0: vdom = self.info['mgmt_vdom']
			self.send_command("sudo %s %s" % (vdom, command,))
		else:
			self.send_command(command)

		out = self.read_until_prompt()
		time.sleep(self.intercommand_sleep)
		return out.strip("\n")
	
	def continuous_exec(self, command, divide_callback, result_callback, exit_callback, args={}, vdom=None, simulate=None):
		if vdom != None and self.info['vdoms_enabled']:
			if len(vdom) == 0: vdom = self.info['mgmt_vdom']
			if not simulate: self.send_command("sudo %s %s" % (vdom, command,))
		else:
			if not simulate: self.send_command(command)

		data = ""
		while True:
			if not simulate:
				data += self.channel.recv(1024)
			else:
				tmp = simulate.read(1024)
				if len(tmp) == 0:
					args['info']['no_new_data'] = True
				else:
					args['info']['no_new_data'] = False
				data += tmp

			r = divide_callback(data, **args)

			# simple None means there is no full results available in the output
			if r == None: continue

			# if there is a result, we should get back the list of results and the unprocessed part
			(result, data) = r
			# however, the result can be None, which means we just need to strip some unrelated outputs
			# but do not return it as the result
			if result != None: 
				for r in result:
					result_callback(r, **args)

			# should we finish?
			ex = exit_callback(**args)
			if ex != None:
				if not simulate:
					self.channel.send(ex)
					self.read_until_prompt()
				else:
					pass

				break
