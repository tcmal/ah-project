from math import ceil
from hash import sha256
from secrets import randbelow
import numpy as np
import base64

# Size of output from hash_bytearray (bytes)
HASH_FUNCTION_SIZE = 32

# Total size of padded blocks (bytes)
BLOCK_SIZE = 64

# How much actual data can be in one padded block (bytes)
BLOCK_MSG_SIZE = BLOCK_SIZE // 2

# The size of each padded block after encryption (bytes)
# Same as the size of n
ENCRYPTED_BLOCK_SIZE = 512

# Encrypt/Sign bytearray M using private or public key (e, n)
# Returns a string
def encrypt(M, e, n):
	M = M.copy() # So we don't modify the caller's copy
	
	# Get Hash = Hash of data
	orig_hash = hash_bytearray(M)

	# New data = data + Hash
	M += orig_hash

	# Get number of blocks
	num_blocks = ceil(len(M) / BLOCK_MSG_SIZE)

	# Encrypt each block

	## Generate random bytes (r)
	r = rand_bytes(BLOCK_MSG_SIZE)

	## G = Hash r
	G = hash_bytearray(r)

	## For each block
	encrypted = []
	for i in range(0, num_blocks):
		## Get the data for that block
		block = M[i * BLOCK_MSG_SIZE:(i + 1) * BLOCK_MSG_SIZE]

		## If there's not enough, pad with 0s
		while len(block) < BLOCK_MSG_SIZE:
			block.append(0)

		## Add padding to block
		padded = padding_add(block, r, G)

		## Encrypt the block
		enc = crypt_bytearray(padded, e, n, ENCRYPTED_BLOCK_SIZE)

		## Add it to the end of the encrypted message
		encrypted.extend(enc)

	# Base64 encode the whole message
	encoded = base64.b64encode(bytearray(encrypted))

	# Add banners around the message
	return (b"---SIGNED MESSAGE---\n" + encoded + b"\n---SIGNED MESSAGE---").decode('ascii')

# Decrypt string M with key (e, n)
# Returns bytearray or False if data is invalid
def decrypt(M, e, n):
	# Remove banners
	encoded = M.replace("\n", "").replace("---SIGNED MESSAGE---", "")

	# Base64 decode the message
	decoded = base64.b64decode(encoded)

	# Split message into blocks
	num_blocks = ceil(len(decoded) / ENCRYPTED_BLOCK_SIZE)
	
	# Decrypt each block
	r, G = (None, None)
	orig = []

	## For each block,
	for i in range(num_blocks):
		## Get the data for that block
		encrypted = decoded[i * ENCRYPTED_BLOCK_SIZE:(i+1) * ENCRYPTED_BLOCK_SIZE]

		## Decrypt it
		decrypted = crypt_bytearray(encrypted, e, n, BLOCK_SIZE)

		## If we haven't found r yet,
		if r == None:
			# Extract it
			r = extract_r(decrypted)

			# G = Hash r
			G = hash_bytearray(r)
		
		## Remove Padding from message and add to decrypted message
		orig.extend(remove_padding(decrypted, G))

	# Remove trailing 0s from message
	while orig[-1] == 0:
		orig.pop()

	# Check the hash at the end of the message
	
	## Get the hash from the message
	expected_hash = orig[-HASH_FUNCTION_SIZE:]

	## Hash the rest of the message
	orig = orig[:-HASH_FUNCTION_SIZE]
	actual_hash = hash_bytearray(orig)

	## Compare the two
	if np.array_equal(expected_hash, actual_hash):
		# If valid, return the rest of the message
		return orig
	else:
		# Otherwise, return False
		return False

# Add padding to a bytearray
def padding_add(block, r, G):
	# X = block ^ G
	X = xor_bytearrays(block, G)
	
	# H = Hash X
	H = hash_bytearray(X)

	# Y = H ^ r
	Y = xor_bytearrays(H, r)
	
	# Return X concat Y
	return X + Y

# Accepts a bytearray and runs RSA on it as a BE integer
# Returns a bytearray of size `size`.
def crypt_bytearray(buf, e, n, size):
	# Interpret bytearray as an integer
	M = int.from_bytes(buf, byteorder='big', signed=False)

	# Sanity check
	if M >= n:
		raise Exception("RSA doesn't work if M >= n")

	# Enc(M) = M^e (mod n)
	enc = pow(M, e, n)

	# Turn it back into a bytearray
	return enc.to_bytes(size, 'big', signed=False)

# Remove padding from bytearray.
# G is a hash of r
def remove_padding(decrypted, G):
	X = decrypted[:BLOCK_MSG_SIZE]
	return xor_bytearrays(X, G)

# Extract r from the bytearray
def extract_r(decrypted):
	# Get X and Y
	X = decrypted[:BLOCK_MSG_SIZE]
	Y = decrypted[BLOCK_MSG_SIZE:]

	# H = Hash X
	H = hash_bytearray(X)

	# H ^ r = Y so r = H ^ Y
	return xor_bytearrays(H, Y)

# Hash a bytearray, returning a bytearray
def hash_bytearray(b):
	return sha256(bytearray(b))
	# return list([x for x in sha256(bytes(b)).digest()])

# Return an n long random bytearray
def rand_bytes(n):
	return [randbelow(256) for _ in range(0, n)]

# XOR 2 bytearrays
def xor_bytearrays(a, b):
	return [a[i] ^ b[i] for i in range(0, len(a))]
