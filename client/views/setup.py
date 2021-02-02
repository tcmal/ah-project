from tkinter import *
from tkinter.ttk import *
import requests

from views import HomeView
from common import labelled_entry
from rsa import RSAKeypair

# Initial window to set the server url
class SetServerURLView:
	def __init__(self, app, frame):
		self.app = app
		self.frame = frame

		# Initialise widgets
		## Header
		Label(self.frame, text="Initial Setup").grid(row=0, column=0, columnspan=2)

		## Form for server URL
		self.serverBaseUrl_entry = labelled_entry(self.frame, 1, "Server Base URL: ")

		## Submit button
		self.finished_button = Button(frame, text="New Account", command=self.onClick)
		self.finished_button.grid(row=2, column=0, columnspan=2, pady=5)

	## Called when button is submitted
	def onClick(self):
		# Validate the server base URL
		serverBaseUrl = self.serverBaseUrl_entry.get()
		
		## Required
		if len(serverBaseUrl) == 0:
			return

		## Make sure it ends in /
		if serverBaseUrl[-1] != '/':
			serverBaseUrl += '/'

		# Make a test connection
		try:
			requests.get(serverBaseUrl)
		except requests.exceptions.ConnectionError as _:
			# If it fails,, notify the user and wait for them to try again
			messagebox.showerror('Server not Found', 'The server doesnt seem to be responding.')	
			return

		# If it succeeds, go to the next view, passing it this URL
		self.app.replace_view(NewAccountView, serverBaseUrl)

class NewAccountView:
	def __init__(self, app, frame, serverBaseUrl):
		# Store options for later
		self.app = app
		self.frame = frame
		self.serverBaseUrl = serverBaseUrl

		# Initialise widgets

		## Username
		self.username_entry = labelled_entry(self.frame, 0, "Username: ", width=50)

		## Bio (extended Text)
		Label(self.frame, text="Bio: ").grid(sticky=W, row=1, column=0)
		self.bio_text = Text(self.frame, width=50, height=5)
		self.bio_text.grid(row=1, column=1)

		## Encrypt key checkbox
		self.encrypt_key = IntVar()
		self.encrypt_key_check = Checkbutton(self.frame,
			text="Encrypt Key?",
			command=self.update_password_entry,
			variable=self.encrypt_key)
		self.encrypt_key_check.grid(row=2)

		## Password entry
		self.password_entry = labelled_entry(self.frame, 3, "Encryption Password: ",
			show="*", state=DISABLED)

		## Invite code
		self.invite_code_entry = labelled_entry(self.frame, 4, "Invite Code: ")

		## Submit button
		self.submit_button = Button(self.frame, text="Submit", command=self.on_submit)
		self.submit_button.grid(row=5)
	
	# Flash a message to the bottom
	def flash_message(self, msg):
		# Create the label if it doesn't exist
		if not hasattr(self, 'flash_label'):
			self.flash_label = Label(self.frame, text="")
			self.flash_label.grid(row=6, column=0)

		# Set the text
		self.flash_label.config(text=msg)

	# Called when use password checkbox is toggled
	def update_password_entry(self):
		if self.encrypt_key.get() > 0:
			# Enable password entry if it's being used
			self.password_entry.config(state=NORMAL)
		else:
			# Disable otherwise
			self.password_entry.config(state=DISABLED)

	def on_submit(self):
		# Get inputs from entries
		username = self.username_entry.get()
		bio = self.bio_text.get('1.0', 'end')
		invite_code = self.invite_code_entry.get()
		encrypt_key = self.encrypt_key.get() > 0
		password = None
		if encrypt_key:
			password = self.password_entry.get()

		# Check validity
		error_messages = []

		## 0 < len(username) <= 50
		if len(username) == 0:
			error_messages.append("Username is required")
		elif len(username) > 50:
			error_messages.append("Username is too long (max 50 characters)")

		## bio shorter than 250
		if len(bio) > 250:
			error_messages.append("Bio is too long (max 250 characters)")

		## Password required if encrypting key
		if encrypt_key and len(password) == 0:
			error_messages.append("Encryption selected but no password provided")

		## Invite code is 10 alphanumeric chars
		if not invite_code.isalnum() or len(invite_code) != 10:
			error_messages.append("Invalid invite code")

		# Show errors if needed
		if len(error_messages) > 0:
			self.flash_message(", ".join(error_messages))
			return

		# Schedule the actual generation of key and stuff
		self.set_all_state(DISABLED)
		self.app.tk.after(1, self.create_user, username, bio, invite_code, password)

	def create_user(self, username, bio, invite_code, password):
		# Generate key
		self.flash_message("Generating keypair...")
		self.app.tk.update()

		key = RSAKeypair.generate_keypair()

		# Register with server
		self.flash_message("Registering with server...")
		self.app.tk.update()
		
		res = requests.post(self.serverBaseUrl + 'register', json={
			'invite_code': invite_code,
			'name': username,
			'bio': bio,
			'public_key': key.serialise(force_public=True)
		})
		res = res.json()

		if res['success']:
			# If successful, flash message
			self.flash_message("Done!")
			self.app.tk.update()

			# Store config
			config = self.app.config
			config.initial_setup(self.serverBaseUrl, username, key, password != None, password)
			config.save()

			# Go to the home view
			self.app.replace_view(HomeView)
		else:
			# If failed, show errors
			self.flash_message(res['message'])

			# Re-enable inputs
			self.set_all_state(NORMAL)
			if not self.encrypt_key:
				self.password_entry.config(state=DISABLED)

	# Set the state of all inputs
	def set_all_state(self, state):
		self.username_entry.config(state=state)
		self.bio_text.config(state=state)
		self.encrypt_key_check.config(state=state)
		self.password_entry.config(state=state)
		self.invite_code_entry.config(state=state)
		self.submit_button.config(state=state)
		