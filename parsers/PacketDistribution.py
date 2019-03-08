from EasyParser import EasyParser

import re
import time

# fgt-core-1 # diag firewall packet distribution
# getting packet distribution statistics...
# 0 bytes - 63 bytes: 133937665 packets
# 64 bytes - 127 bytes: 138188952 packets
# 128 bytes - 255 bytes: 126095679 packets
# 256 bytes - 383 bytes: 29800094 packets
# 384 bytes - 511 bytes: 181410438 packets
# 512 bytes - 767 bytes: 55133806 packets
# 768 bytes - 1023 bytes: 1841940 packets
# 1024 bytes - 1279 bytes: 185652002 packets
# 1280 bytes - 1500 bytes: 788393 packets
#  > 1500 bytes: 0 packets


class ParserPacketDistribution(EasyParser):
	def prepare(self):
		self.re_std_dist    = re.compile("^(\d+) bytes - (\d+) bytes: (\d+) packets", re.M)
		self.re_big_dist    = re.compile("^ > (\d+) bytes: (\d+) packets", re.M)

	def get(self):
		dists = self.sshc.clever_exec("diagnose firewall packet distribution", vdom='')
		collected_on = time.time()

		result = {}
		for dist in self.re_std_dist.findall(dists):
			left = int(dist[0])
			if left == 0: left = None
			right = int(dist[1])
			result[ (left, right) ] = int(dist[2])
		
		for dist in self.re_big_dist.findall(dists):
			left = int(dist[0])+1
			result[ (left, None) ] = int(dist[1])

		return {
			'collected_on': collected_on,
			'packets': result,
		}

