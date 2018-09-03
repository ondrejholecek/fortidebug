from EasyParser import EasyParser

import re
import time

class ParserProcessCPU(EasyParser):
	def prepare(self):
		self.re_main_split = re.compile("^(.*?\nsoftirq .*?\n)(.*)$", re.DOTALL)
		self.re_global_cpu = re.compile("^cpu\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+", re.M)
		self.re_process    = re.compile("^(\d+)\s+\((.*?)\)\s+(\S+)\s+(.*)$")

	def get(self, pids):
		if type(pids) == int: pids = [pids]

		files = "/proc/stat"
		for pid in pids:
			files += " /proc/%i/stat" % (pid,)

		pss = self.sshc.clever_exec("fnsysctl cat %s" % (files,))

		# split the all cpu stats from per process stats
		g = self.re_main_split.search(pss)
		if not g:
			print "Debug: cannot split the output"
			return None

		cpu_global = g.group(1)
		cpu_processes = g.group(2)

		g = self.re_global_cpu.search(cpu_global)
		if not g:
			print "Debug: cannot parse global CPU utilization"
			return None

		
		results = { 
			'global'    : None, 
			'processes' : {},
			'time'      : time.time(),
		}

		results['global'] = {
			'user': int(g.group(1)),
			'nice': int(g.group(2)),
			'system': int(g.group(3)),
			'idle': int(g.group(4)),
			'iowait': int(g.group(5)),
			'irq': int(g.group(6)),
			'softirq': int(g.group(7)),
		}

		# parse user cpu
		for ps in cpu_processes.split("\n"):
			ps = ps.strip()
			if len(ps) == 0: continue
			g = self.re_process.search(ps)
			if not g:
				#print "Debug: cannot parse process"
				continue

			# we do it this way to handle possible (?) space in process name and use numbers from 
			# http://man7.org/linux/man-pages/man5/proc.5.html
			values = ('', g.group(1), g.group(2), g.group(3)) + tuple(g.group(4).split())

			p_pid    = int(values[1])
			p_user   = int(values[14])
			p_system = int(values[15])
			p_cpu    = int(values[39])
			results['processes'][p_pid] = { 'name': values[2], 'user': p_user, 'system': p_system, 'last_cpu': p_cpu, 'last_state': values[3] }

		return results
	
	def diff(self, old_results, current_results):
		# overall
		overall = {
			'user'  : (current_results['global']['user']+current_results['global']['nice']) - (old_results['global']['user']+old_results['global']['nice']),
			'system': (current_results['global']['system']) - (old_results['global']['system']),
			'idle': (current_results['global']['idle']) - (old_results['global']['idle']),
			'iowait': (current_results['global']['iowait']) - (old_results['global']['iowait']),
			'irq': (current_results['global']['irq']) - (old_results['global']['irq']),
			'softirq': (current_results['global']['softirq']) - (old_results['global']['softirq']),
		}

		difftime = current_results['time'] - old_results['time']
		
		# per process
		processes = {}
		for pid in current_results['processes'].keys():
			if pid not in old_results['processes']: continue

			processes[pid] = {
				'name'       : current_results['processes'][pid]['name'],
				'last_cpu'   : current_results['processes'][pid]['last_cpu'],
				'last_state' : current_results['processes'][pid]['last_state'],
				'user'       : current_results['processes'][pid]['user'] - old_results['processes'][pid]['user'],
				'system'     : current_results['processes'][pid]['system'] - old_results['processes'][pid]['system'],
			}


		return (overall, processes, difftime)
