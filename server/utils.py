import random
from math import floor
from os import path
from config import FILE_DIR

# Generate n random bytes
def random_bytes(n):
	# Initialise an empty array
	buf = bytearray()
	
	# Loop n times
	for _ in range(n):
		# Add a random byte
		buf.append(floor(random.random() * 255))

	# Return the array
	return buf

# Generate a random string, used for challenges and invite codes
def random_string(n):
	ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	return "".join([ALPHABET[floor(random.random() * len(ALPHABET))] for _ in range(n)])

# Returns true if dict has all keys in keys
def has_keys(dict, keys):
	for key in keys:
		if key not in dict.keys():
			return False
	return True

# Return the path to the archival file.
# filename identifies the file, created_at and username identifies the history statement
# which this file is representative of
def archive_filename(filename, created_at, username):
	return path.join(FILE_DIR, "%s-%s-%s" % (filename, created_at, username))