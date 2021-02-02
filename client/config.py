from tkinter import messagebox as mb
from tkinter import simpledialog as sd

from pathlib import Path

import pickle
import base64
import sys

from aes import aesEncrypt, aesDecrypt
from hash import sha256
from rsa import RSAKeypair
from rsa.classes import PRIV_KEY_START

# Config format:
# serverBaseUrl		http://127.0.0.1/
# username			john_smith
# key 				-----
# key_is_encrypted	True
# local_files		[{
#  path 		C:\secrets
#  hashAcquired	---
#  prevHistoryStatement ---
# }]
class Config:
	def __init__(self, tk):
		# Get the path for the config
		self.config_path = Path.home().joinpath('securevcs.config')

		# Check if it exists
		if self.config_path.exists():
			# If so, try to load it
			try:
				with open(self.config_path, "rb") as f:
					self.load_config(f)

				self.is_valid = True
			except KeyError as _:
				# If something goes wrong, config is probably invalid
				self.is_valid = False
		else:
			# If it doesnt exist, mark that this config isn't valid
			self.is_valid = False

	# Load config from a file object
	def load_config(self, f):
		# Deserialise from pickle
		stored = pickle.load(f)

		# Load the basic details
		self.serverBaseUrl = stored['serverBaseUrl']
		self.username = stored['username']
		self.key_is_encrypted = stored['key_is_encrypted']
		self.key_raw = stored['key']

		# If encrypted
		if self.key_is_encrypted:
			# Get the decryption key from the user and decrypt it

			## Loop until we get the right key
			is_decrypted = False
			while not is_decrypted:
				## Ask the user for their password
				pword = sd.askstring("Public key is encrypted", "Please enter decryption key")

				## If they hit cancel, exit
				if pword == None:
					sys.exit(1)

				try:
					## Try decrypting with password
					key = sha256(bytearray(pword.encode('ascii')))
					decrypted = "".join([chr(x) for x in aesDecrypt(base64.b64decode(self.key_raw), key)])

					## Check if it has the banner to determine if its valid
					## (assert will raise an exception if this isn't true)
					assert decrypted[:len(PRIV_KEY_START)] == PRIV_KEY_START

					# If it's valid deserialise it
					self.key = RSAKeypair.deserialise(decrypted)

					# Show a success message
					mb.showinfo('Success!', 'Successfully decrypted private key.')

					# Break out the loop
					is_decrypted = True
				except Exception as e:
					# If decryption fails, show error and ask again
					mb.showerror('Invalid Decryption Key', 'Could not decrypt with that key. Please try again.')
		else:
			# If not decrypted, Deserialise it
			self.key = RSAKeypair.deserialise(self.key_raw)

		# Deserialise all the local files
		self.local_files = stored['local_files']

	# Populate the config with the given initial values
	def initial_setup(self, serverBaseUrl, username, key, encrypt_key, password=None):
		# Store the properties
		self.serverBaseUrl = serverBaseUrl
		self.username = username
		self.key_is_encrypted = encrypt_key
		self.local_files = []
		self.key = key

		if encrypt_key:
			# Encrypt the key if we need to

			## Get the encryption key from the password
			encryption_key = sha256(bytearray(password.encode('ascii')))

			## Serialise the keypair
			payload = bytearray(key.serialise().encode('ascii'))

			## Encrypt it
			encrypted = aesEncrypt(payload, encryption_key)

			## Store the encrypted one base64 encoded
			self.key_raw = base64.b64encode(encrypted).decode('ascii')
		else:
			# If it's not encrypted, just store it serialised
			self.key_raw = key.serialise()

		# Config is now guaranteed to be valid
		self.is_valid = True

	def save(self):
		# Don't try to save if we never finished setup
		if not self.is_valid:
			return

		# Open the file to save to
		# w+ overwrites or creates file
		with open(self.config_path, "w+b") as f:
			# pickle serialise everything and write it to the file
			pickle.dump({
				'serverBaseUrl': self.serverBaseUrl,
				'username': self.username,
				'key': self.key_raw,
				'key_is_encrypted': self.key_is_encrypted,
				'local_files': self.local_files
			}, f)

	def add_local_file(self, local_file):
		# TODO: Don't duplicate paths
		self.local_files.append(local_file)

class LocalFile:
	def __init__(self, file_id, path, hashAcquired, prevHistoryStatement):
		self.id = file_id
		if not isinstance(path, Path):
			self.path = Path(path)
		else:
			self.path = path
		self.hashAcquired = hashAcquired
		self.prevHistoryStatement = prevHistoryStatement

	def __str__(self):
		return "<LocalFile at %s>" % self.path