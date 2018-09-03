from EasyParser import EasyParser

import re

class ParserSystemInterfaceList(EasyParser):
	def prepare(self):
		self.re_nl = re.compile("\r\n\r\n")
		self.re_kv = re.compile("(\S+)=(.+?)\s*(?=\S+=|$)", re.DOTALL | re.M)

	def get(self, types=None):
		ifaces = {}

		ilist = self.sshc.clever_exec("diag netlink interface list", "")
		for iface in self.re_nl.split(ilist):
			# [('if', 'port25'), ('family', '00'), ('type', '1'), ('index', '39'), ('mtu', '1500'), ('link', '0'), ('master', '0'), ('ref', '23'), ('state', 'off start'), ('fw_flags', '0'), ('flags', 'up broadcast run allmulti multicast')]
			tmp = {}
			for key, value in self.re_kv.findall(iface):
				tmp[key] = value

			if types != None and int(tmp['type']) not in types: continue

			ifaces[tmp['if']] = {
				'type'   : int(tmp['type']),
				'index'  : int(tmp['index']),
				'mtu'    : int(tmp['mtu']),
				'state'  : tmp['state'].split(' '),
				'flags'  : tmp['flags'].split(' '),
			}
		
		return ifaces
