from GenericModel import GenericModel, NICCounters, NICDrops

class Model(GenericModel):
	def init(self):
		self.gen_ports()
		self.np6 = [0, 1, 2]

	def gen_ports(self):
		hwnic_switch   = NICCounters(NICCounters.SRC_HWNIC,   "switch", NICCounters.SPD_IFACE)
		xestats0_0     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/XE0",  NICCounters.SPD_S10G)
		xestats0_1     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/XE1",  NICCounters.SPD_S10G)
		xestats0_2     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/XE2",  NICCounters.SPD_S10G)
		xestats0_3     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/XE3",  NICCounters.SPD_S10G)
		xestats1_0     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "1/XE0",  NICCounters.SPD_S10G)
		xestats1_1     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "1/XE1",  NICCounters.SPD_S10G)
		xestats1_2     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "1/XE2",  NICCounters.SPD_S10G)
		xestats1_3     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "1/XE3",  NICCounters.SPD_S10G)
		xestats2_0     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "2/XE0",  NICCounters.SPD_S10G)
		xestats2_1     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "2/XE1",  NICCounters.SPD_S10G)
		xestats2_2     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "2/XE2",  NICCounters.SPD_S10G)
		xestats2_3     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "2/XE3",  NICCounters.SPD_S10G)
		hwnic_kernel   = NICCounters(NICCounters.SRC_HWNIC,   "kernel", NICCounters.SPD_IFACE)

		np6drops0      = NICDrops(NICDrops.SRC_NP6_DROPS, 0)
		np6drops1      = NICDrops(NICDrops.SRC_NP6_DROPS, 1)
		np6drops2      = NICDrops(NICDrops.SRC_NP6_DROPS, 2)

		self.add_port("1-C1", hwnic_switch, xestats0_0, hwnic_kernel, np6drops0)
		self.add_port("1-C2", hwnic_switch, xestats0_1, hwnic_kernel, np6drops0)
		self.add_port("1-C3", hwnic_switch, xestats0_2, hwnic_kernel, np6drops1)
		self.add_port("1-C4", hwnic_switch, xestats0_3, hwnic_kernel, np6drops1)
		self.add_port("2-C1", hwnic_switch, xestats1_0, hwnic_kernel, np6drops2)
		self.add_port("2-C2", hwnic_switch, xestats1_1, hwnic_kernel, np6drops2)
		self.add_port("2-C3", hwnic_switch, xestats1_2, hwnic_kernel, np6drops2)
		self.add_port("2-C4", hwnic_switch, xestats1_3, hwnic_kernel, np6drops2)
