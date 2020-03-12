#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.PCI import ParserPCI
from parsers.NP6Links import ParserNP6Links
from parsers.NP6Drops import ParserNP6Drops
from _common import ssh, cycle, simple_command_with_timestamp, prepend_timestamp

import re
import sys
import math
import time

sshc, args = ssh([
	{ 'name':'--cycle-time',   'type':float, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--max',   'type':int, 'default':0,  'help':'Maximum lines to show (unlimited by default)' },
	{ 'name':'--show-zeros',  'default':False, 'action':'store_true',  'help':'Include lanes with no traffic' },
	{ 'name':'--npu',   'type':int, 'default':[], 'action':'append',  'help':'Include only lanes from selected NPU' },
	{ 'name':'--npu-range', 'type':str, 'default':"",  'help':'Range of NPU to monitor (use "-" and ",")' },
	{ 'name':'--units', 'type':str, 'default':"",  'help':'Force units' },
	{ 'name':'--min-rate-mbps',  'type':int, 'default':0,  'help':'Minimum rate on lane to display (default 0)'},
	{ 'name':'--no-drops', 'default':False, 'action':'store_true',  'help':'Do not collect drop counters' },
	{ 'name':'--no-colors', 'default':False, 'action':'store_true',  'help':'Do not colorize counters' },
	{ 'name':'--no-sort', 'default':False, 'action':'store_true',  'help':'Do not sort by bandwidth' },
	{ 'name':'--sum-drops', 'default':False, 'action':'store_true',  'help':'Summarize drops instead of counting per second' },
], """
""", supports_script=False)

def do(sshc, cache, show_zeros, max_lines, include_npus, force_units, show_drops, use_colors, sum_drops, sort, min_rate_Bps):
	# Get all NP6 IDs from lspci
	pci = ParserPCI(sshc)
	np6ids = pci.simple_value(pci.get(), "np6_ids")

	# Collect current counters from all existing NPUs
	npus  = {}
	drops = {}
	for npuid in np6ids:
		if len(include_npus) > 0 and npuid not in include_npus: continue

		dc    = ParserNP6Drops(sshc).get(npuid=npuid)
		lanes = ParserNP6Links(sshc).get(npuid=npuid)
		npus[npuid]  = lanes
		drops[npuid] = dc

	# Get current time for output lines
	etime = ParserCurrentTime(sshc).get()

	# If this is first run, we need to wait for the next one to calculate difference
	if 'lanes' not in cache or 'drops' not in cache:
		cache["lanes"]  = npus
		cache["drops"] = drops
		return

	# For each lane calculate stats
	stat = []
	dstat = {}

	for npu in npus.keys():
		if npu not in cache["lanes"]: continue

		if show_drops:
			if sum_drops:
				if "drops_sum" not in cache: cache["drops_sum"] = {}
				if npu not in cache["drops_sum"]: cache["drops_sum"][npu] = 0
				if "drops_sum_last_update" not in cache: cache["drops_sum_last_update"] = {}
				if npu not in cache["drops_sum_last_update"]: cache["drops_sum_last_update"][npu] = 0

				dstat[npu] = cache["drops_sum"][npu] + drops[npu]["dce"]["summary"]
				if drops[npu]["dce"]["summary"] > 0: cache["drops_sum_last_update"][npu] = time.time()
			else:
				tdiff   = drops[npu]["collected_on"] - cache["drops"][npu]["collected_on"]
				dropped_since_last_read = drops[npu]["dce"]["summary"]
				dstat[npu] = int(math.ceil(float(dropped_since_last_read)/tdiff))

		for lane in npus[npu].keys():
			if lane not in cache["lanes"][npu]: continue

			tdiff = npus[npu][lane]['collected_on'] - cache['lanes'][npu][lane]['collected_on']
			alias = npus[npu][lane]['alias']
			speed = npus[npu][lane]['speed']
			rxp = npus[npu][lane]["counters"]["rx_packets_all"] - cache["lanes"][npu][lane]["counters"]["rx_packets_all"]
			txp = npus[npu][lane]["counters"]["tx_packets_all"] - cache["lanes"][npu][lane]["counters"]["tx_packets_all"]
			rxb = npus[npu][lane]["counters"]["rx_bytes_all"] - cache["lanes"][npu][lane]["counters"]["rx_bytes_all"]
			txb = npus[npu][lane]["counters"]["tx_bytes_all"] - cache["lanes"][npu][lane]["counters"]["tx_bytes_all"]
			rxps = int(math.ceil((float(rxp) / tdiff)))
			txps = int(math.ceil((float(txp) / tdiff)))
			rxbs = int(math.ceil((float(rxb) / tdiff)))
			txbs = int(math.ceil((float(txb) / tdiff)))

			stat.append( (npu, lane, {
				'alias': alias,
				'speed': speed,
				'rxp/s': rxps,
				'txp/s': txps,
				'rxB/s': rxbs,
				'txB/s': txbs,
			}) )

	# Sort by rx+tx bytes
	if sort:
		stat.sort(reverse=True, key=lambda x: x[2]["rxB/s"] + x[2]["txB/s"])

	# Print
	if os.name == 'nt':
		os.system('cls')
		print "NP6 lanes utilization    (written by Ondrej Holecek <oholecek@fortinet.com>)"
	else:
		print "\x1b[2J\x1b[H\033[1mNP6 lanes utilization    (written by Ondrej Holecek <oholecek@fortinet.com>)\033[0m"

	
	header = "NPU       LANE SPD       RX PPS      RX RATE units       TX PPS      TX RATE units"
	if show_drops: header += "  NPU DROPS"
	print prepend_timestamp(header, etime, 'np6top')

	lines = 0
	for s in stat:
		npu, lane, data = s
		if not show_zeros and (data["rxp/s"] == data["rxB/s"] == data["txp/s"] == data["txB/s"] == 0): continue
		if data["rxB/s"] < min_rate_Bps and data["txB/s"] < min_rate_Bps: continue

		if len(force_units) > 0:
			units_rxb = units_txb = force_units
		else:
			units_rxb = get_best_units(data["rxB/s"])
			units_txb = get_best_units(data["txB/s"])

		#data["speed"] = 1000
		rxb_util = float(data["rxB/s"]*100)/(data["speed"]*1000*1000/8)
		txb_util = float(data["txB/s"]*100)/(data["speed"]*1000*1000/8)

		if use_colors:
			rxb_color_start, txb_color_start, desc_color_start = get_colors( (rxb_util, txb_util,) )
			color_end = "\033[0m"
		else:
			rxb_color_start = txb_color_start = desc_color_start = ""
			color_end = ""

		if show_drops:
			mark = False
			if dstat[npu] == 0:
				drop_color_start = color_end
			elif dstat[npu] >= 10:
				drop_color_start = "\033[38;5;9m"
				mark = True
			else:
				drop_color_start = "\033[33m"
				mark = True

			if not use_colors or (sum_drops and time.time()-cache["drops_sum_last_update"][npu] > 10):
				drop_color_start = ""
				desc_color_start = ""
				mark = False

			if mark: desc_color_start = "\033[1m"

			line_drop = " %s%10i%s" % (drop_color_start, dstat[npu], color_end)

		line = "%s%3i %10s%s %3i %12i %s%12s %-5s%s %12i %s%12s %-5s%s" % (desc_color_start, npu, data["alias"], color_end, data["speed"]/1000,
		                                                                        data["rxp/s"], rxb_color_start, show_in_units(data["rxB/s"], units_rxb), units_rxb, color_end,
		                                                                        data["txp/s"], txb_color_start, show_in_units(data["txB/s"], units_txb), units_txb, color_end,
		                                                                        )

		if show_drops: line += line_drop

		print prepend_timestamp(line, etime, 'np6top') 

		lines += 1
		if max_lines != 0 and lines >= max_lines: break
	
	sys.stdout.flush()
	cache["lanes"] = npus
	cache["drops"] = drops
	cache["drops_sum"] = dstat
	return etime

def get_colors(utils):
	out = []
	mark = False

	for util in utils:
		if util > 75:
			color_start  = "\033[38;5;9m"
			mark         = True
		elif util > 50:
			color_start  = "\033[33m"
			mark         = True
		elif util > 10:
			color_start  = "\033[32m"
		else:
			color_start = "\033[0m"

		out.append(color_start)
	
	if mark: out.append("\033[1m")
	else   : out.append("\033[0m")

	return tuple(out)

def show_in_units(Bps, units):
	if units[-2:] != "ps": raise Exception("Invalid units")
	if units[-3] not in ["b", "B"]: raise Exception("Invalid units")

	bB    = units[-3]
	multi = units[:-3]

	tmp = float(Bps)
	if multi in ["k", "K"]:      tmp /= 1000
	elif multi in ["m", "M"]:    tmp /= 1000*1000
	elif multi in ["g", "G"]:    tmp /= 1000*1000*1000
	elif multi in ["t", "T"]:    tmp /= 1000*1000*1000*1000

	# possible convert from bytes to bits
	if bB == "b": tmp *= 8

	# return decimal point number only if the base is smaller than 1000
	if tmp < 1000:
		return "%.1f" % (tmp,)
	else:
		return "%i" % (round(tmp, 0),)

# Always prefer mutliply of bits (rather than Bytes)
# Always prefer SI units over "computer units" (kibi, mibi, etc.)
def get_best_units(Bps):
	bps = Bps * 8
	if    bps < 1000: return "bps"
	elif  bps < 1000*1000: return "Kbps"
	elif  bps < 1000*1000*1000: return "Mbps"
	elif  bps < 1000*1000*1000*1000: return "Gbps"
	else: return "Tbps"
	

if __name__ == '__main__':
	# get npu id from range
	npus = []
	for nr in args.npu_range.split(","):
		r = nr.split("-")
		if len(r) == 1:
			try: 
				if int(r[0]) not in npus:
					npus.append(int(r[0]))
			except: pass
			continue

		for i in range(int(r[0]), int(r[1])+1):
			if i not in npus: npus.append(i)

	# add the npu ids from simple command
	for i in args.npu:
		if i not in npus: npus.append(i)

	#
	cache = {}
	try:
		cycle(do, {
			'sshc': sshc, 
			'cache': cache,
			'show_zeros': args.show_zeros,
			'max_lines': args.max,
			'include_npus': npus,
			'force_units': args.units,
			'show_drops': not args.no_drops,
			'use_colors': not args.no_colors,
			'sum_drops': args.sum_drops,
			'min_rate_Bps': args.min_rate_mbps*1000*1000/8,
			'sort': not args.no_sort,
		}, args.cycle_time, cycles_left=[args.max_cycles], debug=args.debug, interactive=args.interactive)
	except KeyboardInterrupt:
		sshc.destroy()

