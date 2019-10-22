from EasyParser import EasyParser

import re
import time


# FG1K2D-2 # diag hardware sysinfo interrupts
#             CPU0       CPU1       CPU2       CPU3       CPU4       CPU5       CPU6       CPU7
#    0:         36          0          0          0          0          0          0          0   IO-APIC-edge      timer
#    2:          0          0          0          0          0          0          0          0    XT-PIC-XT-PIC    cascade
#    3:          0    3577171          0          0          0          0          0          0   IO-APIC-edge      serial
#    4:          0       4688          0          0          0          0          0          0   IO-APIC-edge      serial
#    8:          0          0          0          0          0          0          0          0   IO-APIC-edge      rtc
#   16:          0    1832355          0          0          0          0          0          0   IO-APIC-fasteoi   ehci_hcd:usb1, ehci_hcd:usb2, uhci_hcd:usb5, uhci_hcd:usb9, linux-kernel-bde, mgmt1
#   17:          0          0          3          0          0          0          0          0   IO-APIC-fasteoi   uhci_hcd:usb3, uhci_hcd:usb6, mgmt2
#   18:          0          0          0          0          0          0          0          0   IO-APIC-fasteoi   uhci_hcd:usb4, uhci_hcd:usb7
#   19:          0          0          0          0          0          0          0          0   IO-APIC-fasteoi   uhci_hcd:usb8, net2280
#   64:          1          0          0     260298          0          0          0          0   PCI-MSI-edge      ahci
#   65:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_0_vpn0
#   66:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_0_vpn1
#   67:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_0_vpn2
#   68:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_0_vpn3
#   69:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_0_kxp
#   70:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_1_vpn0
#   71:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_1_vpn1
#   72:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_1_vpn2
#   73:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_1_vpn3
#   74:          0          0          0          0          0          0          0          0   PCI-MSI-edge      cp8_1_kxp
#   75:          5          1          0          0          0          0          0          0   PCI-MSI-edge      np6_0-tx-rx0
#   76:          0          1          5          0          0          0          0          0   PCI-MSI-edge      np6_0-tx-rx1
#   77:          0          0          1          0          5          0          0          0   PCI-MSI-edge      np6_0-tx-rx2
#   78:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_0-err0
#   79:          0          0         17          0          0          0          0          0   PCI-MSI-edge      np6_0-nturbo-tx-rx0
#   80:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_0-nturbo-err0
#   81:   16418964          0          0          1          0          0          0          0   PCI-MSI-edge      np6_0-nturbo-ips-0
#   82:          0   16141636          0          1          0          0          0          0   PCI-MSI-edge      np6_0-nturbo-ips-1
#   83:          0          0          0   14991882          0          0          0          0   PCI-MSI-edge      np6_0-nturbo-ips-2
#   84:          0          0          0          1   15879562          0          0          0   PCI-MSI-edge      np6_0-nturbo-ips-3
#   85:          0          0          0          0          1   16707050          0          0   PCI-MSI-edge      np6_0-nturbo-ips-4
#   86:          0          0          0          0          1          0   16444822          0   PCI-MSI-edge      np6_0-nturbo-ips-5
#   87:          0          0          0          0          1          0          0   16581448   PCI-MSI-edge      np6_0-nturbo-ips-6
#   88:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_0-nturbo-ips-7
#   89:          0          0          0          0          0          1          7          0   PCI-MSI-edge      np6_0-tx-rx3
#   90:          5          0          0          0          0          1          0          0   PCI-MSI-edge      np6_0-tx-rx4
#   91:          0          0          5          0          0          1          0          0   PCI-MSI-edge      np6_0-tx-rx5
#   92:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_0-err1
#   93:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_0-nturbo-err1
#   94:  207221826          0          0          0          0          0          1          0   PCI-MSI-edge      np6_1-tx-rx0
#   95:          0          0  200639569          0          0          0          1          0   PCI-MSI-edge      np6_1-tx-rx1
#   96:          0          0          0          0  240962811          0          1          0   PCI-MSI-edge      np6_1-tx-rx2
#   97:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_1-err0
#   98:          0          1  479259756          0          0          0          0          0   PCI-MSI-edge      np6_1-nturbo-tx-rx0
#   99:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_1-nturbo-err0
#  100:          0          0          1          0          0          0  240663469          0   PCI-MSI-edge      np6_1-tx-rx3
#  101:  210887756          0          1          0          0          0          0          0   PCI-MSI-edge      np6_1-tx-rx4
#  102:          0          0  202674599          0          0          0          0          0   PCI-MSI-edge      np6_1-tx-rx5
#  103:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_1-err1
#  104:          0          0          0          0          0          0          0          0   PCI-MSI-edge      np6_1-nturbo-err1
#  NMI:     451378     451332     451379     451331     451379     451330     451380     451329   Non-maskable interrupts
#  LOC:   27025393   27025374   27025356   27025338   27025320   27025302   27025284   27025266   Local timer interrupts
#  SPU:          0          0          0          0          0          0          0          0   Spurious interrupts
#  PMI:     451378     451332     451379     451331     451379     451330     451380     451329   Performance monitoring interrupts
#  IWI:          0          0          0          0          0          0          0          0   IRQ work interrupts
#  RES:   54764029   23029410   66355685   21516202   64664597   18859876   69639605   20136217   Rescheduling interrupts
#  CAL:       1227       1315       1304        287       1295       1290       1323       1325   Function call interrupts
#  TLB:        350        792       1188       1324        712        547        831        507   TLB shootdowns
#  ERR:          0
#  MIS:          0

# FG1K2D-2 # fnsysctl cat /proc/softirqs
#                     CPU0       CPU1       CPU2       CPU3       CPU4       CPU5       CPU6       CPU7
#           HI:          0          0          0          0          0          0          0          0
#        TIMER:   28521064   28525832   28520649   28526326   28524819   28526243   28524655   28526254
#       NET_TX:        994      57592        871        518        854        502        578        462
#       NET_RX:  576621254    1990912  889144076          0  350281983          2  353098308          0
#        BLOCK:        476        301        193     275534        181        396         98        313
# BLOCK_IOPOLL:          0          0          0          0          0          0          0          0
#      TASKLET:   14128586    1943262   12439627    1942008    9747759    1944864    9735439    1961939
#        SCHED:    9818324   13579287   11060339   13505914   10051866   12468454    9796770   12164434
#      HRTIMER:          0          0          0          0          0          0          0          0
#          RCU:   26288609   14045430   23576147   14059434   19574070   15025426   19446047   15275527

class ParserInterrupts(EasyParser):
	def prepare(self):
		self.re_cpus      = re.compile("^\s+CPU.*?(\d+)\s+\n")

	def get(self, soft=True, hard=True, description=None):
		interrupts   = {}
		collected_on = None
		cpus         = None
		desc_re      = None

		if description != None:
			desc_re = re.compile(description)

		if hard:
			hw = self.get_real('hard')
			interrupts.update(hw['interrupts'])
			collected_on = hw['collected_on']
			cpus         = hw['cpus']

		if soft:
			sw = self.get_real('soft')
			interrupts.update(sw['interrupts'])
			collected_on = sw['collected_on']
			cpus         = sw['cpus']

		if collected_on == None or cpus == None: 
			raise Exception('Either soft or hard interrupts must be selected')

		# filter out not matching
		for irq in interrupts.keys():
			if desc_re == None or desc_re.search(interrupts[irq]['description']) != None: continue
			del interrupts[irq]

		return {
			'collected_on': collected_on,
			'cpus'        : cpus,
			'interrupts'  : interrupts,
		}

	def get_real(self, source):
		if source == 'hard':
			interrupts = self.sshc.clever_exec("diagnose hardware sysinfo interrupts")
		elif source == 'soft':
			interrupts = self.sshc.clever_exec("fnsysctl cat /proc/softirqs")
		else:
			raise Exception('Interrupts can be either "hard" or "soft"')

		command_time = time.time()
		result = {}

		# count cpus
		g = self.re_cpus.search(interrupts)
		if g == None: raise Exception("Cannot count CPUs")
		cpus = int(g.group(1))+1

		# parse lines with entry for each cpu
		tmp = "^\s*(\S+):" + "\s*(\d+)"*cpus
		if source == 'hard': tmp += "\s+(.*?)[\r]*$"
		re_interrupt = re.compile(tmp, re.M)

		for iline in re_interrupt.findall(interrupts):
			if source == 'hard':
				try: int(iline[0])
				except ValueError: itype = 'other'
				else: itype = 'numeric'

				if itype == 'numeric':
					tmp = iline[-1].split(None, 1)
					trigger = tmp[0]
					desc    = tmp[1]
	
				elif itype == 'other':
					trigger = 'other'
					desc    = iline[-1]
			
			elif source == 'soft':
				itype = 'soft'
				trigger = 'other'
				if iline[0] == 'NET_RX':
					desc = 'Incoming packets (NAPI)'
				elif iline[0] == 'NET_TX':
					desc = 'Outgoing packets (NAPI)'
				elif iline[0] == 'HI':
					desc = 'High priority tasklet'
				elif iline[0] == 'TASKLET':
					desc = 'Normal priority tasklet'
				elif iline[0] == 'TIMER':
					desc = 'Normal timer'
				elif iline[0] == 'HRTIMER':
					desc = 'High-resolution timer'
				elif iline[0] == 'RCU':
					desc = 'RCU locking'
				elif iline[0] == 'SCHED':
					desc = 'Scheduler'
				elif iline[0] in ('BLOCK', 'BLOCK_IOPOLL'):
					desc = 'Block device (disk)'
				else:
					desc = 'softirq'

			ticks = {'total':0}
			for i in range(cpus):
				ticks[i] = int(iline[1+i])
				ticks['total'] += ticks[i]

			result[iline[0]] = {
				'type'        : itype,
				'trigger'     : trigger,
				'description' : desc,
				'ticks'       : ticks,
				'source'      : source,
			}

		# parse lines with single cpu column
		re_single = re.compile('^\s*(ERR|MIS):\s*(\d+)', re.M)
		for single in re_single.findall(interrupts):
			ticks = {'total': int(single[1])}
			for i in range(cpus): ticks[i] = ticks['total']

			result[single[0]] = {
				'type'        : 'single',
				'trigger'     : 'other',
				'description' : 'unknown',
				'ticks'       : ticks,
				'source'      : source,
			}

		return {
			'collected_on': command_time,
			'cpus'        : cpus,
			'interrupts'  : result,
		}

