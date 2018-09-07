from EasyParser import EasyParser

import re

# pid = 243, engine count =  11
# 0 - pid:275:275 cfg:1 master:0 run:1
# 1 - pid:3284:3284 cfg:0 master:1 run:1
# 2 - pid:3285:3285 cfg:0 master:0 run:1
# 3 - pid:3286:3286 cfg:0 master:0 run:1
# 4 - pid:3287:3287 cfg:0 master:0 run:1
# 5 - pid:3288:3288 cfg:0 master:0 run:1
# 6 - pid:3289:3289 cfg:0 master:0 run:1
# 7 - pid:3290:3290 cfg:0 master:0 run:1
# 8 - pid:3291:3291 cfg:0 master:0 run:1
# 9 - pid:3292:3292 cfg:0 master:0 run:1
# 10 - pid:3293:3293 cfg:0 master:0 run:1
# 
# pid:         3284 index:1 master
# version:     05006000FLEN02300-00003.00532-1807252049
# up time:     0 days 3 hours 25 minutes
# init time:   0 seconds
# socket size: 128(MB)
# database:    extended
# bypass:      disable
# pid:         3285 index:2
# version:     05006000FLEN02300-00003.00532-1807252049
# up time:     0 days 3 hours 25 minutes
# init time:   0 seconds
# socket size: 128(MB)
# database:    extended
# bypass:      disable
# [...]

class ParserIPSSummary(EasyParser):
	def prepare(self):
		self.re_ips = re.compile("^(\d+)\s*-\s*pid:(\d+):(\d+)\s+cfg:(\d+)\s+master:(\d+)\s+run:(\d+)", re.M)

	def get(self):
 		stat = self.sshc.clever_exec("diagnose test application ipsmonitor 1")
		parts = self.re_ips.findall(stat)
		if len(parts) == 0:
			raise Exception("Cannot parse ips status")

		engines = []
		for part in parts:
			engines.append({
				'pid'    : part[1],
				'cfg'    : int(part[3]) == 1,
				'master' : int(part[4]) == 1,
				'run'    : int(part[5]) == 1,
			})

		return engines

	def simple_value(self, result, name):
		if name == 'ipse_pids_all':
			return [e['pid'] for e in result]

		else:
			raise Exception("Unknown simple value name")
