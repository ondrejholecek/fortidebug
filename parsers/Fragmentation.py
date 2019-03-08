from EasyParser import EasyParser

import re
import time

# fgt-core-1 # diag snmp ip frags
# ReasmTimeout = 509494
# ReasmReqds   = 13891819952
# ReasmOKs     = 4987244982
# ReasmFails   = 510061
# FragOKs      = 4739194407
# FragFails    = 184
# FragCreates  = 13305160044

class ParserFragmentation(EasyParser):
	def prepare(self):
		self.re_frag = re.compile("^(.*?)\s*=\s*(\d*)", re.M)

	def get(self):
		frags = self.sshc.clever_exec("diagnose snmp ip frags", vdom='')
		collected_on = time.time()

		result = {}
		for fr in self.re_frag.findall(frags):
			result[fr[0]] = int(fr[1])

		return {
			'collected_on': collected_on,
			'frags' : result,
		}

