from EasyParser import EasyParser

import re

class ParserHWInterfaceList(EasyParser):
	def prepare(self):
		self.re_l = re.compile("^\s+(\S+)\s*$", re.M)

	def get(self):
		ifaces = {}

		nics = self.sshc.clever_exec("diag hardware deviceinfo nic")
		return self.re_l.findall(nics)

