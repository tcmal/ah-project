from tkinter import *
from tkinter.ttk import *
from tkinter import simpledialog as sd
from tkinter import messagebox as mb

import base64
import json

from statement import HistoryStatement
from hash import sha256
from views import ViewHasBackButton

class UploadLocalView(ViewHasBackButton):
	def __init__(self, app, frame):
		self.app = app
		self.frame = frame
		# Initialise widgets

		## Tree
		self.tree = Treeview(self.frame, selectmode="browse")
		self.tree.bind('<<TreeviewSelect>>', self.select_change)

		self.tree['columns'] = ('fullpath')
		
		### Column configuration
		self.tree.column('#0', width=500, minwidth=100)
		self.tree.heading('#0', text='Name')
		self.tree.column('fullpath', minwidth=250)
		self.tree.heading('fullpath', text='Full Path')

		self.tree.grid(row=0, column=0, rowspan=2, padx=5)

		## Back button
		self.add_back_button(row=0, column=1, sticky=N+E+W)

		## Upload button
		self.upload_button = Button(self.frame, text="Upload", state=DISABLED, command=self.upload_file)
		self.upload_button.grid(row=1, column=1, sticky=S+E+W)

		self.refresh_list()

	def refresh_list(self):
		# Clear list
		self.tree.delete(*self.tree.get_children())
		# Add changed files to the list
		## For each file
		for i in range(len(self.app.config.local_files) - 1, -1, -1):
			local_file = self.app.config.local_files[i]
			## Check it still exists
			if not local_file.path.exists():
				## If it doesn't, remove it from the list
				del self.app.config.local_files[i]
				continue

			## Otherwise, hash it
			with open(local_file.path, "rb") as f:
				currentHash = sha256(bytearray(f.read()))

			## Check if the hash is different
			if currentHash != local_file.hashAcquired:
				## If it is, add it to the treeview
				self.tree.insert("", "end", i, text=local_file.path.name, values=(
					local_file.path,
				))

		# Clear focus and disable upload button
		self.tree.focus("")

	def select_change(self, _event):
		# Make sure upload button isn't clickable when it shouldn't be
		if self.tree.focus() == "":
			## Disable when no file selected
			self.upload_button.config(state=DISABLED)
		else:
			## Enable otherwise
			self.upload_button.config(state=NORMAL)

	def upload_file(self):

		self.progress_bar = Progressbar(self.frame, max=4)
		self.progress_bar.grid(row=3, column=0, columnspan=2, sticky=N+S+E+W)
		self.progress_bar['value'] = 0

		self.app.tk.update()

		# Get which file was selected
		if self.tree.focus() == "":
			return
		selected_idx = int(self.tree.focus())
		local_file = self.app.config.local_files[selected_idx]

		# Make a history statement
		## Get the file's current hash and data
		with open(local_file.path, "rb") as f:
			data = bytearray(f.read())
			hashUploaded = sha256(data)
		
		self.progress_bar['value'] = 1
		self.app.tk.update()

		## Hash the previous history statement
		prevHistoryStatementBytes = bytearray(
			base64.b64decode(
				local_file.prevHistoryStatement.replace("---SIGNED MESSAGE---", "")
			)
		)
		hashPrev = sha256(prevHistoryStatementBytes)
		
		self.progress_bar['value'] = 2
		self.app.tk.update()

		## Ask the user for an optional comment
		comment = sd.askstring("Comment", "Enter comment for history statement (can be blank)")

		hs = HistoryStatement(hashPrev, hashUploaded, self.app.config.username, comment)

		# Sign it
		signed = hs.sign(self.app.config.key)

		self.progress_bar['value'] = 3
		self.app.tk.update()

		# Upload it to the server
		self.app.ensure_authorised()
		res = self.app.post('file/upload', files={
			'meta': ('meta', json.dumps({
				'file_id': local_file.id,
				'statement': signed
			}), 'application/json'),
			'data': data
		})
		res = res.json()

		self.progress_bar['value'] = 4
		self.app.tk.update()

		# If failed, show error message
		if not res['success']:
			mb.showerror('Error uploading file', res['message'])
			self.progress_bar.destroy()
			return

		if mb.askquestion('Uploading succeeded', 'Uploading suceeded. Delete local file?') == 'yes':
			local_file.path.unlink()

			del self.app.config.local_files[selected_idx]
		else:
			local_file.prevHistoryStatement = signed
			local_file.hashAcquired = hashUploaded

			self.app.config.local_files[selected_idx] = local_file

		self.refresh_list()
		self.progress_bar.destroy()


