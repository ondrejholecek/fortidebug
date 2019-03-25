from EasyParser import EasyParser

import re
import datetime

# exe date
# ---
# current date is: 2018-08-01

# exe time
# ---
# current time is: 15:05:43
# last ntp sync:Wed Aug  1 14:58:13 2018

class TZoffset(datetime.tzinfo):
	def __init__(self, seconds_from_utc, name):
		self.offset = seconds_from_utc
		self.name   = name
	
	def utcoffset(self, dt):
		return datetime.timedelta(seconds=int(round(float(self.offset)/60))*60)

	def dst(self, dt):
		return datetime.timedelta(0)
	
	def tzname(self, dt):
		return self.name

class OurDatetime():
	def __init__(self, dt, time_format, time_source):
		self.dt               = dt
		self.time_format = time_format
		self.time_source      = time_source

	def __str__(self):
		if self.time_format == 'human-with-offset':
			return str(self.dt)

		elif self.time_format == 'human':
			return str(self.dt.replace(tzinfo=None))

		elif self.time_format == 'timestamp':
			return str(self.as_timestamp())

		elif self.time_format == 'iso':
			return self.dt.isoformat()

		else:
			return "UnknownFormat"

	def as_timestamp(self):
		return int((self.dt - datetime.datetime(1970, 1, 1, 0, 0, 0, 0, TZoffset(0, "utc"))).total_seconds())
	
	def as_datetime(self):
		return self.dt
	
	def get_offset(self):
		return int(self.dt.tzinfo.utcoffset(self.dt).total_seconds()/60)	

	def replace(self, year=None, month=None, day=None, hour=None, minute=None, second=None, microsecond=None, tzinfo=None):
		if year == None: n_year = self.dt.year
		else: n_year = year
		if month == None: n_month = self.dt.month
		else: n_month = month
		if day == None: n_day = self.dt.day
		else: n_day = day
		if hour == None: n_hour = self.dt.hour
		else: n_hour = hour
		if minute == None: n_minute = self.dt.minute
		else: n_minute = minute
		if second == None: n_second = self.dt.second
		else: n_second = second
		if microsecond == None: n_microsecond = self.dt.microsecond
		else: n_microsecond = microsecond
		if tzinfo == None: n_tzinfo = self.dt.tzinfo
		else: n_tzinfo = tzinfo

		return OurDatetime(datetime.datetime(n_year, n_month, n_day, n_hour, n_minute, n_second, n_microsecond, n_tzinfo), self.time_format, self.time_source)
	
	def __add__(self, delta):
		return OurDatetime(self.dt + delta, self.time_format, self.time_source)

	def __sub__(self, other):
		return self.math(other, '-')

	def __eq__(self, other):
		return self.math(other, '==')

	def __ne__(self, other):
		return self.math(other, '!=')

	def __ge__(self, other):
		return self.math(other, '>=')

	def __gt__(self, other):
		return self.math(other, '>')

	def __le__(self, other):
		return self.math(other, '<=')

	def __lt__(self, other):
		return self.math(other, '<')

	def math(self, other, operation):
		a   = self.dt
		b   = other.dt

		if a.tzinfo == None: a = a.replace(tzinfo = b.tzinfo)
		if b.tzinfo == None: b = b.replace(tzinfo = a.tzinfo)

		if operation == '-':
			return a-b
		elif operation == '==':
			return a==b
		elif operation == '!=':
			return a!=b
		elif operation == '>=':
			return a>=b
		elif operation == '>':
			return a>b
		elif operation == '<=':
			return a<=b
		elif operation == '<':
			return a<b

class ParserCurrentTime(EasyParser):
	def prepare(self):
		self.re_date = re.compile("current date is: (\d+)-(\d+)-(\d+)")
		self.re_time = re.compile("current time is: (\d+):(\d+):(\d+)")

	def get(self):
		time_format = self.get_local_param('args').time_format
		time_source = self.get_local_param('args').time_source
		time_offset = self.get_local_param('time_offset_seconds')

		if time_source == 'device':
			dt_with_offset = OurDatetime(self.get_from_device(time_offset), time_format, time_source)
		elif time_source == 'local':
			dt_with_offset = OurDatetime(self.get_from_local(time_offset), time_format, time_source)

		return dt_with_offset

	def get_from_device(self, time_offset=None):
		o_date = self.sshc.clever_exec("exe date")
		g = self.re_date.search(o_date)
		if not g:
			raise Exception("Cannot parse date output")

		d_year  = int(g.group(1))
		d_month = int(g.group(2))
		d_day   = int(g.group(3))

		o_time = self.sshc.clever_exec("exe time")
		g = self.re_time.search(o_time)
		if not g:
			raise Exception("Cannot parse time output")

		d_hour   = int(g.group(1))
		d_minute = int(g.group(2))
		d_second = int(g.group(3))

		dt = datetime.datetime(d_year, d_month, d_day, d_hour, d_minute, d_second)

		if time_offset == None:
			now = datetime.datetime.utcnow().replace(microsecond=0)
			dt_with_offset = dt.replace(tzinfo=TZoffset((dt-now).total_seconds(), 'device'))
			return dt_with_offset

		else:
			dt_with_offset = dt.replace(tzinfo=TZoffset(time_offset, 'device'))
			return dt_with_offset

	def get_from_local(self, time_offset=None):
		now     = datetime.datetime.now().replace(microsecond=0)

		if time_offset == None:
			now_utc = datetime.datetime.utcnow().replace(microsecond=0)
			dt_with_offset = now.replace(tzinfo=TZoffset((now-now_utc).total_seconds(), 'local'))
			return dt_with_offset

		else:
			dt_with_offset = now.replace(tzinfo=TZoffset(time_offset, 'local'))
			return dt_with_offset
