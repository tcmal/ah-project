# A standard circular queue
class Queue:
	# + Queue(Integer)
	def __init__(self, n):
		# Initialise instance properties
		self.max = n
		self.array = [None for _ in range(0, n)] # Empty array of n elements
		self.start = 0
		self.end = 0
		self.size = 0

	# + put(Object)
	def put(self, element):
		# If the queue is already full,
		if self.size == self.max:
			# Throw an error
			raise Exception("Queue Overflow")

		# Add the element at the end index
		self.array[self.end] = element

		# Add 1 to end, wrapping around if necessary
		self.end = (self.end + 1) % self.max
		
		# Update size
		self.size += 1

	# + get(): Object
	def get(self):
		# If the queue is empty,
		if self.size == 0:
			# Throw an error
			raise Exception("Queue Underflow")

		# Get whatever is at the front of the queue
		val = self.array[self.start]

		# Set that index to nothing
		self.array[self.start] = None

		# Add 1 to start, wrapping around if necessary
		self.start = (self.start + 1) % self.max

		# Update size
		self.size -= 1

		# Return the retrieved value
		return val

	# + empty(): Boolean
	def empty(self):
		# True if size = 0
		return self.size == 0