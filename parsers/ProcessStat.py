from EasyParser import EasyParser

import re

# fnsysctl cat /proc/$PID/stat
# ---
# 2 (kthreadd) S 0 0 0 0 -1 2149613632 0 0 0 0 0 0 0 0 20 0 1 0 1 0 0 18446744073709551615 0 0 0 0 0 0 0 2147483647 0 18446744071564646232 0 0 0 10 0 0 0 0 0

class ParserProcessStat(EasyParser):
	def prepare(self):
		self.re_first_part = re.compile("^(\d+)\s+\((.*?)\)\s+(.*)$", re.M)

	def get(self, pids):
		if type(pids) == int: pids = [pids]

		files = ""
		for pid in pids:
			files += " /proc/%i/stat" % (pid,)

		results = []

		pss = self.sshc.clever_exec("fnsysctl cat %s" % (files,))
		for ps in pss.split("\n"):
			ps = ps.strip()
			if len(ps) == 0: continue
			g = self.re_first_part.search(ps)
			if not g:
				print "Debug: cannot parse '%s'" % (ps,)
				continue

			others = g.group(3).split()

			results.append( {
				'PID': int(g.group(1)),
				'name': g.group(2),
				'current_CPU': int(others[36]),
				'state': others[0],
			} )

		return results
