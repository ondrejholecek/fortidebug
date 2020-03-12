from EasyParser import EasyParser

import re
import time

class ParserNP6Drops(EasyParser):
	def prepare(self):
		# dce
		# APSTYPE_IPTI0   :0000000000000000 [e0]  APSTYPE_IPTI1   :0000000000000000 [e1]
		# ano
		# IPV6_OPTTUNNEL    :0000000000000000 [f0]        IPV6_OPTHOMEADDR  :0000000000000000 [f1]
		# hrx
		# VHIF_TX9_DROP     :0000000000000000     VHIF_TX10_DROP    :0000000000000000

		self.re_c     = re.compile("(\S+)\s*:(\S+)\s+", re.M)
		self.re_block = re.compile("(\S+):\s*\r\n(.*?)(?=\r\n\S+:\s*|$)", re.DOTALL)

	def get(self, npuid):
		# collect raw data
		drops_dce = self.sshc.clever_exec("diag npu np6 dce-all %i" % (npuid,))
		drops_ano = self.sshc.clever_exec("diag npu np6 anomaly-drop-all %i" % (npuid,))
		drops_hrx = self.sshc.clever_exec("diag npu np6 hrx-drop-all %i" % (npuid,))
		ctime    = time.time()
		data     = {
			'dce': { 'raw': {} },
			'ano': { 'raw': {} },
			'hrx': { 'raw': {} },
		}

		# parse
		for dtype, dcounter in ( ('dce', drops_dce), ('ano', drops_ano), ('hrx', drops_hrx) ):
			if dtype == 'ano':
				for bname, block in self.re_block.findall(dcounter):
					data[dtype]['raw'][bname] = self.parse_block(block)
			else:
				data[dtype]['raw']['global'] = self.parse_block(dcounter)
				
		# calculate summary
		for dtype in data.keys():
			summary = 0
			for l in data[dtype]['raw'].keys():
				for c in data[dtype]['raw'][l].keys():
					summary += data[dtype]['raw'][l][c]

			data[dtype]['summary'] = summary

		#
		data['collected_on'] = ctime
		return data
	
	def parse_block(self, block):
		r = {}
		for name, value in self.re_c.findall(block):
			r[name] = int(value)
		return r
