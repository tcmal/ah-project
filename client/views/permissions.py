from tkinter import *
from tkinter.ttk import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

from config import LocalFile
from hash import sha256
from common import bool_to_tick
from views import ViewHasBackButton
from views.verify import VerifyHistoryView

class FilePermissionsView(ViewHasBackButton):
	def __init__(self, app, frame, file):
		self.app = app
		self.frame = frame
		self.file = file

		# Initialise widgets

		## Tree
		self.tree = Treeview(frame, selectmode="browse")
		self.tree.bind('<<TreeviewSelect>>', self.select_change)

		self.tree['columns'] = ('bio')
		
		### Column configuration
		self.tree.column('#0', width=500, minwidth=100)
		self.tree.heading('#0', text='Name')
		self.tree.column('bio', minwidth=250)
		self.tree.heading('bio', text='Bio')

		### Loading to start with
		self.tree.insert("", 'end', 'loading', text="Loading...")
		self.tree.grid(row=0, column=0, rowspan=5, padx=5)

		## Back button
		self.add_back_button(row=0, column=1, sticky=N+E+W)

		## Checkboxes for reading and writing
		self.allow_read = IntVar()
		self.read_checkbox = Checkbutton(self.frame, text="Read", state=DISABLED, variable=self.allow_read)
		self.read_checkbox.grid(row=1, column=1, sticky=E+W)

		self.allow_write = IntVar()
		self.write_checkbox = Checkbutton(self.frame, text="Write", state=DISABLED, variable=self.allow_write)
		self.write_checkbox.grid(row=2, column=1, sticky=E+W)

		## Save changes button
		self.submit_button = Button(frame, text="Submit", state=DISABLED, command=self.submit)
		self.submit_button.grid(row=3, column=1, sticky=E+W)

		## Draw the GUI
		self.app.tk.update()

		# Get the list of users and permissions
		self.update_data()

	# Returns a tuple (allow_read, allow_write)
	def get_permissions(self, username):
		if username not in self.permissions.keys():
			return (False, False)
		else:
			return (self.permissions[username]['allow_read'], self.permissions[username]['allow_write'])

	def update_data(self):
		# Clear list
		self.tree.focus("")
		self.select_change(None)
		
		self.tree.delete(*self.tree.get_children())

		# Get a list of users from the server
		self.users = {}

		self.app.ensure_authorised()
		res = self.app.get('directory').json()

		## If it fails, Show error and go home
		if not res['success']:
			messagebox.showerror('Error', 'Error getting user list from server: %s' % res['message'])
			self.back_home()
			return

		## Insert each user
		for user in res['users']:
			self.insert_user(user)

		# Get the permissions for this file
		self.app.ensure_authorised()
		res = self.app.get(
			'file/getPermissions?file_id=%s' % (self.file['id'])
		).json()

		if not res['success']:
			messagebox.showerror('Error getting file permissions', res['message'])
			self.back_home()
			return

		self.permissions = res['permissions']

	def insert_user(self, user):
		## Don't display the user
		if user['name'] == self.app.config.username:
			return
		
		## Store the full object for later
		self.users[user['name']] = user

		## Add to the treeview
		self.tree.insert("", 'end', user['name'], text=user['name'], values=(
			user['bio'].split("\n")[0],))

	# Called when user selects 
	def select_change(self, _event):
		# Make sure inputs aren't usable when they shouldn't be

		## Disable all when no user selected
		if self.tree.focus() == "":
			self.submit_button.config(state=DISABLED)
			self.write_checkbox.config(state=DISABLED)
			self.read_checkbox.config(state=DISABLED)
			return
		username = self.tree.focus()

		## Enable whenever anything is selected
		self.submit_button.config(state=NORMAL)
		self.write_checkbox.config(state=NORMAL)
		self.read_checkbox.config(state=NORMAL)

		# Get the permissions for that user and update checkboxes
		## If they're not listed, they don't have any permissions
		allow_read, allow_write = self.get_permissions(username)
		self.allow_read.set(allow_read)
		self.allow_write.set(allow_write)

	def submit(self):
		# Get the selected username
		if self.tree.focus() == "":
			return
		selected_name = self.tree.focus()
		selected = self.users[selected_name]

		# Get the desired permissions
		allow_read = self.allow_read.get() > 0
		allow_write = self.allow_write.get() > 0

		# Tell the server
		self.app.ensure_authorised()
		res = self.app.post('file/setPermissions', json={
			'file_id': self.file['id'],
			'target': selected_name,
			'allow_read': allow_read,
			'allow_write': allow_write
		}).json()

		if not res['success']:
			messagebox.showerror('Error setting file permissions', res['message'])

		# Update the data
		self.update_data()
