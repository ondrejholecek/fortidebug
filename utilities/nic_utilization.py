#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.name == 'nt': import msvcrt

from parsers.CurrentTime import ParserCurrentTime
from parsers.NIC2 import ParserNIC2
from parsers.NP6Links import ParserNP6Links
from parsers.NP6Drops import ParserNP6Drops
from parsers.SystemInterfaceList import ParserSystemInterfaceList
from parsers.HWInterfaceList import ParserHWInterfaceList
from models.GenericModel import GetModelSpec
from _common import ssh, cycle, prepend_timestamp

import re
import sys
import select
import time
import datetime

sshc, args = ssh([
	{ 'name':'--cycle-time',     'type':int, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--iface',          'default':None, 'action':'append',  'help':'Show this interface only (can repeat)' },
	{ 'name':'--all-ifaces',     'default':False, 'action':'store_true',  'help':'Show all interfaces regardless on link status' },
	{ 'name':'--display',        'default':'fnkod', 'help':'What fields to disply (f, n, k, o, d)' },
	{ 'name':'--show-timestamp', 'default':False, 'action':'store_true',  'help':'Show timestamp on each line' },
	{ 'name':'--no-colors',      'default':False, 'action':'store_true',  'help':'Do not colorize the output' },
], """
This program collects the traffic counters from network interfaces. By default it only shows the interface in the
up state, but it can be changed with `--all-iface` option or by pressing the 'a' key (and enter).

It collects the "front port" counters ("wire" counters on the incoming ports), npu counters (traffic hitting the NPU)
and the kernel counters (traffic that is not offloaded). By default all counters are shown and they can be enabled/disabled 
by pressing "f", "n" or "k" keys (and enter). All bandwidth counters are shown in the relevant units and the program
uses the SI to calculate them (ie. dividing by 1000 and NOT by 1024).

Be aware that on some models the NPU lanes are shared. This program displays the NPU column for each interface, 
but in case of shared lanes the same counter will be displayed for all the relevant interfaces.

There are also drop counters collected. Visibility of this field can be enabled/disabled with 'd' key. Similar to NPU counters, 
the drop counters are disabled for each interface, but they are collected for the whole NPU, hence the numbers will be the same 
for all the ports on the same NPU. Unlike others, these counters are not averaged per second, but intestat the total number 
of drops is shown. Drop counters can be zeroed with "z" key. 

This program needs a definition of ports used by each platform. It is possible that your platform is not yet supported,
but it should not be a problem to add the right definition - just send an email to Ondrej Holecek <oholecek@fortinet.com>.

If you are running this program with the output redirected to file, you most probably want to use `--show-timestamp` and `--no-colors` options.
""")

def diff_counters(prev, curr, seconds):
	if prev == None or curr == None: return None

	diff = {}
	for k in curr.keys():
		if k not in prev.keys(): continue

		# exceptions for not-really-counters :)
		if k in ('speed'):
			diff[k] = curr[k]
			continue

		#
		if seconds != 0:
			diff[k] = int(round((curr[k] - prev[k]) / seconds))
		else:
			diff[k] = 0
		
	return diff

def show(stats, info, etime):
	if os.name == 'nt':
		os.system('cls')
		print "FortiGate interface statistics. Last update on: %s  (written by Ondrej Holecek <oholecek@fortinet.com>)" % (datetime.datetime.now().replace(microsecond=0),)
	else:
		print "\x1b[2J\x1b[H\033[1mFortiGate interface statistics. Last update on: %s  (written by Ondrej Holecek <oholecek@fortinet.com>)\033[0m" % (datetime.datetime.now().replace(microsecond=0),)

	# header
	line = "Interface      Speed"
	if info['show_front']:      line += show_traffic(custom="Front port")
	if info['show_npu']:        line += show_traffic(custom=" NPU")
	if info['show_kernel']:     line += show_traffic(custom="Kernel")
	if info['show_offloaded']:  line += show_percentage(custom="Offloaded %")
	if info['show_drops']:      line += show_drops(custom="NPU Drops (sum)")
	line += " |"

	if info['show_timestamp']:
		print prepend_timestamp("-"*len(line), etime, "nic")
		print prepend_timestamp(line, etime, "nic")
	else:
		print "-"*len(line)
		print line

	# headers
	line = "%s" % (" "*20,)
	if info['show_front']:     line += show_traffic(header=True)
	if info['show_npu']:       line += show_traffic(header=True)
	if info['show_kernel']:    line += show_traffic(header=True)
	if info['show_offloaded']: line += show_percentage(header=True)
	if info['show_drops']:     line += show_drops(header=True)
	line += " |"

	if info['show_timestamp']:
		print prepend_timestamp(line, etime, "nic")
	else:
		print line

	# data
	for iface in sorted(stats.keys()):
		if stats[iface]['front'] == None:
			spd = "???"
		else:
			spd = str(stats[iface]['front']['speed'])

		line = "%s%s%s" % (iface, " "*(20-len(iface)-len(spd)), spd, )

		if info['show_front']:
			line += show_traffic(stats[iface]['front'])
		if info['show_npu']:
			line += show_traffic(stats[iface]['npu'])
		if info['show_kernel']:
			line += show_traffic(stats[iface]['kernel'])
		if info['show_offloaded']:
			line += show_percentage(stats[iface]['offloaded'])
		if info['show_drops']:
			line += show_drops(stats[iface]['npudrops'])

		line += " |"
		
		if info['show_timestamp']:
			print prepend_timestamp(line, etime, "nic")
		else:
			print line

		sys.stdout.flush()

def show_traffic(counter=None, header=False, custom=None):
	if custom != None:
		pre  = (47 - len(custom)) / 2
		post = 47 - len(custom) - pre
		return " | %s%s%s" % (" "*pre, custom, " "*post)

	if header:
		return " | Rx packets       Rx bps Tx packets       Tx bps"

	if counter == None:
		return " |        ---          ---        ---          ---"

	try:
		perc_rx = int(round(float(counter['rx_bytes_all'] * 8 * 100) / (counter['speed']*1000*1000)))
	except ZeroDivisionError:
		perc_rx = 0
	try:
		perc_tx = int(round(float(counter['tx_bytes_all'] * 8 * 100) / (counter['speed']*1000*1000)))
	except ZeroDivisionError:
		perc_tx = 0

	# http://jafrog.com/2013/11/23/colors-in-terminal.html
	if perc_rx > 75:
		#color_rx  = "\033[31m"
		color_rx  = "\033[38;5;9m"
	elif perc_rx > 50:
		#color_rx  = "\033[38;5;11m"
		color_rx  = "\033[33m"
	elif perc_rx > 10:
		color_rx  = "\033[32m"
	else:
		color_rx = "\033[0m"

	if perc_tx > 75:
		#color_tx  = "\033[31m"
		color_tx  = "\033[38;5;9m"
	elif perc_tx > 50:
		#color_tx  = "\033[38;5;11m"
		color_tx  = "\033[33m"
	elif perc_tx > 10:
		color_tx  = "\033[32m"
	else:
		color_tx = "\033[0m"
	
	color_end = "\033[0m"

	if not info['show_colors']:
		color_rx   = ""
		color_tx   = ""
		color_end  = ""

	#return " | %10i %12i %10i %12i" % (
	return " | %10i %s%12s%s %10i %s%12s%s" % (
		counter['rx_packets_all'],
		color_rx,
		get_nice_bw(counter['rx_bytes_all']),
		color_end,
		counter['tx_packets_all'],
		color_tx,
		get_nice_bw(counter['tx_bytes_all']),
		color_end,
	)

def get_nice_bw(Bps):
	bps = float(Bps * 8)

	if bps < 1000:  # less than 1 kbps
		r = (bps, '')
	elif bps < 900*1000:  # > 1 kbps && < 1 Mbps
		r = (bps/1000, 'k')
	elif bps < 900*1000*1000:  # > 1 mbps && < 1 Gbps
		r = (bps/1000/1000, 'm')
	else:  # > 1 Gbps
		r = (bps/1000/1000/1000, 'g')
	
	if r[1] == '':
		return "%10i b" % (r[0],)
	elif r[1] == 'k':
		return "%6.2f kb" % (r[0],)
	elif r[1] == 'm':
		return "%6.2f mb" % (r[0],)
	elif r[1] == 'g':
		return "%6.2f gb" % (r[0],)
		
	
def show_percentage(counter=None, header=False, custom=None):
	if custom != None:
		pre  = (15 - len(custom)) / 2
		post = 15 - len(custom) - pre
		return " | %s%s%s" % (" "*pre, custom, " "*post)

	if header:
		return " | RxP RxB TxP TxB"

	if counter == None:
		return " | --- --- --- ---"

	return " | %3i %3i %3i %3i" % (
		counter['rx_packets_all'],
		counter['rx_bytes_all'],
		counter['tx_packets_all'],
		counter['tx_bytes_all'],
	)

def show_drops(counter=None, header=False, custom=None):
	if custom != None:
		pre  = (23 - len(custom)) / 2
		post = 23 - len(custom) - pre
		return " | %s%s%s" % (" "*pre, custom, " "*post)

	if header:
		return " |     dce     hrx anomaly"

	if counter == None:
		return " |     ---     ---     ---"

	# colors
	color     = {}
	tm        = time.time()
	color_end = "\033[0m"

	for dc in ('dce', 'hrx', 'ano'):
		if (dc+'_changed') not in counter:
			color[dc] = color_end
		elif counter[dc] == 0:
			color[dc] = color_end
		elif counter[dc+'_changed'] == 0:
			color[dc] = color_end
		elif (tm - counter[dc+'_changed']) < 30:
			color[dc] = "\033[38;5;9m"
		elif (tm - counter[dc+'_changed']) < 60:
			color[dc] = "\033[33m"
		else:
			color[dc] = color_end

	if not info['show_colors']:
		for dc in ('dce', 'hrx', 'ano'):
			color[dc] = ""
		color_end = ""
	
	return " | %s%7i%s %s%7i%s %s%7i%s" % (
		color['dce'],
		counter['dce'],
		color_end,
		color['hrx'],
		counter['hrx'],
		color_end,
		color['ano'],
		counter['ano'],
		color_end,
	)


	
def change_view(info):
	while True:
		if os.name == 'nt':
			if msvcrt.kbhit(): r = msvcrt.getch()
			else: break
		else:
			(fin, fout, fexc) = select.select([sys.stdin], [], [], 0)
			if sys.stdin not in fin: break
			r = sys.stdin.read(1).lower()

		if r == 'q': raise KeyboardInterrupt()
		if r == 'f': info['show_front']      = not info['show_front']
		if r == 'n': info['show_npu']        = not info['show_npu']
		if r == 'k': info['show_kernel']     = not info['show_kernel']
		if r == 'o': info['show_offloaded']  = not info['show_offloaded']
		if r == 'd': info['show_drops']      = not info['show_drops']
		if r == 'z': info['clear_drops']     = True
		if r == 'a': info['all_ifaces']      = not info['all_ifaces']
		if r == 'r': 
			info['show_front']      = info['defaults']['show_front']
			info['show_npu']        = info['defaults']['show_npu']
			info['show_kernel']     = info['defaults']['show_kernel']
			info['show_offloaded']  = info['defaults']['show_offloaded']
			info['show_drops']      = info['defaults']['show_drops']
			info['all_ifaces']      = info['defaults']['all_ifaces']

def do(sshc, ifaces, spec, info):
	change_view(info)

	etime = ParserCurrentTime(sshc).get()

	# if no interfaces were specified, select all of them
	if ifaces == None:
		check_ifaces = spec.ports.keys()
	else:
		check_ifaces = ifaces
	
	# select only those that are up
	up_ifaces = ParserSystemInterfaceList(sshc).get2(None, True)

	for iface in up_ifaces.keys():
		if iface not in check_ifaces: del up_ifaces[iface]
	
	# get counters
	buf_np6 = {}
	buf_counters = {}
	stats = {}
	for iface in up_ifaces:
		stats[iface] = {
			'collected_on': None
		}

		for t in ('front', 'npu', 'kernel'):
			# get counters
			if spec.ports[iface][t] == None:
				stats[iface][t] = None
			elif spec.ports[iface][t].source == spec.ports[iface][t].SRC_HWNIC:
				if iface not in buf_counters:
					buf_counters[iface] = ParserNIC2(sshc).get(iface)
				stats[iface][t] = buf_counters[iface]['counters'][spec.ports[iface][t].counter]
				stats[iface]['collected_on'] = buf_counters[iface]['collected_on']
			elif spec.ports[iface][t].source == spec.ports[iface][t].SRC_NP6_PORTSTATS:
				(npid, cname) = spec.ports[iface][t].counter.split('/', 1)
				# collect only necessary np6 and only once
				npid = int(npid)
				if npid not in buf_np6:
					buf_np6[npid] = ParserNP6Links(sshc).get(npid)
				#
				stats[iface][t] = buf_np6[npid][cname]['counters']
				stats[iface]['collected_on'] = buf_np6[npid][cname]['collected_on']
			else:
				stats[iface][t] = None

			# get speed
			if spec.ports[iface][t] == None:
				stats[iface][t] = None
			elif spec.ports[iface][t].maxspeed == spec.ports[iface][t].SPD_S1G:
				stats[iface][t]['speed'] = 1000
			elif spec.ports[iface][t].maxspeed == spec.ports[iface][t].SPD_S10G:
				stats[iface][t]['speed'] = 10000
			elif spec.ports[iface][t].maxspeed == spec.ports[iface][t].SPD_IFACE:
				if iface not in buf_counters:
					buf_counters[iface] = ParserNIC2(sshc).get(iface)
				stats[iface][t]['speed'] = buf_counters[iface]['speed']
			else:
				stats[iface][t]['speed'] = 0

	# check if we have previous value
	if 'prev' not in info:
		info['prev'] = stats
		return
	else:
		prev = info['prev']

	# calculate diff 
	diff = {}
	for iface in up_ifaces:
		diff[iface] = {}

		for t in ('front', 'npu', 'kernel'):
			try:
				diff[iface][t] = diff_counters(prev[iface][t], stats[iface][t], stats[iface]['collected_on'] - prev[iface]['collected_on'])
			except KeyError:
				del diff[iface]
				break

	# calculate npu drops
	buf_np6drops = {}
	for iface in diff.keys():
		if spec.ports[iface]['npudrops'] == None:
			diff[iface]['npudrops'] = None
		elif spec.ports[iface]['npudrops'].source == spec.ports[iface]['npudrops'].SRC_NP6_DROPS:
			npuid =  spec.ports[iface]['npudrops'].npuid
			if npuid not in buf_np6drops: 
				buf_np6drops[npuid] = ParserNP6Drops(sshc).get(npuid)
			diff[iface]['npudrops'] = {
				'dce': buf_np6drops[npuid]['dce']['summary'],
				'dce_changed': 0,
				'ano': buf_np6drops[npuid]['ano']['summary'],
				'ano_changed': 0,
				'hrx': buf_np6drops[npuid]['hrx']['summary'],
				'hrx_changed': 0, 
			}

		if info['clear_drops'] and prev[iface]['npudrops'] != None:
			for dc in ('dce', 'ano', 'hrx'):
				prev[iface]['npudrops'][dc] = 0
				prev[iface]['npudrops'][dc+"_changed"] = 0


		if (diff[iface]['npudrops'] != None) and ('npudrops' in prev[iface] and prev[iface]['npudrops'] != None):
			for dc in ('dce', 'ano', 'hrx'):
				if diff[iface]['npudrops'][dc] > 0:
					diff[iface]['npudrops'][dc] += prev[iface]['npudrops'][dc]
					diff[iface]['npudrops'][dc+"_changed"] = time.time()
				else:
					diff[iface]['npudrops'][dc] = prev[iface]['npudrops'][dc]
					diff[iface]['npudrops'][dc+"_changed"] = prev[iface]['npudrops'][dc+"_changed"]

		stats[iface]['npudrops'] = diff[iface]['npudrops']

	info['clear_drops'] = False
	
	# calculate offloaded
	for iface in diff.keys():
		if ('front' not in diff[iface] or diff[iface]['front'] == None) or ('kernel' not in diff[iface] or diff[iface]['kernel'] == None):
			diff[iface]['offloaded'] = None
			continue
		else:
			diff[iface]['offloaded'] = {}

		for c in diff[iface]['front']:
			try: 
				diff[iface]['offloaded'][c] = int(round(100 - float(diff[iface]['kernel'][c] * 100)/float(diff[iface]['front'][c])))
				if diff[iface]['offloaded'][c] < 0: diff[iface]['offloaded'][c] = 0
			except ZeroDivisionError: diff[iface]['offloaded'][c] = 0

	# show
	show(diff, info, etime)

	# save for next cycle
	info['prev'] = stats


if __name__ == '__main__':
	info = {
		'defaults': {
			'show_front'     : False,
			'show_npu'       : False,
			'show_kernel'    : False,
			'show_offloaded' : False,
			'show_drops'     : False,
			'all_ifaces'     : False,
		},
		'show_front'     : False,
		'show_npu'       : False,
		'show_kernel'    : False,
		'show_offloaded' : False,
		'show_drops'     : False,
		'clear_drops'    : False,
		'all_ifaces'     : False,
		'show_timestamp' : False,
		'show_colors'    : True,
	}

	for d in args.display:
		if d == 'f':
			info['defaults']['show_front'] = True
			info['show_front'] = True
		elif d == 'n':
			info['defaults']['show_npu'] = True
			info['show_npu'] = True
		elif d == 'k':
			info['defaults']['show_kernel'] = True
			info['show_kernel'] = True
		elif d == 'o':
			info['defaults']['show_offloaded'] = True
			info['show_offloaded'] = True
		elif d == 'd':
			info['defaults']['show_drops'] = True
			info['show_drops'] = True
	
	if args.all_ifaces:
		info['defaults']['all_ifaces'] = True
		info['all_ifaces'] = True

	if args.show_timestamp:
		info['show_timestamp'] = True

	# Windows terminal cannot show colors the way we use...
	if args.no_colors or os.name == 'nt':
		info['show_colors'] = False

	# disable buffering for stdin
	sys.stdin = os.fdopen(sys.stdin.fileno(), "r", 0)

	# spec
	spec = GetModelSpec(sshc.get_info()['serial'])
	if spec == None:
		print >>sys.stderr, "This model is not yet supported. Contact Ondrej Holecek <oholecek@fortinet.com> to add support for SN %s." % (sshc.get_info()['serial'],)
		sys.exit(0)

	try:
		cycle(do, {
			'sshc': sshc, 
			'ifaces': args.iface,
			'spec': spec,
			'info': info,
		}, args.cycle_time, cycles_left=[args.max_cycles], debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

