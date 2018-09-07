#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from _common import ssh, cycle, prepend_timestamp

import xml.etree.ElementTree

import re
import sys
import copy
import time
import json

sshc, args = ssh([
	{ 'name':'--cycle-time',   'type':int, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--script',       'required':True,  'help':'The XML file with commands to execute' },
	{ 'name':'--list',         'default':False, 'action':'store_true',  'help':'List existing cycles and quit' },
	{ 'name':'--cycle',        'default':None, 'help':'Run the specified cycle' },
	{ 'name':'--profile',      'default':None, 'help':'Override the default profile name for the cycle' },
	{ 'name':'--param',        'default':[], 'action':'append', 'help':'Override some parameters' },
	{ 'name':'--output',       'default':None, 'help':'Name of the output file (.jsonl format)' },
	{ 'name':'--quiet',        'default':False, 'action':'store_true',  'help':'Do not show commands on stdout' },
], """
This utility allows you to write and run custom commands and/or standard parsers on the remote FortiGate. 

The execution is controlled by the XML file (passed by "--script" option) which contains one or more "cycles".
The "cycle" has a name and description and it contains the definition of the actions to take (like run
simple command, run parser, etc.). At one time only once cycle can be executed and its name is passed 
by "--cycle" option. To find all available cycle names, use option "--list" (together with "--script"). 

Format of the XML file and all its options is described in the sample XML file ("samples/script.xml").

By default only the human readable output of the commands is print on standard output and this can be 
disabled with "--quiet" option. To write a computer-frieldy .jsonl output to a file, use "--output" option.

Each cycle has pre-assigned profile that controls its behavior. At this moment, only the "interscript sleep"
control is implemented. The default profile can be overriden with "--profile" command.

Each cycles also has pre-assigned a parameter list. This is a list of variables that can be altered when
the program is running (either manually or as a side effect of some command). It is not possible to choose
which parameter list is assigned to the cycle, but it is possible to change the paramaters with "--param".
Format of this parameter can be either "s:name:value" which sets the parameter "name" to a text "value",
or it can be "l:name:,:value1,value2,..." which creates a list called "name" with values from 4th field
delimited by the character in the 3rd filed (',' in this case).
""")

class MyException(Exception): pass

class Script:
	def __init__(self, sshc, args):
		self.sshc     = sshc

		self.filename = args.script
		self.list     = args.list
		self.cycle    = args.cycle
		self.profile  = args.profile
		self.params   = args.param
		self.quiet    = args.quiet

		if args.output == None:
			self.output   = None
		else:
			self.output   = open(args.output, "ab")


		self.profiles    = { 'default': {} }
		self.parameters  = {}

		self.root     = None

		self.load()

	def load(self):
		e = xml.etree.ElementTree.parse(self.filename).getroot()
	
		# verify we can work with this file
		if e.tag != "fortimonitor_scriptfile":
			raise MyException("The file '%s' is not FortiMonitor script file" % (self.filename,))
		
		try:
			version = int(e.attrib['version'])
		except:
			raise MyException("The script file does not contain a version")
	
		if version > 1:
			raise MyException("The script file format is newer than this utility can process")

		self.profiles['default'] = {
			'intercommand_sleep'   : 0.1,
		}

		self.parameters['default'] = {}

		self.root = e

	def load_profile(self, name):
		# if the profile was already loaded, just return it
		if name in self.profiles:
			return self.profiles[name]

		# otherwise we need to load it from xml file
		all_profiles = self.root.find('profiles')
		if all_profiles == None:
			raise MyException("Script file does not contain any profiles")

		prof = all_profiles.find("./profile[@name='%s']" % (name,))
		if prof == None:
			raise MyException("Cannot find profile with name '%s'" % (name,))

		#
		p = copy.deepcopy(self.profiles['default'])
		for opt in prof:
			if opt.tag == 'intercommand_sleep':
				p['intercommand_sleep'] = float(opt.text)
			else:
				raise MyException("Invalid profile option '%s'" % (opt.tag,))

		self.profiles[name] = p
		return self.profiles[name]

	def load_parameters(self, name):
		# cached
		if name in self.parameters:
			return self.parameters[name]

		# otherwise we need to load it from xml file
		all_plists = self.root.find('plists')
		if all_plists == None:
			raise MyException("Script file does not contain any parameter lists")

		params = all_plists.find("./parameters[@name='%s']" % (name,))
		if params == None:
			raise MyException("Cannot find parameter list with name '%s'" % (name,))

		# load parameters from configuration
		p = {}
		for param in params:
			if param.tag != 'param':
				raise MyException("Unknown parameter element '%s'" % (param.tag,))

			for a in ('name', 'value'):
				if a not in param.attrib:
					raise MyException("Parameter is missing '%s' attribute" % (a,))

			name  = param.attrib['name']
			value = param.attrib['value']

			try:
				ptype = param.attrib['type']
			except KeyError:
				ptype = 'str'

			if ptype == 'str':
				p[name] = value

			elif ptype == 'list':
				delimiter = value[0]
				values    = value[1:].split(delimiter)
				p[name]   = values

		# override parameters from command line
		for cparam in self.params:
			if cparam.startswith('s:'):
				try:
					(cname, cvalue) = cparam[2:].split(':', 1)
				except Exception, e:
					raise MyException("Invalid --param option '%s'" % (cparam,))

			elif cparam.startswith('l:'):
				try:
					(cname, cdel, cdata) = cparam[2:].split(':', 2)
					cvalue = cdata.split(cdel)
				except Exception, e:
					raise MyException("Invalid --param option '%s'" % (cparam,))

			else:
				raise Exception("Unknown --param option type '%s'" % (cparam,))
				
			p[cname] = cvalue

		self.parameters[name] = p
		return self.parameters[name]

	def do(self):
		# what we want to do
		if self.list:
			all_cycles = self.root.find('cycles')
			if all_cycles == None:
				raise MyException("Script file does not contain any cycles")
	
			for cycle in all_cycles.findall('cycle'):
				print "%-20s : %s" % (cycle.attrib['name'], cycle.attrib['desc'],)

			raise KeyboardInterrupt()
	
		elif self.cycle != None:
			c = self.root.find("./cycles/cycle[@name='%s']" % (self.cycle,))
			if c == None:
				raise MyException("Cannot find cycle '%s'" % (args.cycle,))
	
			self.do_cycle(c)

	def do_cycle(self, c):
		# if there is a profile name we will use it, otherwise the default profile is used
		if self.profile != None:
			profile = self.load_profile(self.profile)
		elif 'profile' in c.attrib:
			profile = self.load_profile(c.attrib['profile'])
		else:
			profile = self.load_profile('default')

		# load parameters
		if 'parameters' in c.attrib:
			params = self.load_parameters(c.attrib['parameters'])
		else:
			params = self.load_parameters('default')

		# all 'c' attributes must be checked before continuing
		self.do_commands(c, profile, params)

	def do_commands(self, c, profile, params):
		# do not check any attributes of 'c' because it can be anything!

		for child in c:
			self.last_command_time = ParserCurrentTime(self.sshc).get()

			if child.tag == 'simple':
				self.do_simple_command(child, profile, params)

			elif child.tag == 'foreach':
				self.do_foreach(child, profile, params)
	
			elif child.tag == 'subcycle':
				self.do_subcycle(child, profile, params)
	
			elif child.tag == 'parser':
				self.do_parser(child, profile, params)
	
			elif child.tag == 'dump_params':
				self.do_dump_params(child, profile, params)
	
			else:
				print >>sys.stderr, "Warning: unknown cycle command '%s', ignoring" % (child.tag,)

			if profile['intercommand_sleep'] > 0:
				time.sleep(profile['intercommand_sleep'])


	def do_simple_command(self, cmd, profile, params):
		vdom    = None
	
		if 'context' in cmd.attrib:
			if cmd.attrib['context'] == 'global':
				vdom    = None
			elif cmd.attrib['context'] == 'mgmt_vdom':
				vdom    = ''
			elif cmd.attrib['context'] == 'vdom':
				if 'vdom' not in cmd.attrib:
					raise MyException("Simple command: vdom context but no vdom name for '%s'" % (cmd.text,))
	
				vdom    = cmd.attrib['vdom']
			else:
				raise MyException("Simple command: unknown context '%s'" % (cmd.attrib['context'],))
	
		fortios_cmd = cmd.text.strip(' ')

		# replace parameters
		regex = re.compile('^(.*?)\${(.+?)}(.*)$')
		while True:
			g = regex.search(fortios_cmd)
			if g == None: break

			if g.group(2) not in params:
				v = ''
			else:
				v = params[g.group(2)]

			fortios_cmd = g.group(1) + v + g.group(3)

		# run the command
		result = sshc.clever_exec(fortios_cmd, vdom)
		self.save_result(fortios_cmd, vdom, result, self.last_command_time)

	def do_foreach(self, cmd, profile, params):
		for tmp in ('list', 'use'):
			if tmp not in cmd.attrib:
				raise MyException("Foreach: attribute '%s' missing" % (tmp,))

		if cmd.attrib['list'] not in params:
			raise MyException("Foreach: list '%s' does not exist in params")
		if type(params[cmd.attrib['list']]) != type([]):
			raise MyException("Foreach: parameter '%s' is not a list")

		# save original value
		original = None
		if cmd.attrib['use'] in params: original = params[cmd.attrib['use']]

		# run the cycle
		for it in params[cmd.attrib['list']]:
			params[cmd.attrib['use']] = it
			self.do_commands(cmd, profile, params)

		# restore original
		if original == None:
			del params[cmd.attrib['use']]
		else:
			params[cmd.attrib['use']] = original

	def do_subcycle(self, cmd, profile, params):
		for tmp in ('name',):
			if tmp not in cmd.attrib:
				raise MyException("Subcycle: attribute '%s' missing" % (tmp,))

		# find the right sub-cycle
		c = self.root.find("./cycles/cycle[@name='%s']" % (cmd.attrib['name'],))
		if c == None:
			raise MyException("Cannot find sub-cycle '%s'" % (cmd.attrib['name'],))
	
		self.do_commands(c, profile, params)

	def do_parser(self, cmd, profile, params):
		for tmp in ('name',):
			if tmp not in cmd.attrib:
				raise MyException("Parser: attribute '%s' missing" % (tmp,))

		pname = cmd.attrib['name']

		# load parser
		try:
			parserclass = getattr(__import__('parsers.' + pname, fromlist=['Parser'+pname]), 'Parser'+pname)
		except Exception, e:
			raise MyException("Parser: unable to load parser '%s': '%s'" % (pname, str(e),))

		# get input parameters
		iparams = []
		inp = cmd.find('input')
		if inp != None:
			for iparam in inp:
				# read requested type
				ptype = str
				if 'type' in iparam.attrib: 
					if iparam.attrib['type'] == 'str':
						ptype = str
					elif iparam.attrib['type'] == 'int':
						ptype = int
					else:
						raise MyException("Parser: input parameter type '%s' is invalid" % (iparam.attrib['type'],))


				# get value
				# ... from parameter list
				if iparam.tag == 'parameter':
					if 'name' not in iparam.attrib: raise MyException("Parser: input parameter specified by no name")
					if iparam.attrib['name'] not in params: raise MyException("Parser: input parameter specified by name that does not exist")

					value = copy.deepcopy(params[iparam.attrib['name']])
				
				# ... statically defined
				elif iparam.tag == 'static':
					if 'value' not in iparam.attrib: raise MyException("Parser: input static specified by no value")
					value = iparam.attrib['value']

				else:
					raise MyException("Parser: unknown input parameter type '%s'" % (iparam.tag,))

				# convert before save
				if type(value) == type([]):
					for i in range(len(value)):
						value[i] = ptype(value[i])
				else:
					value = ptype(value)

				# save it to function parameter list
				iparams.append(value)

		# execute it
		parser = parserclass(self.sshc)
		try:
			result = parser.get(*iparams)
		except Exception, e:
			raise MyException("Parser: unable to call parser '%s': '%s'" % (pname, str(e),))

		self.save_result("Parser:%s:%s" % (pname, iparams,), None, result, self.last_command_time)

		# if we want to store some parameters, do it
		store = cmd.find('store')
		if store != None:
			for sparam in store.findall('param'):
				for tmp in ('type', 'use'):
					if tmp not in sparam.attrib:
						raise MyException("Parser: store attribute '%s' missing" % (tmp,))

				simple = parser.simple_value(result, sparam.attrib['type'])
				params[sparam.attrib['use']] = simple

	def do_dump_params(self, cmd, profile, params):
		self.save_result("internal:dump_params", None, params, self.last_command_time)

	def save_result(self, command, vdom, output, etime):
		if self.output != None:
			tmp = {
				'command': command,
				'context': vdom,
				'output' : output,
				'time': str(etime),
			}
			self.output.write(json.dumps(tmp) + "\n")
			self.output.flush()

		if not self.quiet:
			print prepend_timestamp(str(output), etime, 'script')
			
	

if __name__ == '__main__':
	script = Script(sshc, args)
	try:
		cycle(script.do, {}, args.cycle_time, cycles_left=[args.max_cycles], debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

