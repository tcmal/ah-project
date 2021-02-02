from rsa.gen_primes import generate_prime
from math import gcd

# Returns g, x, y
# Where ax + by = g
def gcd_extended(a, b):
	if a == 0:
		return (b, 0, 1)

	g, x1, y1 = gcd_extended(b % a, a)

	x = y1 - (b // a) * x1
	y = x1

	return (g, x, y)

def mod_mult_inverse(a, m):
	# Use the extended euclidean algorithm
	g, x, y = gcd_extended(a, m)

	# a and m must be coprime (GCD = 1)
	if g != 1:
		raise Exception("a and m aren't coprime")

	# Apply mod m to whole equation
	x = x % m

	# Deal with x < 0
	if x < 0:
		x = x + m

	return x

def generate_key():
	# e is a constant
	e = 65537

	# Get p, q and X where X is coprime to e
	p, q, X = None, None, None
	
	## Until we find a correct candidate
	while True:
		## Get 2 primes p and q
		p = generate_prime(2 ** 1024, 2 ** 2048)
		q = generate_prime(2 ** 1024, 2 ** 2048)

		## Find X = phi(pq)
		X = (p - 1) * (q - 1)

		## If X is coprime to e, break out of the loop
		if gcd(X, e) == 1:
			break

	# n = pq
	n = p * q

	# Find d with the extended Euclidean Algorithm
	d = mod_mult_inverse(e, X)

	return (e, d, n)
