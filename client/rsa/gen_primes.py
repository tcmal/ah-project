from random import randrange
from secrets import randbelow
import numpy as np

SMALL_PRIMES = [3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97
                   ,101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179
                   ,181,191,193,197,199,211,223,227,229,233,239,241,251,257,263,269
                   ,271,277,281,283,293,307,311,313,317,331,337,347,349,353,359,367
                   ,373,379,383,389,397,401,409,419,421,431,433,439,443,449,457,461
                   ,463,467,479,487,491,499,503,509,521,523,541,547,557,563,569,571
                   ,577,587,593,599,601,607,613,617,619,631,641,643,647,653,659,661
                   ,673,677,683,691,701,709,719,727,733,739,743,751,757,761,769,773
                   ,787,797,809,811,821,823,827,829,839,853,857,859,863,877,881,883
                   ,887,907,911,919,929,937,941,947,953,967,971,977,983,991,997]

# Attempts to prove that X is a composite number using A as a witness
# d2^s must equal n - 1
def attempt_prove_composite(x, a, s, d):
	# Calculate v = a^d % x
	v = pow(a, d, x) # pow(base, exponent, modulus)

	# If first term v = 1 or x - 1, A won’t prove X is composite
	if v in (1, x - 1):
		return False

	# Keep going through the sequence till we find something that proves not composite
	## For i from 0 to s (exclusive)
	for i in range(1, s):
		# v = v^2 mod x
		v = pow(v, 2, x)

		# If v = x - 1, X is not composite
		if v == x - 1:
			return False

	# If we don't find anything, it's probably composite
	return True

# Returns if a number looks prime after a series of tests.
# Higher k gives a higher confidence.
def is_prime(x, k=40):
	# Try some divisions by small primes to weed out easy ones
	## For each small prime
	for small in SMALL_PRIMES:
		## If x % small prime is 0, X isn't prime
		if x % small == 0:
			return False

	# Find s and d such that d2^s = n - 1
	## Start with d = x - 1 and s = 0 divisions by 2 done.
	d = np.int(x - 1)
	s = np.int(0)
	# While we can roundly divide d by 2,
	while d % 2 == 0:
		# Divide d by 2
		d //= 2

		# Increment the number of times we've divided by 2
		s += 1

	# Repeat k times:
	for _ in range(0, k):
		# Get a random number a (0 < a < x)
		a = np.int(randrange(0, x - 1))

		# Try to prove x is composite with a, s and d
		if attempt_prove_composite(x, a, s, d):
			# If it is composite, X is not prime
			return False
	
	# If we can't prove it's composite, it's probably prime
	return True

# Generates a prime number in [minimum, maximum)
def generate_prime(minimum, maximum):
	# Since x = 6r +- 1, min r = min / 6, etc
	r_min = minimum // 6
	r_max = maximum // 6

	# Until a prime is found
	while True:
		# Get a random number r
		r = np.int(randbelow(r_max - r_min) + r_min)

		# Check if 6r + 1 is probably prime
		x = (6 * r) + 1
		if is_prime(x):
			# If so, return it
			return x
		
		# Check if 6r - 1 is probably prime
		x = (6 * r) - 1
		if is_prime(x):
			# If so, return it.
			return x