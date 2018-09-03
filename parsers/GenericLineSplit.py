from EasyParser import EasyParser

import re

## be careful: some lines can be skipped if using the advanced parameters

class ParserGenericLineSplit(EasyParser):
	def get(self, split, command, vdom=None, key_index=0, value_index=None, value_type=None):
		
		split_re = re.compile(split)
		results = {}

		out = self.sshc.clever_exec(command, vdom)
		for line in out.split("\n"):
			line = line.strip("\r")
			if len(line) == 0: continue

			g = split_re.split(line)
			if not g: continue
			if len(g) < key_index:
				#print "Debug: resulting line has not enough fields to satisfy key index %i" % (key_index,)
				continue
			if value_index != None and len(g) < value_index:
				#print "Debug: resulting line has not enough fields to satisfy value index %i" % (value_index,)
				continue

			if value_index == None:
				results[ g[key_index] ] = g
			else:
				if value_type == None:
					results[ g[key_index] ] = g[value_index]
				else:
					try:
						results[ g[key_index] ] = value_type(g[value_index])
					except ValueError:
						#print "Debug: unable to convert value '%s' to the desired type" % (g[value_index],)
						continue
					
		return results
