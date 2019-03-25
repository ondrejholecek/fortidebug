import bz2
import datetime
import json
import sys

class ScriptFile:
	def __init__(self, filename=None, compressed=True):
		self.filename   = filename
		self.compressed = compressed

		if self.filename == None:
			self.input = sys.stdin
		else:
			self.input = open(self.filename, "rb")

		if self.compressed:
			self.readline = self.readline_bz2
		else:
			self.readline = self.readline_plain

		self.decom = None
		self.decom_rest = ""
		self.decom_buf  = ""

	def readline_bz2(self):
		last = False

		while True:
			# if we have some lines in the buffer, process it with priority
			nl = self.decom_buf.find("\n")
			if nl != -1:
				line = self.decom_buf[:nl]
				self.decom_buf = self.decom_buf[nl+1:]
				return line

			# otherwise decompress more
			chunk = self.input.read(1024)
			if len(chunk) == 0 and len(self.decom_rest) == 0:
				last = True

			else:
				if self.decom == None:
					self.decom = bz2.BZ2Decompressor()
					if len(self.decom_rest) > 0:
						tmp = self.decom.decompress(self.decom_rest)
						if len(tmp) > 0: self.decom_buf += tmp
						self.decom_rest = ""
		
				try:
					tmp = ""
					tmp = self.decom.decompress(chunk)
				except EOFError:
					self.decom_rest = self.decom.unused_data + chunk
					self.decom = None
		
				if len(tmp) > 0: self.decom_buf += tmp

			if last: 
				if len(self.decom_rest) > 0:
					continue
				else:
					break

		if last:
			return None
		
	def readline_plain(self):
		line = self.input.readline()
		if len(line) == 0: return None

		while line[-1] in ('\r', '\n'):
			line = line[:-1]

		return line

	def next(self):
		chunk = self.readline()
		if chunk == None: 
			return None

		obj   = json.loads(chunk)
		return obj

