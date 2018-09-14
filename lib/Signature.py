from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA512, SHA384, SHA256
from Crypto import Random
from base64 import b64encode, b64decode

class SigException(Exception): pass

class Signature:
	HASH_ALG_SHA_512 = "sha512"
	HASH_ALG_SHA_384 = "sha384"
	HASH_ALG_SHA_256 = "sha256"

	def __init__(self, public_key_file=None, private_key_file=None, passphrase=None, hash_alg=HASH_ALG_SHA_256):
		self.public_key = None
		if public_key_file != None:
			self.import_public_key(public_key_file)

		self.private_key = None
		if private_key_file != None:
			self.import_private_key(private_key_file, passphrase=passphrase)

		self.hash_alg    = hash_alg
	
	def import_public_key(self, public_key_file):
		self.public_key = RSA.importKey(open(public_key_file, "rb").read())

	def import_private_key(self, private_key_file, passphrase=None):
		try:
			self.private_key = RSA.importKey(open(private_key_file, "rb").read(), passphrase=passphrase)
		except ValueError:
			raise SigException("Error: invalid passphrase")

	def export_public_key(self, public_key_file):
		open(public_key_file, "wb").write(self.public_key.exportKey()+"\n")

	def export_private_key(self, private_key_file, passphrase=None):
		open(private_key_file, "wb").write(self.private_key.exportKey(passphrase=passphrase)+"\n")


	def generate_keys(self, keysize=4096):
		random_generator = Random.new().read
		key = RSA.generate(keysize, random_generator)
		(self.private_key, self.public_key) = (key, key.publickey())
		return (self.public_key, self.private_key)
	
	def sign(self, message):
		signer = PKCS1_v1_5.new(self.private_key)
		if (self.hash_alg == self.HASH_ALG_SHA_512):
			digest = SHA512.new()
		elif (self.hash_alg == self.HASH_ALG_SHA_384):
			digest = SHA384.new()
		elif (self.hash_alg == self.HASH_ALG_SHA_256):
			digest = SHA256.new()
		else:
			raise Exception("Unknown hash algorithm '%s'" % (self.hash_alg,))

		digest.update(message)
		return b64encode(signer.sign(digest))
	
	def verify(self, message, signature):
		signer = PKCS1_v1_5.new(self.public_key)
		if (self.hash_alg == self.HASH_ALG_SHA_512):
			digest = SHA512.new()
		elif (self.hash_alg == self.HASH_ALG_SHA_384):
			digest = SHA384.new()
		elif (self.hash_alg == self.HASH_ALG_SHA_256):
			digest = SHA256.new()
		else:
			raise Exception("Unknown hash algorithm '%s'" % (self.hash_alg,))

		digest.update(message)
		return signer.verify(digest, b64decode(signature))
