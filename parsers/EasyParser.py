
class EasyParser:
	def __init__(self, sshc):
		self.sshc = sshc

		self.prepare()
	
	def set_local_param(self, name, value):
		self.sshc.set_local_param(name, value)
	
	def get_local_param(self, name):
		return self.sshc.get_local_param(name)

	def prepare(self):
		pass
	
	def get(self):
		raise Exception("Function get must be implemented by parser")
	
	def simple_value(self, result, name):
		raise Exception("Function get must be implemented by parser")
