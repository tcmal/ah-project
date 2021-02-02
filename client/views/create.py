from tkinter import *
from tkinter.ttk import *
import tkinter.filedialog as filedialog

from pathlib import Path
import json

from config import LocalFile
from hash import sha256
from statement import HistoryStatement
from common import labelled_entry, header
from views import ViewHasBackButton

# Form to create a file on the server
class CreateFileView(ViewHasBackButton):
	def __init__(self, app, frame):
		self.app = app
		self.frame = frame

		# Initialise widgets
		self.header = header(self.frame, "Start tracking a file", row=0, column=0, columnspan=2)

		# Path entry
		self.path_sv = StringVar()
		self.path_entry = labelled_entry(self.frame, 1, "Local File Path: ",
			width=50,
			textvariable=self.path_sv,
			state="readonly")

		# "Browse" button
		self.path_select_button = Button(self.frame, text="Browse", command=self.browse_for_path)
		self.path_select_button.grid(row=1, column=2)

		# File name and comment for history statement
		self.name_sv = StringVar()
		self.name_entry = labelled_entry(self.frame, 2, "File Name: ", width=50,
			textvariable=self.name_sv)
		self.comment_entry = labelled_entry(self.frame, 3, "Comment: ", width=50)

		# Back home button
		self.add_back_button(row=4, column=0)

		# Submit button
		self.submit_button = Button(self.frame, text="Submit", command=self.on_submit)
		self.submit_button.grid(row=4, column=1, pady=5)

	# Flash a message to the bottom
	def flash_message(self, msg):
		# Create the label if it doesn't exist
		if not hasattr(self, 'flash_label'):
			self.flash_label = Label(self.frame, text="")
			self.flash_label.grid(row=4, column=0)

		# Set the text
		self.flash_label.config(text=msg)

	# Called when the browse button is clicked
	def browse_for_path(self):
		# Open a file picker dialog
		filename = filedialog.askopenfilename()

		# Save the picked path to the path_entry field
		self.path_sv.set(filename)

		# Also set the filename to whatever it currently is
		self.name_sv.set(Path(filename).name)

	# Called when the submit button is clicked
	def on_submit(self):
		# Validate form inputs
		file_name = self.name_sv.get()
		file_path = Path(self.path_sv.get())
		comment = self.comment_entry.get()

		## Name isn't too long
		error_messages = []
		if len(file_name) == 0:
			error_messages.append("Name is required")
		if len(file_name) > 250:
			error_messages.append("Name is too long (max 250 chars)")

		## Comment isn't too long
		if len(comment) > 50:
			error_messages.append("Comment is too long (max 50 chars)")

		## File exists
		if not file_path.exists() or not file_path.is_file():
			error_messages.append("File does not exist")

		# Show errors, if applicable
		if len(error_messages) > 0:
			self.flash_message(", ".join(error_messages))
			return

		# Schedule doing the actual work
		self.app.tk.after(1, self.create_file, file_path, file_name, comment)
		self.flash_message("")

	# Actually does the work to upload file
	def create_file(self, file_path, file_name, comment):
		# Create the progress bar if it doesn't exist
		if not hasattr(self, 'progress_bar'):
			self.progress_bar = Progressbar(self.frame, maximum=3, value=0)
			self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=N+E+S+W)

		# Hash the file
		self.flash_message("Hashing file...")
		self.app.tk.update()

		with open(file_path, "rb") as f:
			data = bytearray(f.read())

		hashed = sha256(data)

		# Create a history statement using the hash and 32 0s
		hs = HistoryStatement([0 for _ in range(0, 32)], hashed, self.app.config.username, comment)

		self.flash_message("Signing statement...")
		self.progress_bar.config(value=1)
		self.app.tk.update()

		# Sign it with our key
		signed = hs.sign(self.app.config.key)

		# Submit it to the server
		self.flash_message("Uploading...")
		self.progress_bar.config(value=2)
		self.app.tk.update()
		
		self.app.ensure_authorised()
		res = self.app.post('file/create', files={
			'meta': ('meta', json.dumps({
				'name': file_name,
				'statement': signed
			}), 'application/json'),
			'data': ('data', data, 'application/octet-stream')
		})
		res = res.json()


		# Flash error message if needed
		if not res['success']:
			return self.flash_message(res['message'])

		# Start tracking it as a local file
		self.app.config.add_local_file(LocalFile(
			res['file_id'],
			file_path,
			hashed,
			signed,
		))

		# Remove the progress bar and clear message
		self.progress_bar.grid_remove()
		del self.progress_bar

		self.flash_message("")
		self.app.tk.update()

		# Print a success message
		messagebox.showinfo('Success!', 'File successfully uploaded.')

		# Go back home
		self.back_home()
