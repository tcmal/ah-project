class HistoryStatement:
	def __init__(self, hashPrev, hashUploaded, username, comment=""):
		self.hashPrev = hashPrev
		self.hashUploaded = hashUploaded
		self.username = username
		self.comment = comment

	def to_bytes(self):
		buf = bytearray()
		buf.extend(self.hashPrev)
		buf.extend(self.hashUploaded)
		buf.extend(self.username.encode('ascii'))
		for _ in range(0, 50 - len(self.username)):
			buf.append(0)
		buf.extend(self.comment.encode('ascii'))
		return buf

	def sign(self, key):
		return key.sign(self.to_bytes())
		pass

	def from_bytes(buf):
		hashPrev = bytearray(buf[:32])
		hashUploaded = bytearray(buf[32:64])
		
		usernameUntrimmed = buf[64:114]
		username = ""
		i = 0
		while usernameUntrimmed[i] != 0:
			username += chr(usernameUntrimmed[i])
			i += 1

		comment = bytes(buf[114:]).decode('ascii')
		return HistoryStatement(hashPrev, hashUploaded, username, comment)

	def __str__(self):
		return "<HistoryStatement %s uploaded %s, previous was %s, comment: %s>" % (self.username, self.hashUploaded, self.hashPrev, self.comment)