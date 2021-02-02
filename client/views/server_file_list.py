from tkinter import *
from tkinter.ttk import *
import tkinter.filedialog as filedialog

from config import LocalFile
from hash import sha256
from common import bool_to_tick, header
from views import ViewHasBackButton
from views.verify import VerifyHistoryView
from views.permissions import FilePermissionsView

class ServerFileListView(ViewHasBackButton):
	def __init__(self, app, frame):
		self.app = app
		self.frame = frame

		# Initialise widgets
		## Header
		self.header = header(self.frame, "Files on the server", row=0, column=0, columnspan=2, pady=5)

		## Tree
		self.tree = Treeview(frame, selectmode="browse")
		self.tree.bind('<<TreeviewSelect>>', self.select_change)

		self.tree['columns'] = ('owner', 'sealed', 'writable')
		
		### Column configuration
		self.tree.column('#0', minwidth=100)
		self.tree.heading('#0', text='Name')
		self.tree.column('owner', minwidth=100)
		self.tree.heading('owner', text='Owner')
		self.tree.column('sealed', minwidth=100)
		self.tree.heading('sealed', text='Locked for Everyone')
		self.tree.column('writable', minwidth=100)
		self.tree.heading('writable', text='Writable for you')

		### Loading to start with
		self.tree.insert("", 'end', 'loading', text="Loading...")
		self.tree.grid(row=1, column=0, rowspan=6, padx=5)

		## Back button
		self.add_back_button(row=1, column=1, sticky=N+E+W)

		## Verify history button
		self.verify_button = Button(frame, text="Verify History", state=DISABLED, command=self.verify_history)
		self.verify_button.grid(row=2, column=1, sticky=E+W)

		## Download button
		self.download_button = Button(frame, text="Download", state=DISABLED, command=self.download_file)
		self.download_button.grid(row=3, column=1, sticky=E+W)

		## Toggle Sealed button
		self.toggle_sealed_button = Button(frame, text="Toggle Read-Only", state=DISABLED, command=self.toggle_sealed)
		self.toggle_sealed_button.grid(row=4, column=1, sticky=E+W)

		## Archive button
		self.archive_button = Button(frame, text="Archive", state=DISABLED, command=self.archive)
		self.archive_button.grid(row=5, column=1, sticky=E+W)

		## Change Permissions button
		self.change_permissions_button = Button(frame, text="Change Permissions", state=DISABLED, command=self.change_permissions)
		self.change_permissions_button.grid(row=6, column=1, sticky=E+W)

		## Draw the GUI
		self.app.tk.update()

		# Show the list of files
		self.update_files()

	def update_files(self):
		# Clear list
		self.tree.focus("")
		self.select_change(None)
		self.tree.delete(*self.tree.get_children())

		# Get a list of files from the server
		self.files = {}

		self.app.ensure_authorised()
		res = self.app.get('files').json()

		## If it fails, Show error and go home
		if not res['success']:
			messagebox.showerror('Error', 'Error getting file list from server: %s' % res['message'])
			self.go_home()

		## Insert each file
		for file in res['files']:
			self.insert_file(file)

	def insert_file(self, file):
		## Store the full object for later
		self.files[file['id']] = file

		## Add to the treeview
		self.tree.insert("", 'end', file['id'], text=file['name'], values=(
			file['owner'],
			bool_to_tick(file['is_read_only']),
			bool_to_tick(file['user_can_write'])
		))

	# Called when user selects 
	def select_change(self, _event):
		# Make sure buttons aren't clickable when they shouldn't be

		## Disable all when no file selected
		if self.tree.focus() == "":
			self.verify_button.config(state=DISABLED)
			self.download_button.config(state=DISABLED)
			self.toggle_sealed_button.config(state=DISABLED)
			self.change_permissions_button.config(state=DISABLED)
			self.archive_button.config(state=DISABLED)
			return

		## Enable verify and download whenever anything is selected
		self.verify_button.config(state=NORMAL)
		self.download_button.config(state=NORMAL)

		## Only enable toggle sealed and change permissions buttons if the user owns the file
		selected_file = self.files[int(self.tree.focus())]
		if selected_file['owner'] == self.app.config.username:
			self.toggle_sealed_button.config(state=NORMAL)
			self.change_permissions_button.config(state=NORMAL)
			self.archive_button.config(state=NORMAL)
		else:
			self.toggle_sealed_button.config(state=DISABLED)
			self.change_permissions_button.config(state=DISABLED)
			self.archive_button.config(state=DISABLED)

	# Called when user tries to verify history
	def verify_history(self):
		# Get the selected file
		if self.tree.focus() == "":
			return
		selected_id = int(self.tree.focus())
		selected = self.files[selected_id]

		# Replace with the verify view which does the actual work
		self.app.replace_view(VerifyHistoryView, selected)

	# Called when the user tries to download a file
	def download_file(self):
		# Get the selected file
		if self.tree.focus() == "":
			return
		selected_id = int(self.tree.focus())
		selected = self.files[selected_id]

		# Get where to save it
		## Find the original extension
		by_dots = selected['name'].split(".")
		if len(by_dots) > 1:
			extension = ".".join(by_dots[1:])
			path = filedialog.asksaveasfilename(
				filetypes=(("Original filetype (.%s)" % extension, "*." + extension),
							("All files", "*.*")),
				defaultextension=extension,
				initialfile=selected['name']
			)
		else:
			path = filedialog.asksaveasfilename(
				filetypes=(("All files", "*.*"))
			)

		if path == "":
			# Stop if they hit cancel
			return

		# Set up a progress bar
		self.progress_bar = Progressbar(self.frame, max=3, value=0)
		self.progress_bar.grid(row=4, columnspan=2, sticky=N+E+S+W, pady=5)
		self.app.tk.update()

		# Download the file
		self.app.ensure_authorised()
		res = self.app.get('file/download?file_id=%s' % selected_id)

		# If it fails
		if res.status_code != 200:
			# Show an error
			messagebox.showerror('Error', 'Error downloading file: %s' % res.json()['message'])
			
			# Remove progress bar
			self.progress_bar.destroy()
			del self.progress_bar

			# Leave
			return

		data = res.content
		self.progress_bar['value'] += 1
		self.app.tk.update()

		# Save to given location
		with open(path, "wb") as f:
			f.write(data)

		self.progress_bar['value'] += 1
		self.app.tk.update()

		# Get the previous history statement
		res = self.app.get('file/getHistory?id=%s' % selected_id)
		res = res.json()

		# If we fail,
		if not res['success']:
			# Show an error
			messagebox.showerror('Error', 'Error downloading file: %s' % res['message'])

			# Destroy the progress bar
			self.progress_bar.destroy()
			del self.progress_bar
			
			# Leave
			return

		last_statement = res['file']['history'][-1]['payload']
		
		self.progress_bar['value'] += 1
		self.app.tk.update()

		# Add to local files list
		self.app.config.add_local_file(LocalFile(
			selected_id,
			path,
			sha256(bytearray(data)),
			last_statement,
		))

		# Show a success message
		messagebox.showinfo('Success!', 'File downloaded successfully.')
		
		# Get rid of progress bar
		self.progress_bar.destroy()
		del self.progress_bar

	def toggle_sealed(self):
		# Get the selected file
		if self.tree.focus() == "":
			return
		selected_id = int(self.tree.focus())
		selected = self.files[selected_id]

		# Check we're the owner
		if selected['owner'] != self.app.config.username:
			return

		# Get the new sealed state
		new_state = not selected['is_read_only']

		# Send the request to the server
		self.app.ensure_authorised()
		res = self.app.post('file/setOptions', json={
			'file_id': selected_id,
			'is_archived': False,
			'is_read_only': new_state
		}).json()

		if not res['success']:
			messagebox.showerror('Error', res['message'])

		# Update the file list
		self.update_files()

	def change_permissions(self):
		# Get the selected file
		if self.tree.focus() == "":
			return
		selected_id = int(self.tree.focus())
		selected = self.files[selected_id]

		# Replace with the verify view which does the actual work
		self.app.replace_view(FilePermissionsView, selected)

	def archive(self):
		# Get the selected file
		if self.tree.focus() == "":
			return
		selected_id = int(self.tree.focus())
		selected = self.files[selected_id]

		# Ask if they're sure
		if messagebox.askquestion('Archiving File',
			'Are you sure? You won\'t be able to read or write this file anymore') != 'yes':
			return

		# Tell the server to archive it
		self.app.ensure_authorised()

		# Update list
		res = self.app.post('file/setOptions', json={
			'file_id': selected_id,
			'is_archived': True,
			'is_read_only': True
		}).json()

		self.update_files()
