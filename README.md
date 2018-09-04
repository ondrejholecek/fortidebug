# FortiMonitor

This is a set of utilities to make FortiGate troubleshooting easier. 

The project consists of 4 parts:
- Wrapper around [Paramiko](http://www.paramiko.org/) to correctly communicate with FortiGate over SSH. 
- Output parsers for different commands to present the outputs in a form that is further usable in programs.
- Definiton of different FortiGate models that is needed by some utilities (e.g. NIC to NP mapping).
- Utilities that use both of the previous parts to merge and present the collected outputs in a human friendly form.

At this moment the utilities should work on any Mac and Linux with python2.7. Testing on Windows 10 is planned.

## Usage

Basicaly all the programs you may want to use are located in "utilities" directory. All of them accept "-h" parameter
to display the options that can be used. Following options are shared by most of the programs:

```
--host HOST           FortiGate hostname or IP address
--user USER           User name to log in as, default "admin"
--password PASSWORD   Password to log in with, default empty
--credfile CREDFILE   File to read the credentials from 
--port PORT           SSH port, default 22
--time-format {human-with-offset,human,timestamp,iso}  Format of the date and time
--time-source {device,local}                           How to retrieve data and time
--debug               Enable debug outputs
--manual              Show manual
--ignore-ssh-key      Ignore SSH server key problems
```

### Logging in 
You can either provide the username and password on command line with parameters "--user" and "--password" or you can
save them in a file and use "--credfile" option. The file should consist of two lines, the first one being the username 
and the second the password.

### Timestamps
Most of the programs automatically prepend every output line with a timestamp to make it easy to save the output into a text
file and analyze it later. 

By default, the timestamp is printed in human readable format with the timezone offset (e.g. "2018-09-04 11:33:27+02:00") but
it can be changed using "--time-format" parameter to the humand readable without offset or a unix timestamp which is better
usable in subsequent scripts.

The time on the FortiGate device is used by default and the timezone is calculated based on the different from the local
time on your computer (that means the local computer time must be correct). Alternatively you can choose to use local time
directly with the "--time-source" option. 

### Security
The programs expect that the public SSH key of the FortiGate is already present in the "known hosts" file (that happens when
you connect to the FortiGate for first time using the standard SSH client. If you don't care about the remote key validity
the "--ignore-ssh-key" parameter can be used.

### More options
There are another parameters that vary depending on what program you are running. All utilities accept "-h" option that show
both the shared and the local options.

Some utilities also accept "--manual" parameter which prints a more detailed information about the utility.


## Utilities

### continuous_command.py

Runs a specific command every x seconds. If VDOMs are enabled on the unit, you can choose whether to run this command 
in "global" context or in a specific VDOM context. If you don't care about the specific VDOM, you can run it in a
management vdom.

You can also use the "--grep" option to only display lines matching the regular expression.

```
$ ./continuous_command.py --host 10.0.0.1 --cycle-time 10 --command "get sys perf stat" --grep '^Memory:|^CPU states:'
[2018-09-04 12:04:13+02:00] (get_sys_perf_stat) CPU states: 0% user 1% system 0% nice 99% idle 0% iowait 0% irq 0% softirq
[2018-09-04 12:04:13+02:00] (get_sys_perf_stat) Memory: 16449724k total, 3191696k used (19%), 13258028k free (81%)
[2018-09-04 12:04:23+02:00] (get_sys_perf_stat) CPU states: 0% user 0% system 0% nice 100% idle 0% iowait 0% irq 0% softirq
[2018-09-04 12:04:23+02:00] (get_sys_perf_stat) Memory: 16449724k total, 3191796k used (19%), 13257928k free (81%)
```

### continuous_mpstat.py

The same as the "diagnose sys mpstat" on FortiGate, but prefix each line with the timestamp to make it easier to
process for subsequent scripts.

```
$ ./continuous_mpstat.py --host 10.0.0.1
[2018-09-04 12:07:44+02:00] (mpstat) TIME        CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal   %idle
[2018-09-04 12:07:44+02:00] (mpstat) 12:07:44 PM all    0.00    0.00    0.91    0.00    0.00    0.00    0.00   99.09
[2018-09-04 12:07:44+02:00] (mpstat)               0    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
[2018-09-04 12:07:44+02:00] (mpstat)               1    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
[...]
[2018-09-04 12:07:44+02:00] (mpstat)
[2018-09-04 12:07:45+02:00] (mpstat) TIME        CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal   %idle
[2018-09-04 12:07:45+02:00] (mpstat) 12:07:45 PM all    0.00    0.00    1.57    0.00    0.00    0.00    0.00   98.43
[2018-09-04 12:07:45+02:00] (mpstat)               0    0.00    0.00    7.92    0.00    0.00    0.00    0.00   92.08
[2018-09-04 12:07:45+02:00] (mpstat)               1    0.00    0.00    0.00    0.00    0.00    0.00    0.00  100.00
[...]
```

### continuous_sessions_stat.py

The same as "diagnose sys session stat" and "diagnose sys session6 stat", but prefix each line with the timestamp to make it easier to
process for subsequent scripts.

```
$ ./continuous_sessions_stat.py --host 10.0.0.1
[2018-09-04 12:09:16+02:00] (ipv4) misc info:    session_count=10 setup_rate=1 exp_count=0 clash=0
[2018-09-04 12:09:16+02:00] (ipv4)      memory_tension_drop=0 ephemeral=0/1114112 removeable=0
[2018-09-04 12:09:16+02:00] (ipv4)      npu_session_count=0
[2018-09-04 12:09:16+02:00] (ipv4)      nturbo_session_count=0
[2018-09-04 12:09:16+02:00] (ipv4) delete=0, flush=0, dev_down=95/297 ses_flush_filters=0
[...]
[2018-09-04 12:09:16+02:00] (ipv6) misc info:    session_count=1 setup_rate=0 exp_count=0 clash=0
[2018-09-04 12:09:16+02:00] (ipv6)      memory_tension_drop=0 ephemeral=0/0 removeable=0
[2018-09-04 12:09:16+02:00] (ipv6)      npu_session_count=0
[2018-09-04 12:09:16+02:00] (ipv6)      nturbo_session_count=0
[2018-09-04 12:09:16+02:00] (ipv6) delete=0, flush=0, dev_down=0/0 ses_flush_filters=0
[...]
```

### stack_dump.py

This one prints the current stack trace (exact part of the code which is being executed) for a specific program every x seconds. 

If there are multiple processes of the same name, the stack dump is printent for all of them.

```
$ ./stack_dump.py --host 10.0.0.1 --process-name miglogd
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff80382734>] rb_insert_color+0xa4/0x140
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff80385001>] timerqueue_add+0x61/0xb0
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff80278c60>] enqueue_hrtimer+0x20/0x50
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff802790bb>] __hrtimer_start_range_ns+0xfb/0x1c0
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff80278c10>] hrtimer_wakeup+0x0/0x30
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff80300a83>] ep_poll+0x2c3/0x340
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff80256610>] default_wake_function+0x0/0x10
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff80301664>] sys_epoll_wait+0xc4/0xf0
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffff8059993b>] system_call_fastpath+0x16/0x1b
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S) [<ffffffffffffffff>] 0xffffffffffffffff
[2018-09-04 12:12:55+02:00] ('/bin/miglogd':237:S)
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S) [<ffffffff802509db>] update_rq_clock+0x2b/0xe0
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S) [<ffffffff8025357d>] task_sched_runtime+0x4d/0x90
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S) [<ffffffff80277216>] thread_group_cputime+0x76/0xb0
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S) [<ffffffff8025c6c1>] do_syslog+0x571/0x610
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S) [<ffffffff80275c20>] autoremove_wake_function+0x0/0x30
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S) [<ffffffff8025c76b>] sys_syslog+0xb/0x20
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S) [<ffffffff8059993b>] system_call_fastpath+0x16/0x1b
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S) [<ffffffffffffffff>] 0xffffffffffffffff
[2018-09-04 12:12:55+02:00] ('/bin/kmiglogd':239:S)
[...]
```

### processes_on_cpu.py

This program displays the processes running on each CPU (core).

Be aware that the processes can jump between different cores during their lifetime, and this collects the actual status 
only once per `--cycle-time`, hence this is not very accurate.

However, it can be used to identify the process occupying the specific core all the time.

```
$ ./processes_on_cpu.py --host 10.0.0.1
[2018-09-04 12:15:49+02:00] CPU#0: 'initXXXXXXXXXXX'[S](1) 'ksoftirqd/0'[S](3) 'migration/0'[S](6) 'watchdog/0'[S](7) 'kworker/0:1'[S](11) 'sync_supers'[S](59) 'scsi_eh_0'[S](127) 'scsi_eh_1'[S](128) 'scsi_eh_2'[S](129) 'scsi_eh_3'[S](130) 'bcm-shell'[S](196) 'kjournald'[S](209) 'zebos_launcher'[S](225) 'ripd'[S](227) 'fnbamd'[S](245) 'forticron'[S](250) 'foauthd'[S](251) 'ntpd'[S](258) 'dnsproxy'[S](263) 'wpad_ac'[S](268) 'cu_acd'[S](270) 'authd2'[S](291) 'kworker/0:2'[S](2594) 'sshd'[S](2770) 'sshd'[R](2808)
[2018-09-04 12:15:49+02:00] CPU#1: 'migration/1'[S](8) 'kworker/1:0'[S](9) 'ksoftirqd/1'[S](10) 'watchdog/1'[S](12) 'kworker/1:1'[S](56) 'pyfcgid'[S](277)
[2018-09-04 12:15:49+02:00] CPU#2: 'migration/2'[S](13) 'ksoftirqd/2'[S](15) 'watchdog/2'[S](16) 'kworker/2:1'[S](55) 'np6_0'[S](203) 'nsm'[S](226) 'httpsd'[S](240) 'getty'[S](242) 'merged_daemons'[S](244) 'forticldd'[S](248) 'dhcpd'[S](256) 'acd'[S](257) 'sshd'[S](259) 'fgfmd'[S](266) 'authd5'[S](294) 'kworker/2:2'[S](385) 'kworker/u:0'[S](2676) 'kworker/u:1'[S](2778) 'newcli'[S](2811)
```

### ipsec_gateways.py

Every x second this program parses the output of "diagnose vpn ike gateway list" and shows the changes.

You can filter by the direction of the VPN (i.e. whether the FortiGate you are querying is the "initiation" or "reponder") 
with the "--direction" option. Or you can filter by the phase1 status (ie. "established" or "connecting") with the "--status"
option.

```
$ ./ipsec_gateways.py --host 10.0.0.1
[2018-09-04 12:26:19+02:00] (ikegw) {new}     root             Lab-Xxxxxx           abxxxxxxxxxxxx34/65xxxxxxxxxxxxe6  1.2.3.4:500      -> 2.2.2.2:500          initiator    established     483618
[2018-09-04 12:26:19+02:00] (ikegw) {new}     root             Priv_xxxxx           22xxxxxxxxxxxxd7/abxxxxxxxxxxxx18  1.2.3.4:500      -> 3.3.3.3:500          responder    established     409238

[2018-09-04 12:27:04+02:00] (ikegw) {new}     root             Priv_xxxxx           43xxxxxxxxxxxxa3/7cxxxxxxxxxxxxfd  1.2.3.4:500      -> 3.3.3.3:500          responder    established          0
[2018-09-04 12:27:04+02:00] (ikegw) {deleted} root             Priv_xxxxx           22xxxxxxxxxxxxd7/abxxxxxxxxxxxx18  1.2.3.4:500      -> 3.3.3.3:500          responder    established     409238
```

### ipsec_ikesa_ipsecsa_counts.py

This one parses "diagnose vpn ike stats" output every x seconds and displays the number of new or deleted SAs for phases1
or phases2.

```
$ ./ipsec_ikesa_ipsecsa_counts.py --host 10.0.0.1
[2018-09-04 12:37:47+02:00] (vpnsa) IKE SAs: deleted     0 added     0, IPSEC SAs: deleted     3 added     1
[2018-09-04 12:38:27+02:00] (vpnsa) IKE SAs: deleted     0 added     0, IPSEC SAs: deleted     3 added     1
[2018-09-04 12:38:47+02:00] (vpnsa) IKE SAs: deleted     2 added     0, IPSEC SAs: deleted     2 added     0
[2018-09-04 12:38:52+02:00] (vpnsa) IKE SAs: deleted     0 added     1, IPSEC SAs: deleted     0 added     1
```

### cputop.py

This is very similar to FortiGate's "diagnose sys top" program, with following differencies:
- also the kernel threads are shown
- the cpu the process was last seen running on is shown
- cpu utilization is split between "kernel" and "userland" utilization for each process
- it displays the "global" utilization (percentage of all possible CPU ticks)
- and it also displays "of counsumed" utilization (percentage out of the running processes)
- it **does not** display any memory statistics

Different sorting algorithms can be applied (see help for "--sort-by" option).

It is possible to only shown the processes in the specific state (see help for "--state" option),
or processes running on a specific CPU (see help for "--cpu" option).

```
$ ./cputop.py --host 10.0.0.1
[2018-09-04 12:41:36+02:00] (pcpu) Overall CPU utilization: 9.7 % user, 20.1 % system, 1159.9 % idle
[2018-09-04 12:41:36+02:00] (pcpu) Overall CPU utilization: 0.0 % iowait, 0.7 % irq, 1.4 % softirq
[2018-09-04 12:41:36+02:00] (pcpu) Applied filters: TOP[25] SORT[total]
[2018-09-04 12:41:36+02:00] (pcpu)                                  OF CONSUMED      GLOBAL
[2018-09-04 12:41:36+02:00] (pcpu)    PID NAME             STATE   USER  SYSTEM    USER  SYSTEM  CPU#
[2018-09-04 12:41:36+02:00] (pcpu)    201 np6_0                S    0.0    34.5     0.0     6.9     2
[2018-09-04 12:41:36+02:00] (pcpu)    202 np6_1                S    0.0    34.5     0.0     6.9     0
[2018-09-04 12:41:36+02:00] (pcpu)    257 snmpd                S    0.0    27.6     0.0     5.6     6
[2018-09-04 12:41:36+02:00] (pcpu)  11998 newcli               S   21.4     3.4     2.1     0.7     4
[2018-09-04 12:41:36+02:00] (pcpu)  11995 sshd                 R   14.3     6.9     1.4     1.4     2
[2018-09-04 12:41:36+02:00] (pcpu)    200 bcmLINK.0            S    0.0    13.8     0.0     2.8     4
[2018-09-04 12:41:36+02:00] (pcpu)    260 hasync               S    0.0     3.4     0.0     0.7     0
[2018-09-04 12:41:36+02:00] (pcpu)    328 ipsengine            S    0.0     3.4     0.0     0.7    10
[2018-09-04 12:41:36+02:00] (pcpu)      1 initXXXXXXXXXXX      S    0.0     0.0     0.0     0.0     8
[...]
```

### nic_utilization.py

This program collects the traffic counters from network interfaces. By default it only shows the interface in the
up state, but it can be changed with "--all-ifaces" option or by pressing the 'a' key (and enter).

It collects the "front port" counters ("wire" counters on the incoming ports), npu counters (traffic hitting the NPU)
and the kernel counters (traffic that is not offloaded). By default all counters are shown and they can be enabled/disabled
by pressing 'f', 'n' or 'k' keys (and enter). All bandwidth counters are shown in the relevant units and the program
uses the SI to calculate them (i.e. dividing by 1000 **not** by 1024 !).

Be aware that on some models the NPU lanes are shared. This program displays the NPU column for each interface,
but in case of shared lanes the same counter will be displayed for all the relevant interfaces.

There are also drop counters collected. Visibility of this field can be enabled/disabled with 'd' key. Similar to NPU counters,
the drop counters are disabled for each interface, but they are collected for the whole NPU, hence the numbers will be the same
for all the ports on the same NPU. Unlike others, these counters are not averaged per second, but intestat the total number
of drops is shown. Drop counters can be zeroed with 'z' key.

**This program needs a definition of ports used by each platform.** It is quite possible that your platform is not yet supported,
but it should not be a problem to add the right definition - just create an "issue" here.

If you are running this program with the output redirected to file, you most probably want to use "--show-timestamp" 
and "--no-colors" options.

```
$ ./nic_utilization.py --host 10.0.0.1
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Interface      Speed |                   Front port                    |                       NPU                       |                     Kernel                      |   Offloaded %   |     NPU Drops (sum)     |
                     | Rx packets       Rx bps Tx packets       Tx bps | Rx packets       Rx bps Tx packets       Tx bps | Rx packets       Rx bps Tx packets       Tx bps | RxP RxB TxP TxB |     dce     hrx anomaly |
mgmt1           1000 |         67     42.22 kb         54    244.35 kb |        ---          ---        ---          --- |         67     42.22 kb         54    244.35 kb |   0   0   0   0 |     ---     ---     --- |
port17          1000 |      16794     10.35 mb      27700    315.69 mb |      37308     24.14 mb      17456     11.34 mb |          0        336 b          0          0 b | 100 100 100 100 |       0       0       0 |
port18          1000 |      42803     26.25 mb      76256    896.01 mb |      23180     14.95 mb      43029     27.75 mb |          0        336 b          0          0 b | 100 100 100 100 |       0       0       0 |
port25          1000 |      27612    316.29 mb      16959     10.47 mb |      63850    741.31 mb      28443    324.92 mb |          1        440 b          0          0 b | 100 100 100 100 |       0       0       0 |
port38         10000 |      76330    895.01 mb      42663     26.15 mb |      41594    490.89 mb      77035      0.91 gb |          1        720 b          0          0 b | 100 100 100 100 |       0       0       0 |
```
