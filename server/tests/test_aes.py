# Test script for AES encryption

from aes import aesEncrypt, aesDecrypt
import numpy as np
from math import ceil, floor
import random

# Test keys/messages

INPUT_KEYS = [
	list([0 for _ in range(0, 32)]),
	list([i for i in range(0, 32)]),
	list([floor(random.random() * 255) for i in range(0, 32)])
]

INPUT_MESSAGES = [
	list([0 for _ in range(0,16)]),
	list([ord(x) for x in "1234567890abcdef"]),
	list([i for i in range(0,128)]),
	list([floor(random.random() * 255) for i in range(0, 32)])
]


# Hexdump bytearray
def xxd(arr):
    for i in range(0,ceil(len(arr) / 16)):
        print("\t".join([hex(x)[2:] for x in arr[i*16:(i+1)*16]]))

# Returns (True,) or (False, output) where output is invalid decryption
def test_encrypt_decrypt(msg, key):
	encrypted = aesEncrypt(msg, key)
	decrypted = aesDecrypt(encrypted, key)

	if np.array_equal(decrypted, msg):
		return (True,)
	else:
		return (False,decrypted)

# Each entry = (expected, actual)
failures = []

# For each message
for msg in INPUT_MESSAGES:

	# Try encrypting with every key
	for key in INPUT_KEYS:
		# Run test
		res = test_encrypt_decrypt(msg, key)

		# If it failed, add it to failures
		if res[0] != True:
			failures.append((msg, res[1]))
			print("x", end="")
		else:
			print(".", end="")

print()
print("%s tests, %s failures" % (len(INPUT_KEYS) * len(INPUT_MESSAGES), len(failures)))
print("---")

# Print failures
for expected, actual in failures:
	print("Expected:")
	xxd(expected)
	print("Actual:")
	xxd(actual)
	print("---")