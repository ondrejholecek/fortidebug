from EasyParser import EasyParser

import re

# [...]
# ipsengine     4590      S <     0.0     0.5
# pyfcgid      241      S       0.0     0.2
# miglogd      237      S       0.0     0.2
# [...]

class ParserDiagSysTop(EasyParser):
	def prepare(self):
		self.re_top = re.compile("^\s*(\S+)\s+(\d+)\s+(\S)\s+(?:([<>])\s+)?([\d.]+)\s+([\d.]+)", re.M)

	def get(self, interval, filterx, filter_type):
		# get parsed output with all processes
		self.cycles_left = 2
		self.results     = []
		self.sshc.continuous_exec("diagnose sys top %i 99" % (interval,), self.divide, self.result, self.exit, {'cache':{}})
		results = self.results[-1]

		# filter just what we want
		if filter_type == "all":
			return results

		elif filter_type == "pid":
			ret = []
			for r in results:
				if r['pid'] in filterx:
					ret.append(r)
			return ret

		elif filter_type == "name":
			ret = []
			for r in results:
				if r['name'] in filterx:
					ret.append(r)
			return ret

		return None

	def divide(self, data, cache):
		data = data.replace("\x1b[H\x1b[J", '')
		sep  = "Run Time:"

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

	def result(self, data, cache):
		parts = self.re_top.findall(data)
		if len(parts) == 0:
			raise Exception("Cannot parse diag sys top")

		out = []
		for part in parts:
			out.append({
				'name'   : part[0],
				'pid'    : int(part[1]),
				'state'  : part[2],
				'nice'   : part[3],
				'cpu'    : float(part[4]),
				'mem'    : float(part[5]),
			})

		self.results.append(out)
		self.cycles_left -= 1

	def exit(self, cache):
		if self.cycles_left == 0: return "q"
		else: return None

