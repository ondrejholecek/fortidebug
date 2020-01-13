from EasyParser import EasyParser

import re
import time

# 05:00.0 Class 1000: Device 1a29:4338
# 	Subsystem: Device 0829:4338
# 	Flags: bus master, fast devsel, latency 0, IRQ 32
# 	Memory at ef300000 (32-bit, non-prefetchable) [size=32K]
# 	Memory at ef308000 (32-bit, non-prefetchable) [size=8K]
# 	Capabilities: [50] MSI: Enable- Count=1/16 Maskable- 64bit+
# 	Capabilities: [68] MSI-X: Enable+ Count=16 Masked-
# 	Capabilities: [78] Power Management version 3
# 	Capabilities: [80] Express Endpoint, MSI 00
# 	Kernel driver in use: cp8

class ParserPCI(EasyParser):
	def prepare(self):
		self.re_blk = re.compile("\r\n\r\n")
		self.re_dev_id = re.compile("^(\S+):(\S+)\.(\S+)\s+.*?\s+Device (\S+):(\S+)", re.M)
		self.re_driver = re.compile("Kernel driver in use:\s+(.*)$", re.M)

	def get(self):
		pci = self.sshc.clever_exec("diagnose hardware lspci -v")

		results = []
		for item in self.re_blk.split(pci):
			if len(item.strip()) == 0: continue
			g = self.re_dev_id.search(item)
			if g == None: continue

			res = {
				'pci_bus'      : int(g.group(1), 16),
				'pci_dev'      : int(g.group(2), 16),
				'pci_fce'      : int(g.group(3), 16),
				'card_vendor'  : int(g.group(4), 16),
				'card_product' : int(g.group(5), 16),
			}


			g = self.re_driver.search(item)
			if g != None:
				res['driver'] = g.group(1)

			results.append(res)

		return results
	
	def simple_value(self, result, name):
		if name == "cp8_ids":
			cp8 = []
			for x in result:
				if (x['card_vendor'] == 0x1a29) and (x['card_product'] == 0x4338): 
					cp8.append(x)
			return range(len(cp8))

		elif name == "np6_ids":
			np6 = []
			for x in result:
				if (x['card_vendor'] == 0x1a29) and (x['card_product'] == 0x4e36): 
					np6.append(x)
			return range(len(np6)/2)
