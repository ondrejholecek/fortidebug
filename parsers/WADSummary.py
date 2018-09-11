from EasyParser import EasyParser

import re

# Process [0]: WAD manager type=manager(0) pid=23647 diagnosis=yes.
# Process [1]: type=dispatcher(1) index=0 pid=23650 state=running
#               diagnosis=no debug=enable valgrind=unsupported/disabled
# Process [2]: type=wanopt(2) index=0 pid=23651 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [3]: type=worker(3) index=0 pid=23652 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [4]: type=worker(3) index=1 pid=23653 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [5]: type=worker(3) index=2 pid=23654 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [6]: type=worker(3) index=3 pid=23655 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [7]: type=worker(3) index=4 pid=23656 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [8]: type=worker(3) index=5 pid=23657 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [9]: type=worker(3) index=6 pid=23658 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [10]: type=worker(3) index=7 pid=23659 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [11]: type=worker(3) index=8 pid=23660 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [12]: type=worker(3) index=9 pid=23661 state=running
#               diagnosis=no debug=enable valgrind=supported/disabled
# Process [13]: type=informer(4) index=0 pid=23649 state=running
#               diagnosis=no debug=enable valgrind=unsupported/disabled
# [...]

class ParserWADSummary(EasyParser):
	def prepare(self):
		self.re_wad = re.compile("\s+type=(\S+)\((\d+)\)\s+(?:index=(\d+)\s+)?pid=(\d+)")

	def get(self):
 		stat = self.sshc.clever_exec("diagnose test application wad 1000")
		parts = self.re_wad.findall(stat)
		if len(parts) == 0:
			raise Exception("Cannot parse wad 1000")

		wads = []
		for part in parts:
			if len(part[2]) == 0: index=0
			else: index = int(part[2])

			wads.append({
				'type'   : part[0],
				'type_id': int(part[1]),
				'index'  : index,
				'pid'    : int(part[3]),
			})

		return wads

	def simple_value(self, result, name):
		if name == 'wad_contexts_workers':
			return [ ("2%i%02i" % (e['type_id'], e['index'],), e['pid']) for e in result if e['type'] in ('worker', 'wanopt')]
		elif name == 'wad_contexts_managers':
			return [ ("2%i%02i" % (e['type_id'], e['index'],), e['pid']) for e in result if e['type'] in ('manager')]
		elif name == 'wad_contexts_dispatchers':
			return [ ("2%i%02i" % (e['type_id'], e['index'],), e['pid']) for e in result if e['type'] in ('dispatcher')]
		elif name == 'wad_contexts_informers':
			return [ ("2%i%02i" % (e['type_id'], e['index'],), e['pid']) for e in result if e['type'] in ('informer')]

		else:
			raise Exception("Unknown simple value name")
