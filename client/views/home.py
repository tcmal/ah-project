from tkinter import *
from tkinter.ttk import *
from functools import partial

class HomeView:
	def __init__(self, app, frame):
		# Import here because otherwise it makes a circular dependency
		from views import CreateFileView, ServerFileListView, UploadLocalView

		self.app = app
		self.frame = frame

		# Initialise widgets
		## Header
		Label(self.frame, text="Hello, %s!" % (self.app.config.username)).grid(row=0, column=0, pady=5)

		## New file
		self.new_file_button = Button(self.frame,
			text="Start tracking a new file",
			command=partial(self.app.replace_view, CreateFileView))
		self.new_file_button.grid(row=1, column=0, pady=5)

		## Server files
		self.server_files_button = Button(self.frame,
			text="View files on the server",
			command=partial(self.app.replace_view, ServerFileListView))
		self.server_files_button.grid(row=2, column=0, pady=5)

		## Upload changed files
		self.local_files_button = Button(self.frame,
			text="Upload local changes",
			command=partial(self.app.replace_view, UploadLocalView))
		self.local_files_button.grid(row=3, column=0, pady=5)