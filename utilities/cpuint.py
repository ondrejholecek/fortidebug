#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.Processes import ParserProcesses
from _common import ssh, cycle, prepend_timestamp

import re
import sys

sshc, args = ssh([
	{ 'name':'--silent',    'default':False, 'action':'store_true',  'help':'Do not display any progress' },
	{ 'name':'--cpu',       'default':None,  'action':'append',      'help':'Show only specific CPU(s)' },
	{ 'name':'--desc',      'default':None,                          'help':'Only show handler matching RE' },
	{ 'name':'--with-time', 'default':False, 'action':'store_true',  'help':'Show timestamp on each line' },
	{ 'name':'--no-colors', 'default':False, 'action':'store_true',  'help':'Do not colorize handlers' },
], """
Show how interrupts are bound to CPU cores.

Because on some devices the required data collection can take even more than a minute, 
it shows the progress by default, but it can be disabled with `--silent` parameter.

All IRQs and all CPUs are shown by default, but it can be limited using `--cpu` and
`--desc` parameters. Both can be used more than ones. Parameter `--cpu` expects cpu
id and paramter `--desc` expects a regular expression that must match on handler name.

Some IRQs have no affinity, which means those can be handled by any CPU, however to make
the output more readable, those were move to the 'CPU All' section at the end of output,
which will be display unless `--cpu` parameter is used.

By default some well known handlers are colorized (on non-Windows terminals),
this can be disabled with `--no-colors` parameter.
""")

# Colours for handlers
# https://jonasjacek.github.io/colors/
colours = {
	re.compile("^(np6_[0-9]+-tx-rx)([0-9]+)"): ( ("\033[38;5;197m", "\033[0m"), ("\033[38;5;204m", "\033[0m") ),
	re.compile("^(np6_[0-9]+-nturbo-tx-rx)([0-9]+)"): ( ("\033[38;5;172m", "\033[0m"), ("\033[38;5;180m", "\033[0m") ),
	re.compile("^(np6_[0-9]+-nturbo-ips-)([0-9]+)"): ( ("\033[38;5;99m", "\033[0m"), ("\033[38;5;104m", "\033[0m") ),
	re.compile("^(cp8_[0-9]+_kxp)"): ( ("\033[38;5;177m", "\033[0m"), ),
	re.compile("^(cp8_[0-9]+_vpn)([0-9]+)"): ( ("\033[38;5;107m", "\033[0m"), ("\033[38;5;65m", "\033[0m") ),
	re.compile("^(cp9kxp_[0-9]+)(_.*)"): ( ("\033[38;5;177m", "\033[0m"), ("\033[38;5;128m", "\033[0m") ),
	re.compile("^(cp9vpn_[0-9]+)(_.*)"): ( ("\033[38;5;107m", "\033[0m"), ("\033[38;5;65m", "\033[0m") ),
}

def do(sshc, silent, show_cpus, desc, show_time, colors):
	etime = ParserCurrentTime(sshc).get()

	# colors disabled?
	if not colors: 
		global colours
		colours = {}

	# get the structure with all information
	# it is a map with irq number as a key, containing another map with 'cpus' and 'handlers' keys
	# 'cpus' is a list of cpu numbers
	# 'handlers' is a list of string
	cpus, irqs = get(sshc, silent, colors)
	irqs_on_all_cpus = []

	# print one CPU on a line
	for cpu in range(cpus):
		# do we want to display only some cpus?
		if show_cpus != None and cpu not in show_cpus: continue

		line = "CPU %3d:" % (cpu,)

		# for through all the irqs and find those that run
		# on the current cpu id
		hcount = 0
		for irq in irqs.keys():
			if cpu not in irqs[irq]['cpus']: continue

			# ignore irqs that are handled by all the cpus for this moment
			if len(irqs[irq]['cpus']) == cpus:
				if irq not in irqs_on_all_cpus: irqs_on_all_cpus.append(irq)
				continue
				
			# get nicely formatted handlers
			pline, handlers = join_handlers(irqs[irq]['handlers'], irqs[irq]['cpus'], desc, True)
			line   += pline
			hcount += handlers

		if desc == None or hcount > 0:
			if show_time: print prepend_timestamp(line, etime, "cpuint")
			else: print line
	
	# now prepare line for irqs handled by all cpus
	line = "CPU ALL:"
	for irq in irqs_on_all_cpus:
		pline, handlers = join_handlers(irqs[irq]['handlers'], irqs[irq]['cpus'], desc, False)
		line += pline

	# but show it only if there are no specific cpus requested
	if show_cpus == None:
		if show_time: print prepend_timestamp(line, etime, "cpuint")
		else: print line

	#
	sys.stdout.flush()

# Join the handler names and make sure they match regexp is one is used
# and that we differciate multi-cpu handlers if that was requested
def join_handlers(handlers, cpus, desc, highlight_multicpu):
	cnt  = 0
	line = ""

	for h in handlers:
		h = h.strip()

		# show only handlers matching regexp?
		if desc != None and desc.search(h) == None: continue

		# if there is no handler name, use irq number in parenthesis
		if len(h) == 0: h = "(%u)" % (irq,)
	
		# colorize some well known handlers
		for color in colours.keys():
			g = color.search(h)
			if g == None: continue

			nh = h[:g.start(1)]
			for gn in range(1, len(g.groups())+1):
				nh += colours[color][gn-1][0] + h[g.start(gn):g.end(gn)] + colours[color][gn-1][1]
			nh += h[g.end(gn):]
			h   = nh

			#h = h[:g.start(1)] + colours[color][0] + h[g.start(1):g.end(1)] + colours[color][1] + h[g.end(1):]

		# sometimes we want to highlight the handlers that are handled
		# by more than one cpu - show them in brackets
		if highlight_multicpu and len(cpus) > 1:
			line += " [%s]" % (h,)
		else:
			line += " %s" % (h,)

		cnt += 1
	
	return line, cnt


# Collect all the hw interrupts and information about them
def get(sshc, silent, colors):
	#            CPU0       CPU1       CPU2       CPU3       CPU4       CPU5       CPU6       [...]     CPU36      CPU37      CPU38      CPU39
	#   0:         38          0          0          0          0          0          0       [...]         0          0          0          0   IO-APIC-edge      timer
	#   2:          0          0          0          0          0          0          0       [...]         0          0          0          0    XT-PIC-XT-PIC    cascade
	#   3:    6238144          0          0          0          0          0          0       [...]         0          0          0          0   IO-APIC-edge      serial
	# [...]
	#  19:          0          0          0          0          0          0          0       [...]         0          0          0          0   IO-APIC-fasteoi   uhci_hcd:usb5, uhci_hcd:usb8
	#  88:      68904          0          0          0          0          0          0       [...]         0          0          0          0   PCI-MSI-edge      ahci
	#  89:          0          0          0          0          0          0          0       [...]         0          0          0          0   PCI-MSI-edge      cp8_0_vpn0
	# [...]
	#
	# get all hardware interrupts and extract the number of CPU columns
	out    = sshc.clever_exec("fnsysctl cat /proc/interrupts", None)
	lines  = [ tmp.strip() for tmp in out.split("\n") ]
	cpus   = len(lines[0].split())

	result = {}
	if not silent: 
		if colors: print "\033[38;5;242mCollecting IRQs:",
		else: print "Collecting IRQs:",

	# for each interrupt line...
	for interrupt in lines[1:]:
		# separate columns and ignore invalid lines
		s = interrupt.split()
		if len(s) < 1+cpus+1+1: continue

		# translate irq: to number save handlers columns
		# + ignore lines with non-numeric IRQs
		try: irq   = int(s[0][:-1])
		except ValueError: continue
		handlers = s[1+cpus+1:]

		# print progress
		if not silent: 
			print irq,
			sys.stdout.flush()

		# get the IRQ affinity and convert it to a list of CPU numbers
		this = sshc.clever_exec("fnsysctl cat /proc/irq/%u/smp_affinity" % (irq,), None).strip()
		affi = hex_to_cpus(this)

		# save
		result[irq] = {
			'handlers': handlers,
			'cpus'   : affi,
		}

	if not silent: 
		if colors: print "\033[0m"
		else: print

	return cpus, result
	

# Converts strings like 00,00004000 or ff,fffffffff to a list of integers
# that represent the core numbers
def hex_to_cpus(s):
	cpus    = []
	current = 0

	# work group by group, start with the last, current holds the current
	# bit offset (which is also the cpu id)
	for group in reversed(s.split(',')):
		# convert 32bit hex to binary string composed of 1s and 0s, filled from beginning
		g = int(group, 16)
		binary = "{0:032b}".format(g)

		# for each bit in binary string check if it is 1 and append the cpu id if so
		# again work from right
		for b in reversed(binary):
			if b == "1": cpus.append(current)
			current += 1

	return cpus


if __name__ == '__main__':
	if args.cpu != None:
		show_cpus = [ int(x) for x in args.cpu ]
	else:
		show_cpus = None

	if args.desc != None:
		desc = re.compile(args.desc)
	else:
		desc = None

	if os.name == 'nt': 
		args.no_colors = True

	try:
		do(sshc, args.silent, show_cpus, desc, args.with_time, not args.no_colors)
	except KeyboardInterrupt:
		sshc.destroy()

