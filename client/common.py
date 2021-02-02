from tkinter import *
from tkinter.ttk import *

import base64

# Add a form input with an entry
# This uses the grid layout with 2 columns
# kwargs are passed to Entry constructor
def labelled_entry(parent, row, caption, column=0, **kwargs):
	# Make a label and put it in
	Label(parent, text=caption).grid(sticky=W, column=column, row=row, padx=5, pady=5)

	# Make and configure an entry
	entry = Entry(parent, **kwargs)
	
	# Put it in
	entry.grid(column=column + 1, row=row, padx=5, pady=5)

	# Return the entry
	return entry

# If val is true, returns a tick character
# or empty otherwise
def bool_to_tick(val):
	if val:
		return "✔"
	else:
		return ""

def signed_message_to_bytes(msg):
	return bytearray(base64.b64decode(msg.replace("---SIGNED MESSAGE---", "")))

def header(parent, text, **kwargs):
	l = Label(parent, text=text)
	l.grid(**kwargs)
	return l