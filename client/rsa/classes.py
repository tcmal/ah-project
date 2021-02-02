from rsa.keygen import generate_key
from rsa.crypt import encrypt, decrypt
import base64

# Banners used when serialising/deserialising
PUB_KEY_START = "---BEGIN PUBLIC KEY ---\n"
PUB_KEY_END = "\n---END PUBLIC KEY ---"
PRIV_KEY_START = "---BEGIN PRIVATE KEY---\n"
PRIV_KEY_END = "\n---END PRIVATE KEY---"

# Represents an RSA key, either public or private
# Easiest way to deal with RSA encryption/decryption
class RSAKeypair:

	# Construct an instance with given key
	# d can be none, in which case this is a public key
	def __init__(self, e, d, n):
		self.e = e
		self.d = d
		self.n = n
		self.is_public = d == None

	# Generate a new keypair
	def generate_keypair():
		e, d, n = generate_key()

		return RSAKeypair(e, d, n)

	# Encrypt with the public exponent, to be decrypted with the private exponent
	def encrypt(self, msg):
		return encrypt(msg, self.e, self.n)

	# Decrypt with the private exponent, msg should be encrypted with private exponent
	def decrypt(self, msg):
		if self.is_public:
			return False

		return decrypt(msg, self.d, self.n)

	# Sign msg, ie encrypt with private exponent, to be decrypted with public exponent
	def sign(self, msg):
		if self.is_public:
			return False

		return encrypt(msg, self.d, self.n)

	# Decrypt signed message with public exponent
	def decrypt_signed(self, msg):
		return decrypt(msg, self.e, self.n)

	# Serialise this key into a string
	# This string can then be converted back to an instance with .deserialise()
	# Pass force_public=True to make a public key, even if we have the private parts.
	def serialise(self, force_public=False):
		# n and e are in all keys
		buf = self.n.to_bytes(512, byteorder='big')
		buf += self.e.to_bytes(32, byteorder='big')
		
		# Add the private part, if we have it and we're not told not to
		if not self.is_public and not force_public:
			buf += self.d.to_bytes(512, byteorder='big')
		
		# Base64 encode it
		encoded = base64.b64encode(buf).decode('ascii')

		# Add the appropriate banners
		if self.is_public or force_public:
			return PUB_KEY_START + encoded + PUB_KEY_END
		else:
			return PRIV_KEY_START + encoded + PRIV_KEY_END


	# Deserialise a string generated with .serialise() into an instance
	def deserialise(buf):
		# Check which banner it starts with
		if buf[:len(PUB_KEY_START)] == PUB_KEY_START:
			# Public key deserialisation

			# Remove banners and decode
			stripped = buf[len(PUB_KEY_START):-len(PUB_KEY_END)]
			decoded = base64.b64decode(stripped)

			# Public key = n + e
			n = int.from_bytes(decoded[:512], byteorder='big')
			e = int.from_bytes(decoded[512:], byteorder='big')

			return RSAKeypair(e, None, n)
		else:
			# Private key deserialisation

			# Remove banners and decode
			stripped = buf[len(PRIV_KEY_START):-len(PRIV_KEY_END)]
			decoded = base64.b64decode(stripped)
			
			# Private key = n + e + d
			n = int.from_bytes(decoded[:512], byteorder='big')
			e = int.from_bytes(decoded[512:512 + 32], byteorder='big')
			d = int.from_bytes(decoded[-512:], byteorder='big')

			return RSAKeypair(e, d, n)

	# Returns a serialised instance represented as a hexstring suitable for insertion to the database
	# Always returns a public key
	# Use binary_hex_to_serialised to reverse this
	def serialised_to_binary_hex(key):
		processed_pk = key[:]

		# Strip off banners if needed
		if processed_pk[:len(PUB_KEY_START)] == PUB_KEY_START:
			processed_pk = processed_pk[len(PUB_KEY_START)]

		if processed_pk[-len(PUB_KEY_END):] == PUB_KEY_END:
			processed_pk = processed_pk[:-len(PUB_KEY_END)]

		# Base64 decode and return hexstring
		processed_pk = base64.b64decode(processed_pk)

		return processed_pk.hex()

	# Makes a deserialisable string from binary stored in the database
	# Always returns a public key
	def binary_hex_to_serialised(hex):
		return PUB_KEY_START + base64.b64encode(bytes.fromhex(hex)).decode('ascii') + PUB_KEY_END

	# Returns this key represented as a hexstring suitable for insertion to the database
	# Always returns a public key
	# Use from_binary_hex to reverse this
	def to_binary_hex(self):
		buf = self.n.to_bytes(512, byteorder='big')
		buf += self.e.to_bytes(32, byteorder='big')
		
		return buf.hex()

	# Makes an instance from a hex string from binary stored in the database
	# This always returns a public key
	def from_binary_hex(hex):
		buf = bytes.fromhex(hex)
		n = int.from_bytes(buf[:512], byteorder='big')
		e = int.from_bytes(buf[512:], byteorder='big')
		return RSAKeypair(e, None, n)

	def __str__(self):
		return "<RSAKeypair e=%s d=%s n=%s>" % (self.e, self.d, self.n)

	def __eq__(self, other):
		return self.e == other.e and self.d == other.d and self.n == other.n