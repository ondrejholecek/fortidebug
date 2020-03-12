from EasyParser import EasyParser

import re
import time

class ParserNP6Links(EasyParser):
	def prepare(self):
		self.re_block = re.compile("^Counters\s+.*?\r\n\r", re.DOTALL | re.M)

	def get(self, npuid):
		# collect raw data
		stats1G  = self.sshc.clever_exec("fnsysctl cat /proc/net/np6_%i/gige-stats" % (npuid,))
		stats10G = self.sshc.clever_exec("fnsysctl cat /proc/net/np6_%i/xe-stats" % (npuid,))
		ctime    = time.time()
		data     = {}

		for stats in (stats1G, stats10G):
			for block in self.re_block.findall(stats):
				columns = None
				for line in block.split("\r\n"):
					s = line.split()
					if len(s) == 0: continue
					if s[0][0] == '-': continue
	
					if s[0] == "Counters":
						columns = [None,]
						for i in range(1, len(s)):
							cname = s[i]

							alias = s[i].split('|')[0]
							speed = 1000
							if alias == "XE0"  : 
								speed = 10000
								alias = "XAUI_0"
							elif alias == "XE1": 
								speed = 10000
								alias = "XAUI_1"
							elif alias == "XE2": 
								speed = 10000
								alias = "XAUI_2"
							elif alias == "XE3": 
								speed = 10000
								alias = "XAUI_3"

							if cname not in data: 
								data[cname] = {
									'alias': alias,
									'speed': speed,
									'raw': {},
								}
							columns.append(cname)
						continue
	
					name = s[0]
					for i in range(1, len(s)):
						data[columns[i]]['raw'][name] = int(s[i])

		# calculate counters
		for link in data.keys():
			data[link]['counters'] = {
				'rx_packets_all': data[link]['raw']['RX_UCAST'] + data[link]['raw']['RX_BCAST'] + data[link]['raw']['RX_MCAST'],
				'rx_bytes_all': data[link]['raw']['RX_OCTET'],
				'tx_packets_all': data[link]['raw']['TX_UCAST'] + data[link]['raw']['TX_BCAST'] + data[link]['raw']['TX_MCAST'],
				'tx_bytes_all': data[link]['raw']['TX_OCTET'],
			}
			data[link]['collected_on'] = ctime

		#
		return data

