from EasyParser import EasyParser

import re

class ParserNP6IfaceMapping(EasyParser):
	def prepare(self):
		self.re_l = re.compile("^(?:np6_(\d+))?\s+(\d+)\s+(\S+)\s+(\d+)G\s+(\S+)\s*$")

	def get(self):
		links   = {}
		last_np = None

		plist = self.sshc.clever_exec("diag npu np6 port-list")
		for line in plist.split("\n"):
			g = self.re_l.search(line)
			if not g: continue

			if g.group(1) == None:
				current_np = last_np
			else:
				current_np = int(g.group(1))
				last_np    = current_np

			xaui  = int(g.group(2))
			iface = g.group(3)
			speed = int(g.group(4))
			xchip = g.group(5).lower() == 'yes'

			if current_np not in links: links[current_np] = {}
			if xaui not in links[current_np]: links[current_np][xaui] = []
			links[current_np][xaui].append({
				'interface': iface,
				'speed'    : speed,
				'xchip'    : xchip,
			})

		return links

	def simple_value(self, result, name):
		if name == "np6_ids":
			return result.keys()
