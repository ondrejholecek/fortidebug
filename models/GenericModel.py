class NICCounters:
	SRC_HWNIC   = 'hwnic'
	SRC_NP6_PORTSTATS = 'np6_portstats'

	SPD_IFACE  = 'iface'
	SPD_S1G    = '1G'
	SPD_S10G   = '10G'

	def __init__(self, source, counter, maxspeed):
		self.source = source
		self.counter = counter
		self.maxspeed = maxspeed

class NICDrops:
	SRC_NP6_DROPS = 'np6drops'

	def __init__(self, source, npuid):
		self.source = source
		self.npuid  = npuid

class GenericModel:
	def __init__(self):
		self.ports = {}

		self.init()
	
	def init(self):
		pass

	def add_port(self, name, front, npu, kernel, npudrops):
		self.ports[name] = {
			'front'   : front,
			'npu'     : npu,
			'kernel'  : kernel,
			'npudrops': npudrops,
		}

def GetModelSpec(serial):
	if serial[:6] == 'FG1K5D':
		model = __import__('models.1500D', fromlist=['Model']).Model()
	elif serial[:6] == 'FG1K2D':
		model = __import__('models.1200D', fromlist=['Model']).Model()
	elif serial[:6] == 'FGT37D':
		model = __import__('models.3700D', fromlist=['Model']).Model()
	elif serial[:6] == 'FG5H0E':
		model = __import__('models.500E', fromlist=['Model']).Model()
	elif serial[:6] == 'FG5H1E':
		model = __import__('models.501E', fromlist=['Model']).Model()
	elif serial[:6] == 'FPM20E':
		model = __import__('models.7620E', fromlist=['Model']).Model()
	else:
		model = None
	
	return model
