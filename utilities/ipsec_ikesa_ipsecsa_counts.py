#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.CurrentTime import ParserCurrentTime
from parsers.GenericLineSplit import ParserGenericLineSplit
from _common import ssh, cycle, prepend_timestamp

sshc, args = ssh([
	{ 'name':'--cycle-time', 'type':int, 'default':5,  'help':'How long should each cycle take' },
	{ 'name':'--show-raw', 'action':'store_true', 'default':False,  'help':'Show also raw counters values' },
])

def do(sshc, info, show_raw):
	etime = ParserCurrentTime(sshc).get()
	
	s = ParserGenericLineSplit(sshc).get("\s*:\s*", "diag vpn ike stats", vdom="", key_index=0, value_index=1, value_type=int)
	ikesa_add   = s['ha.ike.sa.add.tx.queued']
	ikesa_del   = s['ha.ike.sa.del.tx']
	ipsecsa_add = s['ha.ipsec.sa.add.tx']
	ipsecsa_del = s['ha.ipsec.sa.del.tx']

	if 'ikesa_add' in info and 'ikesa_del' in info: 
		prev_ike_add = info['ikesa_add']
		prev_ike_del = info['ikesa_del']
		prev_ipsec_add = info['ipsecsa_add']
		prev_ipsec_del = info['ipsecsa_del']

		diff_ike_add = ikesa_add - prev_ike_add
		diff_ike_del = ikesa_del - prev_ike_del
		diff_ipsec_add = ipsecsa_add - prev_ipsec_add
		diff_ipsec_del = ipsecsa_del - prev_ipsec_del

		if diff_ike_add > 0 or diff_ike_del > 0 or diff_ipsec_add > 0 or diff_ipsec_del > 0:
			if show_raw:
				print prepend_timestamp("IKE SAs: deleted %5i added %5i (raw deleted %8i added %8i), IPSEC SAs: deleted %5i added %5i (raw deleted %8i added %8i)" % (
					diff_ike_del, diff_ike_add,
					ikesa_del, ikesa_add,
					diff_ipsec_del, diff_ipsec_add,
					ipsecsa_del, ipsecsa_add,
				), etime, 'vpnsa')
			else:
				print prepend_timestamp("IKE SAs: deleted %5i added %5i, IPSEC SAs: deleted %5i added %5i" % (
					diff_ike_del, diff_ike_add,
					diff_ipsec_del, diff_ipsec_add,
				), etime, 'vpnsa')
	
	info['ikesa_add'] = ikesa_add
	info['ikesa_del'] = ikesa_del
	info['ipsecsa_add'] = ipsecsa_add
	info['ipsecsa_del'] = ipsecsa_del


if __name__ == '__main__':
	try:
		info = {}

		cycle(do, {
			'sshc': sshc, 
			'info': info,
			'show_raw': args.show_raw,
		}, args.cycle_time, debug=args.debug)
	except KeyboardInterrupt:
		sshc.destroy()

