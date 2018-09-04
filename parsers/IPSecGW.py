from EasyParser import EasyParser

import re


## Note: sometimes a VPN exists in one output, gets missing in the next one and magically re-appers in the next one
##   this seems to be a problem on FortiOS
##   seen on: 3000D 5.6.5


# vd: root/0
# name: Priv_psuba
# version: 1
# interface: Internet 54
# addr: 193.86.26.196:500 -> 89.248.245.130:500
# virtual-interface-addr: 10.108.255.2 -> 0.0.0.0
# created: 1311050s ago
# auto-discovery: 0
# IKE SA: created 1/13  established 1/13  time 20/20/30 ms
# IPsec SA: created 1/24  established 1/24  time 0/15/20 ms
# 
#   id/spi: 444 8f649bf9844bde6c/2ed52dc642573ee8
#   direction: initiator
#   status: established 19550-19550s ago = 20ms
#   proposal: aes128-sha256
#   key: 342ffgdf34321237-fsdfkjl321edsaaa
#   lifetime/rekey: 86400/66549
#   DPD sent/recv: 00000221/000025fe
# 
# vd: root/0
# [...]

import datetime

class ParserIPSecGW(EasyParser):
	def prepare(self):
		self.re_sections = re.compile('\r\nvd: ', re.DOTALL)
		self.re_main = re.compile('^vd:\s+(.*?)/.*?^name:\s+(.*?)\r\n.*?^version:\s+(.*?)\r\n.*?^interface:\s+(.*?)\s.*?^addr:\s+(.*?):(\d+)\s+->\s+(.*?):(\d+).*?^created:\s+(\d+)s ago.*?^IKE SA:\s+created\s+(\d+)/(\d+)\s+(?:established\s+(\d+)/(\d+)\s+){0,1}.*?^IPsec SA:\s+created\s+(\d+)/(\d+)\s+(?:established\s+(\d+)/(\d+)\s+){0,1}', re.DOTALL | re.M)
		self.re_isakmp = re.compile('\r\n\r\n^\s+id/spi:\s+\d+\s+(.*?)/(.*?)\r.*?^\s+direction:\s+(.*?)\r.*?^\s+status:\s+(.*?)[^a-zA-Z]', re.DOTALL | re.M)

	def get(self):
		gwlist = self.sshc.clever_exec("diag vpn ike gateway list", "root")

#		#
#		# DEBUG
#		f = open("/tmp/debug/%s" % (datetime.datetime.now(),), "w")
#		f.write(gwlist)
#		f.close()
#		#

		tunnels = []
		for section in self.re_sections.split(gwlist):
			if len(section) == 0: continue
			section = "vd: " + section

			# ('root', 'Priv_psuba', '1', 'Internet', '193.86.26.196', '500', '89.248.245.130', '500', '1314402', '1', '13', '1', '13', '1', '24', '1', '24')
			# ('8f079bf8715bde6c', '2ed52dc066893ee8', 'initiator', 'established')
			g = self.re_main.search(section)
			if not g:
				print "Debug: unable to parse main section"
				continue

			t = {}
			t['vdom'] = g.group(1)
			t['name'] = g.group(2)
			t['version'] = int(g.group(3))
			t['interface'] = g.group(4)
			t['source_ip'] = g.group(5)
			t['source_port'] = int(g.group(6))
			t['destination_ip'] = g.group(7)
			t['destination_port'] = int(g.group(8))
			t['created_ago'] = int(g.group(9))

			t['IKE_SA_created_current']       = 0
			t['IKE_SA_created_all']           = 0
			t['IKE_SA_established_current']   = 0
			t['IKE_SA_established_all']       = 0

			t['IPSEC_SA_created_current']     = 0
			t['IPSEC_SA_created_all']         = 0
			t['IPSEC_SA_established_current'] = 0
			t['IPSEC_SA_established_all']     = 0

			if g.group(10) != None: t['IKE_SA_created_current']       = int(g.group(10))
			if g.group(11) != None: t['IKE_SA_created_all']           = int(g.group(11))
			if g.group(12) != None: t['IKE_SA_established_current']   = int(g.group(12))
			if g.group(13) != None: t['IKE_SA_established_all']       = int(g.group(13))

			if g.group(14) != None: t['IPSEC_SA_created_current']     = int(g.group(14))
			if g.group(15) != None: t['IPSEC_SA_created_all']         = int(g.group(15))
			if g.group(16) != None: t['IPSEC_SA_established_current'] = int(g.group(16))
			if g.group(17) != None: t['IPSEC_SA_established_all']     = int(g.group(17))

			g = self.re_isakmp.search(section)
			if g:
				t['cookie_local']   = g.group(1)
				t['cookie_remote']  = g.group(2)
				t['direction']      = g.group(3)
				t['status']         = g.group(4)
			else:
				print "Debug: unable to parse details section"
				t['cookie_local']   = None
				t['cookie_remote']  = None
				t['direction']      = None
				t['status']         = None

			tunnels.append(t)

		return tunnels
