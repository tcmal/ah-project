# Handles storing and retrieving sessions (server-side cookies)

import base64
import datetime
from threading import Lock

from utils import random_bytes

# Keeps track of all the sessions on our server
class SessionStore:
	def __init__(self):
		self.sessions = {}
		self.session_locks = {}

	# Try to get a Session identified by `cookie`
	def get(self, cookie):
		# Check if that cookie is a valid session

		## Check if it's even stored
		if cookie not in self.sessions:
			## If not, return None
			return None

		## Check if it's expired
		if self.sessions[cookie]['expires'] < datetime.datetime.now():
			## If so, remove it and return none
			del self.sessions[cookie]
			del self.session_locks[cookie]

			return None

		# If it is, lock the session / wait for a lock
		self.session_locks[cookie].acquire()

		# Give a handle to the session
		return Session(self, cookie)

	# Initialise a new empty session that expires 2 hours from now
	# Returns: The cookie value that can be used to identify that session
	def new(self):
		# Generate a random cookie value
		## Generate 64 random bytes, then base64 encode them
		cookie = base64.b64encode(random_bytes(64)).decode('ascii')

		# Make objects for it
		self.sessions[cookie] = {
			'expires': datetime.datetime.now() + datetime.timedelta(hours=2)
		}
		self.session_locks[cookie] = Lock()

		# Return its value
		return cookie

# Wrapper for a session dict that just removes the lock when we finish with it
class Session:
	def __init__(self, store, cookie):
		# Store the session store and values represented by the session
		self._vals = store.sessions[cookie]
		self._cookie = cookie
		self._store = store

	# Called when something tries to get an attribute but it doesn't exist
	def __getattr__(self, name):
		# Get the attribute from session vals, if it exists
		if name in self._vals:
			return self._vals[name]

	# Called whenever something tries to set an attribute
	def __setattr__(self, name, val):
		# If it's a class property (they all start with _), set it normally
		if name[0] == "_":
			self.__dict__[name] = val
		else:
			# Otherwise, store it in the session
			self._vals[name] = val

	# Called when this variable is deleted / no more references exist
	# In this case, when the request has been handled
	def __del__(self):
		# Put changes back into the store
		self._store.sessions[self._cookie] = self._vals

		# Release the lock when we're done with this object
		self._store.session_locks[self._cookie].release()