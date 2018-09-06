from EasyParser import EasyParser

import re
import datetime
import time

# SYSTEM:
# memory capacity            1149M
# memory used                192M
# packet memory used         0B
# recent pps\bps             29442\28797K
# session in-use             1991
# TCP:  in-use\active\total  1991\1991\3088006
# UDP:  in-use\active\total  0\0\0
# ICMP: in-use\active\total  0\0\0
# IP:   in-use\active\total  0\0\0
# TCP reassemble:   0
# TCP ooo:   0
# 
# Packet memory usage:

class ParserIPSSessionsStat(EasyParser):
	def prepare(self):
		self.re_process = re.compile(
			"SYSTEM:.*?" + 
			"\r\nmemory capacity\s+(\d+)(\S?).*?" +
			"\r\nmemory used\s+(\d+)(\S?).*?" +
			"\r\npacket memory used\s+(\d+)(\S?).*?" +
			"\r\nrecent\s+pps\\\\bps\s+(\d+)\\\\(\d+)(\S?).*?" +
			"\r\nsession\s+in-use\s+(\d+).*?" +
			"\r\nTCP:\s+in-use\\\\active\\\\total\s+(\d+)\\\\(\d+)\\\\(\d+).*?" +
			"\r\nUDP:\s+in-use\\\\active\\\\total\s+(\d+)\\\\(\d+)\\\\(\d+).*?" +
			"\r\nICMP:\s+in-use\\\\active\\\\total\s+(\d+)\\\\(\d+)\\\\(\d+).*?" +
			"\r\nIP:\s+in-use\\\\active\\\\total\s+(\d+)\\\\(\d+)\\\\(\d+).*?" +
			"\r\nTCP reassemble:\s+(\d+).*?" +
			"\r\nTCP ooo:\s+(\d+).*?" +
			"", re.DOTALL)

	def multiplier(self, number, units):
		m = 1024
		u = units.upper()

		if u == 'B' or u == '':
			return number
		elif u == 'K':
			return number*m
		elif u == 'M':
			return number*m*m
		elif u == 'G':
			return number*m*m*m
		else:
			return None

	def get(self):
		ipss = self.sshc.clever_exec("diagnose ips session status")
		parts = self.re_process.findall(ipss)
		if len(parts) == 0:
			raise Exception("Cannot parse processes")

		results = {}
		index   = 0

		for part in parts:
			index += 1
			results[index] = {
				'collected_on': time.time(),
				'memory': {
					'capacity'    : self.multiplier(int(part[0]), part[1]),
					'used'        : self.multiplier(int(part[2]), part[3]),
					'packet used' : self.multiplier(int(part[4]), part[5]),
				},
				'pps': int(part[6]),
				'bps': self.multiplier(int(part[7]), part[8]),
				'sessions': {
					'total' : {
						'inuse'   : int(part[9]),
					},
					'tcp'   : {
						'inuse'   : int(part[10]),
						'active'  : int(part[11]),
						'total'   : int(part[12]),
					},
					'udp'   : {
						'inuse'   : int(part[13]),
						'active'  : int(part[14]),
						'total'   : int(part[15]),
					},
					'icmp'   : {
						'inuse'   : int(part[16]),
						'active'  : int(part[17]),
						'total'   : int(part[18]),
					},
					'ip'   : {
						'inuse'   : int(part[19]),
						'active'  : int(part[20]),
						'total'   : int(part[21]),
					},
					'calculated_total': {
						'inuse'   : int(part[10]) + int(part[13]) + int(part[16]) + int(part[19]),
						'active'  : int(part[11]) + int(part[14]) + int(part[17]) + int(part[20]),
						'total'   : int(part[12]) + int(part[15]) + int(part[18]) + int(part[21]),
					},
				},
				'tcp reassemble' : int(part[22]),
				'tcp ooo'        : int(part[23]),
			}

		return results
