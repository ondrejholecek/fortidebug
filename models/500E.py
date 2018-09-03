from GenericModel import GenericModel, NICCounters, NICDrops

class Model(GenericModel):
	def init(self):
		self.gen_ports()
		self.np6 = [0]

	def gen_ports(self):
		hwnic_kernel   = NICCounters(NICCounters.SRC_HWNIC,   "kernel", NICCounters.SPD_IFACE)

		xestats0_0     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/XE0",  NICCounters.SPD_S10G)
		xestats0_2     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/XE2",  NICCounters.SPD_S10G)

		gestats0_0     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE0",   NICCounters.SPD_S10G)
		gestats0_1     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE1",   NICCounters.SPD_S10G)
		gestats0_2     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE2",   NICCounters.SPD_S10G)
		gestats0_3     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE3",   NICCounters.SPD_S10G)
		gestats0_4     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE4",   NICCounters.SPD_S10G)
		gestats0_5     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE5",   NICCounters.SPD_S10G)
		gestats0_6     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE6",   NICCounters.SPD_S10G)
		gestats0_7     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE7",   NICCounters.SPD_S10G)
		gestats0_8     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE8",   NICCounters.SPD_S10G)
		gestats0_9     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE9",   NICCounters.SPD_S10G)
		gestats0_10    = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE10",  NICCounters.SPD_S10G)
		gestats0_11    = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE11",  NICCounters.SPD_S10G)
		gestats0_12    = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE12",  NICCounters.SPD_S10G)
		gestats0_13    = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE13",  NICCounters.SPD_S10G)
		gestats0_14    = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE14",  NICCounters.SPD_S10G)
		gestats0_15    = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "0/GIGE15",  NICCounters.SPD_S10G)

		np6drops0      = NICDrops(NICDrops.SRC_NP6_DROPS, 0)

		self.add_port("port1",  gestats0_13, gestats0_13, hwnic_kernel, np6drops0)
		self.add_port("port2",  gestats0_12, gestats0_12, hwnic_kernel, np6drops0)
		self.add_port("port3",  gestats0_15, gestats0_15, hwnic_kernel, np6drops0)
		self.add_port("port4",  gestats0_14, gestats0_14, hwnic_kernel, np6drops0)
		self.add_port("port5",  gestats0_9,  gestats0_9,  hwnic_kernel, np6drops0)
		self.add_port("port6",  gestats0_8,  gestats0_8,  hwnic_kernel, np6drops0)
		self.add_port("port7",  gestats0_11, gestats0_11, hwnic_kernel, np6drops0)
		self.add_port("port8",  gestats0_10, gestats0_10, hwnic_kernel, np6drops0)
		self.add_port("port9",  gestats0_6,  gestats0_6,  hwnic_kernel, np6drops0)
		self.add_port("port10", gestats0_7,  gestats0_7,  hwnic_kernel, np6drops0)
		self.add_port("port11", gestats0_4,  gestats0_4,  hwnic_kernel, np6drops0)
		self.add_port("port12", gestats0_5,  gestats0_5,  hwnic_kernel, np6drops0)
		self.add_port("s1",     gestats0_2,  gestats0_2,  hwnic_kernel, np6drops0)
		self.add_port("s2",     gestats0_3,  gestats0_3,  hwnic_kernel, np6drops0)
		self.add_port("vw1",    gestats0_0,  gestats0_0,  hwnic_kernel, np6drops0)
		self.add_port("vw2",    gestats0_1,  gestats0_1,  hwnic_kernel, np6drops0)
		self.add_port("x1",     xestats0_0,  xestats0_0,  hwnic_kernel, np6drops0)
		self.add_port("x2",     xestats0_2,  xestats0_2,  hwnic_kernel, np6drops0)
		self.add_port("mgmt",  hwnic_kernel, None, hwnic_kernel, None)
		self.add_port("ha",  hwnic_kernel, None, hwnic_kernel, None)
