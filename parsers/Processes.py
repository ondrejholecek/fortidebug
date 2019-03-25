from EasyParser import EasyParser

import re
import datetime

# fnsysctl ps
# ---
# PID       UID     GID     STATE   CMD
# 1         0       0       S       /bin/initXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# 2         0       0       S       [kthreadd]
# 3         0       0       S       [ksoftirqd/0]
# 6         0       0       S       [migration/0]
# 7         0       0       S       [watchdog/0]
# 8         0       0       S       [migration/1]
# 9         0       0       S       [kworker/1:0]
# 10        0       0       S       [ksoftirqd/1]
# 11        0       0       S       [kworker/0:1]
# 12        0       0       S       [watchdog/1]
# 13        0       0       S       [migration/2]
# 14        0       0       S       [kworker/2:0]
# 15        0       0       S       [ksoftirqd/2]
# 16        0       0       S       [watchdog/2]
# 17        0       0       S       [migration/3]
# 18        0       0       S       [kworker/3:0]
# 19        0       0       S       [ksoftirqd/3]
# 20        0       0       S       [watchdog/3]
# 21        0       0       S       [migration/4]
# 22        0       0       S       [kworker/4:0]
# 23        0       0       S       [ksoftirqd/4]
# 24        0       0       S       [watchdog/4]
# 25        0       0       S       [migration/5]

class ParserProcesses(EasyParser):
	def prepare(self):
		self.re_process = re.compile("^(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(.*?)\s*$", re.M)

	def get(self):
		ps = self.sshc.clever_exec("fnsysctl ps")
		processes = self.re_process.findall(ps)
		if len(processes) == 0:
			raise Exception("Cannot parse processes")
		
		result = []
		for process in processes:
			result.append( {
				'PID': int(process[0]),
				'UID': int(process[1]),
				'GID': int(process[2]),
				'state': process[3],
				'cmd': process[4],
			})

		return result

	def simple_value(self, result, name):
		return [e['PID'] for e in result]
		
