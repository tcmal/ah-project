# Manages the main app window, loading configuration
# etc

from tkinter import *
import time

from requests import Session

from config import Config
from views import SetServerURLView, HomeView

# Padding to use around the actual content of the window
FRAME_PADDING = 10

class App:
	def __init__(self):
		# Initialise the window
		self.tk = Tk()
		self.tk.title("SecureVCS")
		self.tk.resizable(False, False)

		# Create a session for requests
		# this makes cookies persist, etc
		self.session = Session()

		# We haven't yet authenticated
		self.auth_expires = 0

		self.config = Config(self.tk)

		# Load the initial view
		if self.config.is_valid:
			self.replace_view(HomeView)
		else:
			self.replace_view(SetServerURLView)

	# Load a new instance of the given viewClass into the apps window
	# args and kwargs are passed to the constructor
	def replace_view(self, viewClass, *args, **kwargs):
		# Replace the current frame, if it exists
		if hasattr(self, 'frame'):
			self.frame.destroy()
			del self.frame
			
		self.frame = Frame(self.tk)
		self.frame.grid(row=0, column=0, padx=FRAME_PADDING, pady=FRAME_PADDING)

		# Delete the current view if it exists
		if hasattr(self, 'currentView'):
			del self.currentView

		# Create the new view with the frame and given arguments
		self.currentView = viewClass(self, self.frame, *args, **kwargs)

	def loop(self):
		self.tk.mainloop()

	# Send a post request to the configured server with session
	# For convenience
	def post(self, url, *args, **kwargs):
		return self.session.post(self.config.serverBaseUrl + url, *args, **kwargs)

	# As above, but with GET
	def get(self, url, *args, **kwargs):
		return self.session.get(self.config.serverBaseUrl + url, *args, **kwargs)

	# Make sure the session's authorisation cookie is valid
	# This will attempt to renew it if it's not and raise an exception if it fails
	def ensure_authorised(self):
		# If expires in the future, cookie is valid
		if self.auth_expires > int(time.time()):
			return True

		# Otherwise, Get the challenge
		res = self.post("auth/getChallenge", json={
			'username': self.config.username
		})
		res = res.json()

		# Raise an exception if we fail
		if not res['success']:
			raise Exception("Couldn't get auth challenge")

		challenge_string = res['challenge_string']

		# Sign the challenge
		signed = self.config.key.sign(bytearray(challenge_string.encode('ascii')))

		# Submit it
		res = self.post("auth/submitChallenge", json={
			'username': self.config.username,
			'challenge_answer': signed	
		})
		res = res.json()

		# Raise an exception if we fail
		if not res['success']:
			raise Exception("Failed auth challenge")

		# Session cookie is now renewed for 2 hours
		self.auth_expires = int(time.time()) + (2 * 60 * 60)

		# Return success
		return True