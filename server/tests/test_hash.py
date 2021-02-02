# Test script for SHA-256 hashing

from hash import sha256
import numpy as np
from math import ceil, floor

# Test inputs and expected outputs
INPUTS = [
	bytearray("", 'ascii'),
	bytearray("abc", 'ascii'),
	bytearray("abcdefghijklmnopqrstuvwxyz012345", 'ascii'),
	bytearray("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur pharetra tortor ut turpis semper ullamcorper. Pellentesque urna massa, porta eget ipsum sed, blandit dictum erat. Sed eu pellentesque nisi. Nulla facilisi. Curabitur et dapibus orci, imperdiet commodo nisi. Sed elementum egestas vehicula. Cras nec sapien id eros lacinia malesuada. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Vivamus cursus dapibus nisl, ut volutpat orci dignissim et. Sed quis elementum ipsum. Aliquam eget condimentum tellus, ut placerat elit. Morbi et euismod augue.", 'ascii'),
]

EXPECTED_OUTPUTS = [
	bytearray.fromhex("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
	bytearray.fromhex("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
	bytearray.fromhex("653bb1245e828fcda4fa53fcd5a3def5bd7654e651f54b4132b73d74e64435c4"),
	bytearray.fromhex("eee24d397f0270efa587a1873f4bfb6832f6998fa5c1944a97b6762e6c9c77bb"),

]

# Hexdump bytearray
def xxd(arr):
    for i in range(0,ceil(len(arr) / 16)):
        print("\t".join([hex(x)[2:] for x in arr[i*16:(i+1)*16]]))

# Returns (True,) or (False, output) where output is invalid hash
def test_hashing(msg, expected):
	hashed = sha256(msg)

	if hashed == expected:
		return (True,)
	else:
		return (False,hashed)

# Each entry = (expected, actual)
failures = []

# For each test vector
for msg, expected in zip(INPUTS, EXPECTED_OUTPUTS):
	# Run test
	res = test_hashing(msg, expected)

	# If it failed, add it to failures
	if res[0] != True:
		failures.append((expected, res[1]))
		print("x", end="")
	else:
		print(".", end="")

print()
print("%s tests, %s failures" % (len(INPUTS), len(failures)))
print("---")

# Print failures
for msg, (expected, actual) in zip(INPUTS, failures):
	print("For %s, Expected:" % msg)
	print(expected)
	print("Actual:")
	print(actual)
	print("---")