# Database Connection Pool object

import logging
from threading import Lock
from queue import Queue
from time import sleep

import mysql.connector

# .queue stores available connections
# When a connection is used, its popped from the queue, then returned when its done with
# There's a write lock around the queue because this pool will be used from multiple threads
class ConnectionPool:
	# + ConnectionPool(host, port, username, password, database, num_connections)
	def __init__(self, host, port, username, password, database, num_connections):
		# Initialise instance properties

		## Connection arguments
		self.host = host
		self.port = port
		self.username = username
		self.password = password
		self.database = database

		self.num_connections = num_connections

		## Queue and lock
		self.queue = Queue(num_connections)
		self.queue_lock = Lock()

		# Make however many connections we need
		with self.queue_lock as _:
			# Loop num_connections times
			for i in range(0, num_connections):
				logging.debug("Creating connection %s" % i)

				# Make a new connection and add it to the queue
				self.queue.put(mysql.connector.connect(host=self.host,
					user=self.username,
					password=self.password,
					database=self.database,
					port=self.port
				))

	# + acquire(): ConnectionFromPool
	def acquire(self):
		# Loop until we find a connection
		conn = None
		while conn == None:
			# Check if the queue is empty
			if not self.queue.empty():
				# If it's not, lock the queue
				with self.queue_lock as _:
					# Try to get a connection from the queue
					try:
						conn = self.queue.get()
					except Exception as _:
						# This probably means the queue emptied between us checking and actually locking it
						# So just keep looping
						pass

			# If it is empty, let other threads run
			sleep(0)

		# Check the connection is still valid
		if not conn.is_connected():
			# If it's not, reconnect
			# This might happen cos of a timeout
			conn = mysql.connector.connect(host=self.host,
				user=self.username,
				password=self.password,
				database=self.database,
				port=self.port
			)

		# When we find one, wrap it in a ConnectionFromPool and return it
		return ConnectionFromPool(self, conn)

	# + put_back(Connection)
	def put_back(self, conn):
		# Put the connection back in the queue
		self.queue.put(conn)

	# + __del__()
	# Called just before the object is destroyed, ie when the server goes down
	def __del__(self):
		# Make sure nothing can use connections
		logging.debug("Emptying pool...")
		i = 0
		while not self.queue.empty():
			logging.debug("Disconnecting connection %s" % i)
			self.queue.get().close()
			i += 1


class ConnectionFromPool:
	def __init__(self, pool, conn):
		self.pool = pool
		self.conn = conn

	def __enter__(self):
		# Get a cursor from this connection
		self.cursor = self.conn.cursor()
		
		# Return it
		return self.cursor

	def __exit__(self, _, __, ___):
		# Commit all changes and close the cursor
		self.cursor.close()
		self.conn.commit()

	def __del__(self):
		# Return the connection to the pool
		self.pool.put_back(self.conn)
