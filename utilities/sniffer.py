#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _common import ssh, prepend_timestamp

import re
import datetime
import pytz
import struct
import sys

sshc, args = ssh([
	{ 'name':'--filter',  'default':'',  'help':'Tcpdump filter, default ""' },
	{ 'name':'--interface',  'default':'any',  'help':'Interface name, default "any"' },
	{ 'name':'--direction',  'default':'both', 'choices':['in','out','both'], 'help':'Which direction to save, default "both"' },
	{ 'name':'--simulate',  'help':'File name to simulate the SSH output' },
], """
Run the sniffer of FortiGate and dump packets in libpcap (old) format on standard input.

Can be processed by Wireshark with:
$ wireshark -k -i <(./sniffer.py  --host 10.109.250.102 --port 10003 --filter 'proto 89')
""")

# 
# 2018-11-12 13:17:24.757883 port4 in 10.1.4.5 -> 224.0.0.5:  ip-proto-89 48
# 0x0000	 0100 0000 0000 0050 5694 5986 0800 45c0	.......PV.Y...E.
# 0x0010	 0044 d1a8 4000 0159 b8ed 0a01 0405 e000	.D..@..Y........
# 0x0020	 0005 0201 0030 0000 0005 0000 0000 e088	.....0..........
# 0x0030	 0000 0000 0000 0000 0000 ffff ff00 000a	................
# 0x0040	 0201 0000 0028 0a01 0403 0a01 0405 0000	.....(..........
# 0x0050	 0003                                   	..
# 


re_packet = re.compile('^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}).(\d{6}) (\S+) (\S+) (\S+) -> (\S+):.*?[\r\n]+(.*?)\r?\n\r?\n', re.M | re.DOTALL)
unix_epoch_start  = pytz.UTC.localize(datetime.datetime(1970, 1, 1, 0, 0, 0))

def divide(data, info):
	# returns (result, data)
	
	packets = []

	while True:
		g = re_packet.search(data)
		if g == None: break

		packets.append(data[g.start():g.end()])
		data = data[g.end():]
	
	return packets, data

def result(data, info):
	g = re_packet.search(data)
	if g == None: return # this should not happen

	ts = pytz.UTC.localize(datetime.datetime(int(g.group(1)), int(g.group(2)), int(g.group(3)), int(g.group(4)), int(g.group(5)), int(g.group(6)), int(g.group(7))))
	td = ts-unix_epoch_start
	us = td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6

	iface = g.group(8)
	direction = g.group(9)
	src = g.group(10)
	dst = g.group(11)
	pkt = g.group(12)

	hstr = ''
	for pktl in pkt.split("\n"):
		hstr += pktl.split("\t")[1].replace(' ', '')
	bpkt = hstr.decode('hex')

	if info['save_direction'] == 'in' and direction != 'in': return
	if info['save_direction'] == 'out' and direction != 'out': return

	# save packet
	pcap_packet(bpkt, us)


def finished(info):
	if 'no_new_data' in info and info['no_new_data'] == True: return ''
	return None

def pcap_packet(pkt, us):

	packet_header = struct.pack('>IIII',
		us / 1000000,
		us % 1000000,
		len(pkt),
		len(pkt))

	sys.stdout.write(packet_header)
	sys.stdout.write(pkt)
	sys.stdout.flush()

def pcap_header():
	global_header = struct.pack('>IHHIIII',
		0xa1b2c3d4,
		2,
		4,
		0,
		0,
		65535,
		1)
	
	sys.stdout.write(global_header)
	sys.stdout.flush()

def do(sshc, interface, filter_string):
	if args.simulate:
		simulated_file = open(args.simulate, 'rb')
	else:
		simulated_file = None

	pcap_header()
	info = { 'info': {
		'save_direction': args.direction,
	}}
	sshc.continuous_exec("diagnose sniffer packet %s '%s' 6 0 a" % (interface, filter_string,), divide, result, finished, info, simulate=simulated_file)

if __name__ == '__main__':
	try:
		do(sshc, args.interface, args.filter)
	except (KeyboardInterrupt, IOError):
		sshc.destroy()

