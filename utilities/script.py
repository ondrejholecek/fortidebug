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
import requests
import datetime
import bz2

sshc, args = ssh([
	{ 'name':'--cycle-time',   'type':int, 'default':30,  'help':'How long should each cycle take' },
	{ 'name':'--script',       'required':True,  'help':'The XML file with commands to execute' },
	{ 'name':'--list',         'default':False, 'action':'store_true',  'help':'List existing cycles and quit' },
	{ 'name':'--cycle',        'default':None, 'action': 'append', 'help':'Run the specified cycle (can repeat)' },
	{ 'name':'--profile',      'default':None, 'help':'Override the default profile name for the cycle' },
	{ 'name':'--param',        'default':[], 'action':'append', 'help':'Override some parameters' },
	{ 'name':'--output',       'default':None, 'help':'Name of the output file (.jsonl format)' },
	{ 'name':'--compress',     'type':int, 'default':10,  'help':'How many outputs to compress at once, 0 disables compression' },
	{ 'name':'--quiet',        'default':False, 'action':'store_true',  'help':'Do not show commands on stdout' },
], """
This utility allows you to write and run custom commands and/or standard parsers on the remote FortiGate. 

The execution is controlled by the XML file (passed by "--script" option) which contains one or more "cycles".
The "cycle" has a name and description and it contains the definition of the actions to take (like run
simple command, run parser, etc.). One or more cycle names can be selected by "--cycle" option. If there are
more cycles, they are exectuted in specified order and the "--cycle-time" option refers to the time of all
selected cycles togeter. To find all available cycle names, use option "--list" (together with "--script"). 

Format of the XML file and all its options is described in the sample XML file ("samples/script.xml").

By default only the human readable output of the commands is print on standard output and this can be 
disabled with "--quiet" option. To write a computer-frieldy .jsonl output to a file, use "--output" option.
If "--compress" option is not used, there are 10 outputs buffered before they are compressed and written
to the output file. This cna be changed and 0 means to disable compression completely.

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

		self.output_buffer_length = args.compress
		self.output_buffer        = []

		if args.output == None:
			self.output   = None
		else:
			self.output   = open(args.output, "ab")

		self.real_filename = None

		self.profiles    = { 'default': {} }
		self.parameters  = {}

		self.root     = None

		self.load()

	def destroy(self):
		self.save_result_compress()

	def load(self):
		# is it a local file (no prefix or "file://") or remote file (*://)?
		g = re.search("^(\S+)://(.*)$", self.filename)
		if g == None:
			e = xml.etree.ElementTree.parse(self.filename).getroot()
			self.real_filename = self.filename
		elif g.group(1) == 'file':
			e = xml.etree.ElementTree.parse(g.group(2)).getroot()
			self.real_filename = g.group(2)
		else:
			r = requests.get(self.filename)
			if r.status_code != 200: raise MyException("Unable to download file '%s'" % (self.filename,))
			self.real_filename = r.url
			e = xml.etree.ElementTree.fromstring(r.text)
			
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
		if all_profiles != None:
			prof = all_profiles.find("./profile[@name='%s']" % (name,))
		else:
			prof = None

		# any profile is based on 'default' profile with changes
		p = copy.deepcopy(self.profiles['default'])

		# if the requested profile does not exist, just use the default unchanged
		if prof == None:
			print >>sys.stderr, "Warning: profile '%s' does not exist, using the default profile" % (name,)

		else:
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
			for sc in self.cycle:
				c = self.root.find("./cycles/cycle[@name='%s']" % (sc,))
				if c == None:
					raise MyException("Cannot find cycle '%s'" % (sc,))
	
				self.do_cycle(c)

		else:
			print >>sys.stderr, "Nothing to do. Specify the cycle name with '--cycle' option or use '--list' option to find out the cycle name."
			sys.exit(1)

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
			self.last_command_time      = ParserCurrentTime(self.sshc).get()
			self.last_command_time_real = time.time()

			if child.tag == 'simple':
				self.do_simple_command(child, profile, params)

			elif child.tag == 'continuous':
				self.do_continuous_command(child, profile, params)

			elif child.tag == 'foreach':
				self.do_foreach(child, profile, params)
	
			elif child.tag == 'subcycle':
				self.do_subcycle(child, profile, params)
	
			elif child.tag == 'parser':
				self.do_parser(child, profile, params)
	
			elif child.tag == 'version':
				self.do_version(child, profile, params)
	
			elif child.tag == 'set':
				self.do_set(child, profile, params)
	
			elif child.tag == 'unset':
				self.do_unset(child, profile, params)
	
			elif child.tag == 'merge':
				self.do_merge(child, profile, params)
	
			elif child.tag == 'dump_params':
				self.do_dump_params(child, profile, params)
	
			elif child.tag == 'echo':
				self.do_echo(child, profile, params)
	
			else:
				print >>sys.stderr, "Warning: unknown cycle command '%s', ignoring" % (child.tag,)

			if profile['intercommand_sleep'] > 0:
				time.sleep(profile['intercommand_sleep'])


	def element_get_context(self, cmd, profile, params):
		vdom    = None
	
		if 'context' in cmd.attrib:
			if cmd.attrib['context'] == 'global':
				vdom    = None
			elif cmd.attrib['context'] == 'mgmt_vdom':
				vdom    = ''
			elif cmd.attrib['context'] == 'vdom':
				if 'vdom' not in cmd.attrib:
					raise MyException("Vdom context present but no vdom name for '%s'" % (cmd.text,))
	
				vdom    = cmd.attrib['vdom']
			else:
				raise MyException("Unknown context '%s'" % (cmd.attrib['context'],))

		return vdom

	def element_get_command(self, cmd, profile, params):
		fortios_cmd = cmd.text.strip()

		# replace parameters
		regex = re.compile('^(.*?)\${(.+?)}(.*)$')
		while True:
			g = regex.search(fortios_cmd)
			if g == None: break

			if g.group(2) not in params:
				v = ''
			else:
				v = params[g.group(2)]

			fortios_cmd = g.group(1) + str(v) + g.group(3)

		return fortios_cmd

	def do_simple_command(self, cmd, profile, params):
		
		vdom = self.element_get_context(cmd, profile, params)
		fortios_cmd = self.element_get_command(cmd, profile, params)
	
		# run the command
		result = sshc.clever_exec(fortios_cmd, vdom)
		self.save_result(fortios_cmd, vdom, result, self.last_command_time, params)

	def do_continuous_command(self, cmd, profile, params):
		
		vdom = self.element_get_context(cmd, profile, params)
		fortios_cmd = self.element_get_command(cmd, profile, params)

		# continuous parameters
		for tmp in ('separator', 'timeout', 'quit'):
			if tmp not in cmd.attrib:
				raise MyException("Continuous_command: attribute '%s' missing" % (tmp,))

		sep  = cmd.attrib['separator']
		quit = cmd.attrib['quit'].decode('unicode_escape')

		tmo = int(cmd.attrib['timeout'])
		end_time = time.time() + tmo

		if 'ignore' in cmd.attrib:
			ign = cmd.attrib['ignore'].decode('unicode_escape')
		else:
			ign = None

		# prepare sub-functions
		def sub_divide(data, cache):
			if ign != None:
				data = data.replace(ign, '')

			s = data.split(sep)
			if len(s) == 1:  # not found
				return (None, data)

			elif len(s) == 2: # found one, but may not be finished yet
				return (None, data)

			else:
				result = []
				for i in range(len(s)-1):
					if len(s[i]) == 0: continue
					result.append("%s%s" % (sep, s[i],))

				rest = sep+s[-1]
				return (result, rest)
					
		def sub_result(data, cache):
			real_diff = time.time() - self.last_command_time_real
			adj_time  = (self.last_command_time + datetime.timedelta(seconds=real_diff)).replace(microsecond=0)
			self.save_result(fortios_cmd, vdom, data, adj_time, params)

		def sub_exit(cache):
			if time.time() > end_time: return quit
			else: return None
	
		# run the command
		sshc.continuous_exec(fortios_cmd, sub_divide, sub_result, sub_exit, {'cache':{}}, vdom)

	def do_foreach(self, cmd, profile, params):
		for tmp in ('list', 'name'):
			if tmp not in cmd.attrib:
				raise MyException("Foreach: attribute '%s' missing" % (tmp,))

		if cmd.attrib['list'] not in params:
			raise MyException("Foreach: list '%s' does not exist in params")
		elif params[cmd.attrib['list']] == None:
			return
		elif type(params[cmd.attrib['list']]) != type([]):
			raise MyException("Foreach: parameter '%s' is not a list")

		# save original value
		uses      = cmd.attrib['name'].split(' ')
		originals = {}
		for use in uses:
			if use in params: originals[use] = params[use]
			else: originals[use] = None

		# run the cycle
		for it in params[cmd.attrib['list']]:
			if type(it) == tuple:
				i = 0
				for use in uses:
					try:
						params[use] = it[i]
					except IndexError:
						raise MyException("Foreach: not enough parameters to use")

					i += 1
			else:
				params[cmd.attrib['name']] = it

			self.do_commands(cmd, profile, params)

		# restore original
		for use in uses:
			if originals[use] == None and use in params:
				del params[use]
		else:
			params[use] = originals[use]

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

		silent = False
		if 'silent' in cmd.attrib and cmd.attrib['silent'].lower() in ('yes', 'true', '1'):
			silent = True

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

		if not silent:
			self.save_result("Parser:%s:%s" % (pname, iparams,), None, result, self.last_command_time, params)

		# if we want to store some parameters, do it
		store = cmd.find('store')
		if store != None:
			for sparam in store.findall('param'):
				for tmp in ('type', 'name'):
					if tmp not in sparam.attrib:
						raise MyException("Parser: store attribute '%s' missing" % (tmp,))

				simple = parser.simple_value(result, sparam.attrib['type'])
				params[sparam.attrib['name']] = simple

	def do_version(self, cmd, profile, params):
		for el in cmd:
			# <if> 
			if el.tag == 'if':
				# convert attributes into ranges <start, end> where None means infinite
				ranges = {}
				for x in ('major', 'minor', 'patch', 'build'):
					ranges[x] = (None, None) 
					
					try:
						if x in el.attrib:
							xv = el.attrib[x].split('-')
							if len(xv) == 1:
								if len(xv[0]) == 0: ranges[x] = (None, None)
								else: ranges[x] = (int(xv[0]), int(xv[0]))
	
							elif len(xv) == 2:
								if len(xv[0]) == 0: xfrom = None
								else: xfrom = int(xv[0])
	
								if len(xv[1]) == 0: xto = None
								else: xto = int(xv[1])
	
								ranges[x] = (xfrom, xto)
	
							else:
								raise MyException("Version: invalid range for '%s'" % (x,))

					except ValueError:
						raise MyException("Version: cannot process '%s'" % (x,))

				# check if it matches the running version
				running  = sshc.get_info()['version']
				matching = True

				for x in ('major', 'minor', 'patch', 'build'):
					start = ranges[x][0]
					end   = ranges[x][1]

					if (start != None) and (running[x] < start): matching = False
					if (end   != None) and (running[x] > end)  : matching = False

				# if matching, run the command and return
				if matching:
					self.do_commands(el, profile, params)
					return

			# <else> 
			# if we got here, we just run whatever is inside and return
			if el.tag == 'else':
				self.do_commands(el, profile, params)
				return

	def do_set(self, cmd, profile, params):
		for tmp in ('name',):
			if tmp not in cmd.attrib:
				raise MyException("Set: attribute '%s' missing" % (tmp,))

		params[cmd.attrib['name']] = self.element_get_command(cmd, profile, params)

	def do_unset(self, cmd, profile, params):
		for tmp in ('name',):
			if tmp not in cmd.attrib:
				raise MyException("Unset: attribute '%s' missing" % (tmp,))

		if cmd.attrib['name'] in params:
			del params[cmd.attrib['name']] 

	def do_merge(self, cmd, profile, params):
		for tmp in ('name',):
			if tmp not in cmd.attrib:
				raise MyException("Merge: attribute '%s' missing" % (tmp,))

		# we may only choose some positions to include
		pos = None
		if 'positions' in cmd.attrib:
			pos = []
			for p in cmd.attrib['positions'].split(' '):
				try:
					pos.append(int(p))
				except ValueError:
					raise MyException("Merge: param 'positions' must contain numbers")

		# convert to specific type?
		ctype = None
		if 'type' in cmd.attrib:
			if cmd.attrib['type'] == 'int':
				ctype = int
			elif cmd.attrib['type'] == 'str':
				ctype = str
			else:
				raise MyException("Merge: unknown type conversion '%s'" % (cmd.attrib['type'],))

		#
		merge = []
		for p in cmd.findall("param"):
			if 'name' not in p.attrib:
				raise MyException("Merge: param element has no 'name' attribute")

			if p.attrib['name'] in params:
				if pos == None:
					merge += params[p.attrib['name']]
				else:
					for var in params[p.attrib['name']]:
						to_merge = []
						for pi in pos:
							try:
								if ctype == None:
									to_merge.append( var[pi] )
								else:
									try:
										to_merge.append( ctype(var[pi]) )
									except ValueError:
										raise MyException("Merge: unable to convert '%s' to %s" % (var[pi], str(ctype),))

							except IndexError:
								print var
								raise MyException("Merge: no such position %i" % (pi,))

						if len(to_merge) == 1:
							merge += to_merge
						else:
							merge += (tuple(to_merge),)
			else:
				print >>sys.stderr, "Warning: unknown parameter '%s' in merge to '%s', ignoring" % (p.attrib['name'], cmd.attrib['name'],)

		params[cmd.attrib['name']] = merge

	def do_dump_params(self, cmd, profile, params):
		self.save_result("internal:dump_params", None, params, self.last_command_time, params)

	def do_echo(self, cmd, profile, params):
		v = ">>> %s" % (self.element_get_command(cmd, profile, params),)
		print prepend_timestamp(v, self.last_command_time, 'script')

	def save_result(self, command, vdom, output, etime, params):
		rp = {}
		for p in params.keys():
			if p[0] != '>': continue
			else: rp[p[1:]] = params[p]

		if self.output != None:
			tmp = {
				'command': command,
				'context': vdom,
				'output' : output,
				'time': str(etime),
				'parameters' : rp,
				'flags': {
					'time_format'   : etime.time_format,
					'time_source'   : etime.time_source,
					'filename'      : self.filename,
					'real_filename' : self.real_filename,
				},
			}

			if self.output_buffer_length == 0:
				self.output.write(json.dumps(tmp) + "\n")
				self.output.flush()

			else:
				self.output_buffer.append( json.dumps(tmp) )
				if len(self.output_buffer) >= self.output_buffer_length:
					self.save_result_compress()

		if not self.quiet:
			print prepend_timestamp("<<< %s" % (command,), etime, 'script')
			print prepend_timestamp(str(output), etime, 'script')
			
	# separate function to be able to call it also when the program is terminating
	def save_result_compress(self):	
		if self.output_buffer_length > 0 and len(self.output_buffer) > 0:
			o = bz2.compress("\n".join(self.output_buffer) + "\n")
			self.output.write(o)
			self.output.flush()
			self.output_buffer = []

if __name__ == '__main__':
	script = Script(sshc, args)
	try:
		cycle(script.do, {}, args.cycle_time, cycles_left=[args.max_cycles], debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

