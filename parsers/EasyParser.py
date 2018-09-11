
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
	
	# Return:
	# - simple list - each element can be assign to one variable in foreach cycle
	# - list of tuples - in foreach cycle each element of the inner tuple will be
	#                    assigned to its variable in each iteration 
	def simple_value(self, result, name):
		raise Exception("Function get must be implemented by parser")
