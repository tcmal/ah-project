# Code & Objects for the web server, handles receiving requests and
# handing them off to be processed

import logging
import traceback

from sys import stdin
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

from session import SessionStore
from config import SERVER_CONFIG
from routes import GET_ROUTES, POST_ROUTES, send_not_found, send_server_error
from context import Context
from pool import ConnectionPool

# Main App, holds shared variables, listens for requests and creates handlers for them.
class App(ThreadingMixIn, HTTPServer):
	daemon_threads = True
	def __init__(self, *args, **kwargs):
		# Call parent constructor
		super(HTTPServer, self).__init__(*args, **kwargs)

		# Make connection pool
		self.pool = ConnectionPool(
			SERVER_CONFIG['db_host'],
			SERVER_CONFIG['db_port'],
			SERVER_CONFIG['db_username'],
			SERVER_CONFIG['db_password'],
			SERVER_CONFIG['db_database'],
			SERVER_CONFIG['db_pool_size']
		)

		# Initialise session store
		self.session_store = SessionStore()

# Handles a single request
# This runs in its own thread
class Handler(BaseHTTPRequestHandler):
	# Actual logic for handling a request
	def handle_request(self, routing_dict, has_body):
		# Strip URL parameters & trailing / from URL
		normalized_path = self.path.split("?")[0] ## Get Everything before '?'

		## Cut off last character if it's /
		if normalized_path[-1] == "/":
			normalized_path = normalized_path[:-1]

		## Special case for index
		if normalized_path == "":
			normalized_path = "index"

		# Look for a route that matches

		## If none found, 404
		if normalized_path not in routing_dict.keys():
			return send_not_found(self)

		handler = routing_dict[normalized_path]

		# Parse all the data into a context
		ctx = Context(self.path, self.headers, self.rfile, self.server.session_store, has_body, self.server.pool)

		# Call appropriate handler
		try:
			handler(ctx, self)
		except Exception as e:
			# If there's an error, write 503 and log to console.
			send_server_error(self)
			logging.error("Error serving %s to %s: %s " % (self.client_address, normalized_path, e))
			traceback.print_tb(e.__traceback__)

	# Redirect python's methods to ours
	def do_GET(self):
		self.handle_request(GET_ROUTES, False)

	def do_POST(self):
		self.handle_request(POST_ROUTES, True)

	# Don't log every request
	def log_message(self, format, *args):
		pass