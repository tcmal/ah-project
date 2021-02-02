# SHA-256 hashing function

from math import ceil

# Constants
CHUNK_SIZE_BYTES = 64

ROUND_CONSTANTS = [
	0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
	0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
	0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
	0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
	0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
	0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
	0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
	0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]

# Takes in a bytearray of any size < 2^64 and returns a bytearray of those bytes' hash
def sha256(arr):
	# Don't mutate the caller's copy
	arr = arr[:]

	# Start with constants to return
	out = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]

	# Keep the original length in bits
	orig_bits = len(arr) * 8

	# Add a bit to the end of it
	arr.append(0b1000_0000)

	# Pad it so once we add the length to the end, it will be a multiple of 64 bytes.
	while (len(arr) + 8) % CHUNK_SIZE_BYTES != 0:
		arr.append(0)

	# Add the original # of bits to the end as a 64-bit BE integer.
	arr.extend(orig_bits.to_bytes(8, byteorder='big', signed=False))

	# Loop throgh each chunk
	for i in range(0, len(arr) // CHUNK_SIZE_BYTES):
		# Get chunk data
		chunk = arr[i * CHUNK_SIZE_BYTES:(i + 1) * CHUNK_SIZE_BYTES]

		# Compile work schedule
		# This is an array of 64 32-bit integers
		schedule = [0 for _ in range(0, 64)]

		# Copy 64 bytes of chunk to first 16 words (32bit integers) of schedule
		for i in range(0, 16):
			schedule[i] = sum([
				chunk[4 * i + 0] << 24,
				chunk[4 * i + 1] << 16,
				chunk[4 * i + 2] << 8,
				chunk[4 * i + 3] << 0,
			])

		# Expand the rest of the schedule
		for i in range(16, 64):
			# 
			a = schedule_op_a(schedule[i - 15])
			b = schedule_op_b(schedule[i - 2])
			s = a + b + schedule[i - 16] + schedule[i - 7]
			schedule[i] = s & 0xffffffff # Limit to 32 bits

		# Main compression loop
		# For each part of the work schedule
		compressed = out[:]
		for i in range(0, 64):
			# These operations are defined by the algorithm spec
			# Assume a-h = compressed[0-7]
			# All operations are & 0xffffffff to limit them to 32-bits

			a = compression_op_a(compressed[4])
			b = compression_op_b(compressed[0])

			# (e & f) ^ (!e & g)
			ch = (compressed[4] & compressed[5]) ^ (~compressed[4] & compressed[6]) & 0xffffffff

			# (a & b) ^ (a & c) ^ (b & c)
			maj = (compressed[0] & compressed[1]) ^ (compressed[0] & compressed[2]) ^ (compressed[1] & compressed[2]) & 0xffffffff
			
			# h + a + ch + constant for this round + this part of schedule
			temp1 = (compressed[7] + a + ch + ROUND_CONSTANTS[i] + schedule[i]) & 0xffffffff

			temp2 = b + maj

			# Move each integer up the array, except for 4 which has some special ops
			for i in range(7, 0, -1):
				if i == 4:
					compressed[i] = (compressed[i - 1] + temp1) & 0xffffffff
				else:
					compressed[i] = compressed[i-1]

			# Now update the first record of the array
			compressed[0] = (temp1 + temp2) & 0xffffffff

		# Add the compression for this chunk to the final value
		for i in range(0, 8):
			out[i] = (out[i] + compressed[i]) & 0xffffffff

	# Change out to a bytearray rather than words.
	final = []
	for x in out:
		final.extend(bytearray(x.to_bytes(4, byteorder='big', signed=False)))

	# Return a bytearray
	return bytearray(final)


# Circular right shift
def rotate_right(x, y):
	# Limit to 32 bit integers
	x = x & 0xffffffff

	# Don't shift more than 31 bits
	y = y % 31

	lower = x >> y
	higher = x << (32 - y)

	return (lower | higher) & 0xffffffff

# Used when making the work schedule
def schedule_op_a(x):
    return rotate_right(x, 7) ^ rotate_right(x, 18) ^ x >> 3

def schedule_op_b(x):
    return rotate_right(x, 17) ^ rotate_right(x, 19) ^ x >> 10

# Used when compressing data
def compression_op_a(x):
    return rotate_right(x, 6) ^ rotate_right(x, 11) ^ rotate_right(x, 25)

def compression_op_b(x):
    return rotate_right(x, 2) ^ rotate_right(x, 13) ^ rotate_right(x, 22)

