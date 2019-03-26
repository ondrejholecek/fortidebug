from EasyParser import EasyParser

import re

class ParserSystemInterfaceList(EasyParser):
	def prepare(self):
		self.re_nl = re.compile("\r\n\r\n")
		self.re_kv = re.compile("(\S+)=(.+?)\s*(?=\S+=|$)", re.DOTALL | re.M)

	def get(self, types=None, only_up=False):
		ifaces = {}

		ilist = self.sshc.clever_exec("diag netlink interface list", "")
		for iface in self.re_nl.split(ilist):
			# [('if', 'port25'), ('family', '00'), ('type', '1'), ('index', '39'), ('mtu', '1500'), ('link', '0'), ('master', '0'), ('ref', '23'), ('state', 'off start'), ('fw_flags', '0'), ('flags', 'up broadcast run allmulti multicast')]
			tmp = {}
			for key, value in self.re_kv.findall(iface):
				tmp[key] = value

			if types != None and int(tmp['type']) not in types: continue
			if only_up == True and 'run' not in tmp['flags'].split(' '): continue

			try:
				ifaces[tmp['if']] = {
					'type'   : int(tmp['type']),
					'index'  : int(tmp['index']),
					'mtu'    : int(tmp['mtu']),
					'state'  : tmp['state'].split(' '),
					'flags'  : tmp['flags'].split(' '),
				}
			except: continue
		
		return ifaces

	def simple_value(self, result, name):
		if name == 'nic_names_external':
			to_delete = ('ssl.root', 'root', 'vsys_ha', 'vsys_fgfm')
			r = []
			for tmp in result.keys():
				if tmp in to_delete: continue
				r.append(tmp)
			return r
	
