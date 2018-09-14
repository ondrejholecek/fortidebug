#!/usr/bin/env python2.7

import os

# to be able to import our modules from the directory above
os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.Signature import Signature, SigException
import argparse
import sys
import getpass

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')

parser_generate = subparsers.add_parser('generate', help='Generate new keys')
parser_generate.add_argument('--keylen', type=int, default=4096, help='RSA key length, default 4096')
parser_generate.add_argument('--public', required=True, help='File to save the public key')
parser_generate.add_argument('--private', required=True, help='File to save the private key')

parser_sign = subparsers.add_parser('sign', help='Create file signature')
parser_sign.add_argument('--file', required=True, help='File to be signed')
parser_sign.add_argument('--signature', required=True, help='File where the signature is saved')
parser_sign.add_argument('--private', required=True, help='Private key to use for signature')

parser_verify = subparsers.add_parser('verify', help='Verify file signature')
parser_verify.add_argument('--file', required=True, help='File to be verified')
parser_verify.add_argument('--signature', required=True, help='File with signature')
parser_verify.add_argument('--public', required=True, help='Public key to use for verifying')

def do():
	args = parser.parse_args()
	
	if args.command == 'generate':
		passphrase = getpass.getpass("Private key passphrase: ")
		if len(passphrase) == 0:
			print "Warning: Not encrypting the private key"
			passphrase = None
		else:
			tmp = getpass.getpass("Repeat the private key passphrase: ")
			if tmp != passphrase:
				print "Error: Passphrases do not match!"
				sys.exit(1)
	
		s = Signature()
		s.generate_keys(args.keylen)
		s.export_public_key(args.public)
		s.export_private_key(args.private, passphrase)
	
		print "Public key saved to %s" % (args.public,)
		print "Private key saved to %s" % (args.private,)
		sys.exit(0)
	
	elif args.command == 'sign':
		passphrase = getpass.getpass("Private key passphrase: ")
		if len(passphrase) == 0:
			passphrase = None
		
		s = Signature(private_key_file=args.private, passphrase=passphrase)
		signature = s.sign(open(args.file, "rb").read())
		open(args.signature, "wb").write(signature+"\n")
		print "File %s signed into %s" % (args.file, args.signature,)
		sys.exit(0)
	
	elif args.command == 'verify':
		s = Signature(public_key_file=args.public)
		signature = open(args.signature, "rb").read()
		
		if s.verify(open(args.file, "rb").read(), signature):
			print "Signature of file %s is valid" % (args.file,)
			sys.exit(0)
		else:
			print "Invalid signature"
			sys.exit(1)

try:
	do()
except SigException, e:
	print str(e)
	sys.exit(10)
