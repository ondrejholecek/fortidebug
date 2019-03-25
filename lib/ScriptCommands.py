from lib.ScriptFile import ScriptFile
import json
import datetime
import pytz
import re

###
### This is the alternative class to SSHCommands.
### It tries to simulate the behavior of SSHCommands class,
### but reads the outputs from the JSONline file instead
### of the ssh connection.
###

class ScriptCommands:
	def __init__(self, filename):
		self.filename = filename
		self.script   = ScriptFile(filename)

		self.re_status_hostname = re.compile("^Hostname:\s*(.*)$", re.M)
		self.re_status_vdoms    = re.compile("^Virtual domain configuration:\s*(.*)$", re.M)
		self.re_status_mgmtvdom = re.compile("^Current virtual domain:\s*(.*)$", re.M)
		self.re_status_version  = re.compile('(\S)\s+Version:\s+(.*?)\s+v(\d+)\.(\d+)\.(\d+),build(\d+),(\d+)') # does not start with ^ because the is prompt
		                                                                                                        # and we also use it to get the prompt char.
		self.re_status_serial   = re.compile('^Serial-Number:\s*(.*)$', re.M)
		self.re_status_module_serial = re.compile('^Module Serial-Number:\s*(.*)$', re.M)

		self.local_params = {
			'time_offset_seconds': None,
		}

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

		self.last_used_timestamp = 0

		self.basics()

	def is_live(self):
		return False

	def set_local_param(self, name, value):
		self.local_params[name] = value
	
	def get_local_param(self, name):
		return self.local_params[name]

	def destroy(self):
		return

	def basics(self):
		# read automatic command which should be at the beginning of the file
		obj = self.clever_exec(None)
		#print json.dumps(obj, indent=4)

		# fill something from the file direectly
		self.info['connected_on']       = obj['info']['connected_on']
		self.info['nonce']              = obj['info']['nonce']
		self.info['hostname_extension'] = obj['info']['hostname_extension']
		self.info['prompt_character']   = obj['info']['prompt_character']

		# read get system status output
		gss = None
		for cmd in obj['internal_commands']:
			if cmd ['command'] == 'get system status':
				gss = obj['info']['prompt'] + cmd['output']

		if gss == None:
			raise Exception("File does not contain 'get system status' in automatic commands section")

		self.parse_system_status(gss)

		# save the time offset as it was during the data collection
		self.local_params['time_offset_seconds'] = obj['flags']['time_offset'] * 60

	def parse_system_status(self, gss):
		g = self.re_status_version.search(gss)
		if not g: 
			raise Exception("Cannot find version in 'get system status' output")
		else:
			self.info['device'] = g.group(2)
			self.info['version']['major'] = int(g.group(3))
			self.info['version']['minor'] = int(g.group(4))
			self.info['version']['patch'] = int(g.group(5))
			self.info['version']['build'] = int(g.group(6))
			self.info['version']['compilation'] = int(g.group(7))

		g1 = self.re_status_module_serial.search(gss)
		g2 = self.re_status_serial.search(gss)
		if g1:
			self.info['serial'] = g1.group(1)
		elif g2:
			self.info['serial'] = g2.group(1)
		else:
			raise Exception("Cannot find serial number in 'get system status' output")

		g = self.re_status_hostname.search(gss)
		if not g: 
			raise Exception("Cannot find hostname in 'get system status' output")
		else:
			self.info['hostname'] = g.group(1)

		g = self.re_status_mgmtvdom.search(gss)
		if not g: 
			raise Exception("Cannot find management vdom in 'get system status' output")
		else:
			self.info['mgmt_vdom'] = g.group(1)

		g = self.re_status_vdoms.search(gss)
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

	def special_commands(self, command, vdom):
		if command in ('exe date', 'exe time'):
			d = pytz.UTC.localize(datetime.datetime.utcfromtimestamp(self.last_used_timestamp))

			time_offset = self.get_local_param('time_offset_seconds')
			if time_offset != None:
				d += datetime.timedelta(seconds=time_offset)
				
			if command == 'exe date':
				return d.strftime("current date is: %Y-%m-%d\n")
			elif command == 'exe time':
				return d.strftime("current time is: %H:%M:%S\nlast ntp sync:%a %m %d %H:%M:%S %Y\n")

		return None

	def clever_exec(self, command, vdom=None):
#		print command, vdom

		special = self.special_commands(command, vdom)	
		if special != None: return special

		while True:
			obj = self.script.next()
			if obj == None: 
				raise KeyboardInterrupt()
	
			if obj['command'] == command and obj['context'] == vdom:
				self.last_used_timestamp = obj['timestamp']
				return obj['output']

	def continuous_exec(self, command, divide_callback, result_callback, exit_callback, args={}, vdom=None, simulate=None):
		raise Exception("Continuous commands from script file are not supported yet")
