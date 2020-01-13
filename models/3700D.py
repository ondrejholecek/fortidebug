from GenericModel import GenericModel, NICCounters, NICDrops

### 
### WARNING: does not take 40G ports into account!!!!
###

class Model(GenericModel):
	def init(self):
		self.gen_ports()
		self.np6 = [0, 1, 2, 3]

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
		xestats3_0     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "3/XE0",  NICCounters.SPD_S10G)
		xestats3_1     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "3/XE1",  NICCounters.SPD_S10G)
		xestats3_2     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "3/XE2",  NICCounters.SPD_S10G)
		xestats3_3     = NICCounters(NICCounters.SRC_NP6_PORTSTATS, "3/XE3",  NICCounters.SPD_S10G)
		hwnic_kernel   = NICCounters(NICCounters.SRC_HWNIC,   "kernel", NICCounters.SPD_IFACE)

		np6drops0      = NICDrops(NICDrops.SRC_NP6_DROPS, 0)
		np6drops1      = NICDrops(NICDrops.SRC_NP6_DROPS, 1)
		np6drops2      = NICDrops(NICDrops.SRC_NP6_DROPS, 2)
		np6drops3      = NICDrops(NICDrops.SRC_NP6_DROPS, 3)

		# NPU 0
		self.add_port("port27", hwnic_switch, xestats0_0, hwnic_kernel, np6drops0)
		self.add_port("port25", hwnic_switch, xestats0_1, hwnic_kernel, np6drops0)
		self.add_port("port28", hwnic_switch, xestats0_2, hwnic_kernel, np6drops0)
		self.add_port("port27", hwnic_switch, xestats0_3, hwnic_kernel, np6drops0)

		# NPU 1
		self.add_port("port30", hwnic_switch, xestats1_0, hwnic_kernel, np6drops1)
		self.add_port("port29", hwnic_switch, xestats1_1, hwnic_kernel, np6drops1)
		self.add_port("port32", hwnic_switch, xestats1_2, hwnic_kernel, np6drops1)
		self.add_port("port31", hwnic_switch, xestats1_3, hwnic_kernel, np6drops1)

		# NPU 2
		self.add_port("port5",  hwnic_switch, xestats2_0, hwnic_kernel, np6drops2)
		self.add_port("port9",  hwnic_switch, xestats2_0, hwnic_kernel, np6drops2)
		self.add_port("port13", hwnic_switch, xestats2_0, hwnic_kernel, np6drops2)

		self.add_port("port6",  hwnic_switch, xestats2_1, hwnic_kernel, np6drops2)
		self.add_port("port10", hwnic_switch, xestats2_1, hwnic_kernel, np6drops2)
		self.add_port("port14", hwnic_switch, xestats2_1, hwnic_kernel, np6drops2)

		self.add_port("port7",  hwnic_switch, xestats2_2, hwnic_kernel, np6drops2)
		self.add_port("port11", hwnic_switch, xestats2_2, hwnic_kernel, np6drops2)

		self.add_port("port8",  hwnic_switch, xestats2_3, hwnic_kernel, np6drops2)
		self.add_port("port12", hwnic_switch, xestats2_3, hwnic_kernel, np6drops2)

		# NPU 3
		self.add_port("port15", hwnic_switch, xestats3_0, hwnic_kernel, np6drops3)
		self.add_port("port19", hwnic_switch, xestats3_0, hwnic_kernel, np6drops3)
		self.add_port("port23", hwnic_switch, xestats3_0, hwnic_kernel, np6drops3)

		self.add_port("port16", hwnic_switch, xestats3_1, hwnic_kernel, np6drops3)
		self.add_port("port20", hwnic_switch, xestats3_1, hwnic_kernel, np6drops3)
		self.add_port("port24", hwnic_switch, xestats3_1, hwnic_kernel, np6drops3)

		self.add_port("port17", hwnic_switch, xestats3_2, hwnic_kernel, np6drops3)
		self.add_port("port21", hwnic_switch, xestats3_2, hwnic_kernel, np6drops3)

		self.add_port("port18", hwnic_switch, xestats3_3, hwnic_kernel, np6drops3)
		self.add_port("port22", hwnic_switch, xestats3_3, hwnic_kernel, np6drops3)


		# others
		self.add_port("mgmt1",  hwnic_kernel, None, hwnic_kernel, None)
		self.add_port("mgmt2",  hwnic_kernel, None, hwnic_kernel, None)
		self.add_port("npu0_vlink0", None, None, hwnic_kernel, np6drops0)
		self.add_port("npu0_vlink1", None, None, hwnic_kernel, np6drops0)
		self.add_port("npu1_vlink0", None, None, hwnic_kernel, np6drops1)
		self.add_port("npu1_vlink1", None, None, hwnic_kernel, np6drops1)
		self.add_port("npu2_vlink0", None, None, hwnic_kernel, np6drops2)
		self.add_port("npu2_vlink1", None, None, hwnic_kernel, np6drops2)
		self.add_port("npu3_vlink0", None, None, hwnic_kernel, np6drops3)
		self.add_port("npu3_vlink1", None, None, hwnic_kernel, np6drops3)
