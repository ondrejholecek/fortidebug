from EasyParser import EasyParser

import re
import datetime
import time

class ParserNIC2(EasyParser):
	def prepare(self):
		self.re_colon = re.compile("^\s*([^:\r\n]+?)\s*:(.*?)\s*$", re.M)
		self.re_space = re.compile("^\s*([^\s\r\n]+?)\s+(.*?)\s*$", re.M)

	def get(self, iface):
		out = self.sshc.clever_exec("diagnose hardware deviceinfo nic %s" % (iface,))
		if 'FortiASIC NP6 Adapter' in out:
			(generic, counters, raw) = self.parse_np6(iface, out)
		elif 'Broadcom 570x Tigon3 Ethernet Adapter' in out:
			(generic, counters, raw) = self.parse_tg3(iface, out)
		elif 'Intel(R) Gigabit Ethernet Network Driver' in out:
			(generic, counters, raw) = self.parse_igb(iface, out)
		else:
			return None

		return {
			'iface'   : iface,
			'type'    : generic['type'],
			'linkup'  : generic['linkup'],
			'speed'   : generic['speed'],
			'duplex'  : generic['duplex'],
			'counters': counters,
			'raw'     : raw,
			'collected_on': time.time(),
		}
	
	def parse_np6(self, iface, out):
		raw      = {}
		generic  = {}
		counters = {}

		for (k, v) in self.re_colon.findall(out):
			if k.startswith('Current_HWaddr'):
				v = "%s:%s" % (k[-2:], v)
				k = "Current_HWaddr"
				v = v.lower()
			elif k.startswith('Permanent_HWaddr'):
				v = "%s:%s" % (k[-2:], v)
				k = "Permanent_HWaddr"
				v = v.lower()

			raw[k] = v

		generic['linkup'] = raw['netdev status'] == 'up'

		if re.search("^npu\d+_vlink\d+$", iface):
			generic['type']   = 'np6vlink'
			generic['speed']  = 10000
			generic['duplex'] = 'full'

		else:
			generic['type'] = 'np6'
			if generic['linkup']:
				generic['speed']  = int(raw['Speed'])
				generic['duplex'] = raw['Duplex'].lower()
			else:
				generic['speed']  = 0
				generic['duplex'] = "none"

		try:
			counters['switch'] = {
				'rx_packets_all': int(raw['sw_rx_pkts']),
				'tx_packets_all': int(raw['sw_tx_pkts']),
				'rx_bytes_all'  : int(raw['sw_rx_bytes']),
				'tx_bytes_all'  : int(raw['sw_tx_bytes']),
			}
		except:
			counters['switch'] = None

		try:
			counters['np'] = {
				'rx_packets_all': int(raw['sw_np_rx_pkts']),
				'tx_packets_all': int(raw['sw_np_tx_pkts']),
				'rx_bytes_all'  : int(raw['sw_np_rx_bytes']),
				'tx_bytes_all'  : int(raw['sw_np_tx_bytes']),
			}
		except:
			counters['np'] = None

		try:
			counters['kernel'] = {
				'rx_packets_all': int(raw['Host Rx Pkts']),
				'tx_packets_all': int(raw['Host Tx Pkts']),
				'rx_bytes_all'  : int(raw['Host Rx Bytes']),
				'tx_bytes_all'  : int(raw['Host Tx Bytes']),
			}
		except:
			counters['kernel'] = None

		return (generic, counters, raw)


	def parse_tg3(self, iface, out):
		raw      = {}
		generic  = {}
		counters = {}

		for (k, v) in self.re_space.findall(out):
			raw[k] = v

		generic['type']   = 'tg3'
		generic['linkup'] = raw['Link'] == 'up'

		if generic['linkup']:
			generic['speed']  = int(raw['Speed'].split()[0])
			generic['duplex'] = raw['Duplex'].lower()
		else:
			generic['speed']  = 0
			generic['duplex'] = "none"

		try:
			counters['kernel'] = {
				'rx_packets_all': int(raw['Rx_Packets']),
				'tx_packets_all': int(raw['Tx_Packets']),
				'rx_bytes_all'  : int(raw['Rx_Bytes']),
				'tx_bytes_all'  : int(raw['Tx_Bytes']),
			}
		except:
			counters['kernel'] = None


		return (generic, counters, raw)

	def parse_igb(self, iface, out):
		raw      = {}
		generic  = {}
		counters = {}

		for (k, v) in self.re_space.findall(out):
			raw[k] = v

		generic['type']   = 'igb'
		generic['linkup'] = raw['Link'] == 'up'

		if generic['linkup']:
			generic['speed']  = int(raw['Speed'])
			generic['duplex'] = raw['Duplex'].lower()
		else:
			generic['speed']  = 0
			generic['duplex'] = "none"

		try:
			counters['kernel'] = {
				'rx_packets_all': int(raw['Rx_Packets']),
				'tx_packets_all': int(raw['Tx_Packets']),
				'rx_bytes_all'  : int(raw['Rx_Bytes']),
				'tx_bytes_all'  : int(raw['Tx_Bytes']),
			}
		except:
			counters['kernel'] = None


		return (generic, counters, raw)
