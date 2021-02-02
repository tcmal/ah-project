from tkinter import *
from tkinter.ttk import *

import time
from queue import Queue
from threading import Thread

from views import ViewHasBackButton
from statement import HistoryStatement
from rsa import RSAKeypair
from hash import sha256
from common import signed_message_to_bytes

ZEROS_32 = bytearray([0 for _ in range(32)])

# Returns a deserialised HistoryStatement or false
def verify_statement(statement, key, alleged_username, hashPrev=ZEROS_32):
	# Decrypt it
	decrypted = key.decrypt_signed(statement['payload'])

	# If it fails, this is invalid
	if decrypted == False:
		return False

	# Deserialise it
	hs = HistoryStatement.from_bytes(decrypted)

	# Make sure previous hash matches what's expected
	if hashPrev != hs.hashPrev:
		return False

	# Make sure username matches what it should be
	if alleged_username != hs.username:
		return False

	# Looks valid
	return hs

# TODO: Error handling
def verify_history(app, file, queue):
	# Get a list of users so we have all public keys on hand
	app.ensure_authorised()
	res = app.get('directory')
	res = res.json()
	if not res['success']:
		raise Exception(res['message'])

	public_keys = {}
	for row in res['users']:
		public_keys[row['name']] = RSAKeypair.deserialise(row['public_key'])

	# Get all history statements
	res = app.get('file/getHistory?id=%s' % file['id'])
	res = res.json()

	if not res['success']:
		raise Exception(res['message'])

	# For each one,
	for index, statement in enumerate(res['file']['history']):
		# Find the correct public key to use
		key = public_keys[statement['alleged_username']]

		if index > 0:
			prev_statement = res['file']['history'][index - 1]
			hs = verify_statement(statement, key, statement['alleged_username'],
				sha256(signed_message_to_bytes(prev_statement['payload'])))
		else:
			hs = verify_statement(statement, key, statement['alleged_username'])
		
		if hs != False:
			# Add it to the queue so it's displayed
			queue.put({
				'valid': 'Y',
				'user': hs.username,
				'comment': hs.comment,
				'time': statement['created_at']
			})
		else:
			# It was invalid so add some row to the table saying so
			queue.put({
				'valid': 'N',
				'user': '-',
				'comment': '-',
				'time': statement['created_at']
			})

	queue.put('END')

class VerifyHistoryView(ViewHasBackButton):
	def __init__(self, app, frame, file):
		self.app = app
		self.frame = frame
		self.file = file

		# Initialise widgets
		## Tree
		self.tree = Treeview(self.frame, selectmode="browse")

		self.tree['columns'] = ('time', 'user', 'valid')
		
		### Column configuration
		self.tree.column('#0', width=500, minwidth=100)
		self.tree.heading('#0', text='Comment')
		self.tree.column('time', minwidth=100)
		self.tree.heading('time', text='Time')
		self.tree.column('user', minwidth=100)
		self.tree.heading('user', text='Username')
		self.tree.column('valid', minwidth=100)
		self.tree.heading('valid', text='Valid?')

		self.tree.grid(row=0, column=0)

		## Progress bar
		self.progress_bar = Progressbar(self.frame, orient="horizontal", mode="indeterminate")
		self.progress_bar.grid(row=1, column=0, sticky=N+S+E+W, pady=5)

		## Back button
		self.add_back_button(row=2, column=0)

		# Start thread to verify history
		self.queue = Queue()

		self.worker_thread = Thread(target=verify_history, args=(self.app, self.file, self.queue), daemon=True)
		self.worker_thread.start()

		# Start polling the queue for new entries
		self.scheduled_task = self.app.tk.after(20, self.poll_queue)

	def poll_queue(self):
		self.progress_bar['value'] = (self.progress_bar['value'] + 1) % 100
		while not self.queue.empty():
			item = self.queue.get()
			if item == "END":
				self.worker_thread.join()
				del self.worker_thread
				del self.queue

				self.progress_bar.destroy()
				del self.progress_bar

				self.scheduled_task = None

				return

			self.tree.insert("", 'end', text=item['comment'], values=(
				item['time'],
				item['user'],
				item['valid']
			))

		self.scheduled_task = self.app.tk.after(1000, self.poll_queue)

	def back_home(self):
		if self.scheduled_task != None:
			self.app.tk.after_cancel(self.scheduled_task)

		super().back_home()