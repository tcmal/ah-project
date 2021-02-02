# Main entry point for server

import logging
import threading
from config import SERVER_CONFIG
from app import App, Handler
from sys import exit, stdin
from utils import random_string

if __name__ == "__main__":
	# Configure logging
	logging.basicConfig(
		level=SERVER_CONFIG['log_level'],
	    format='[%(levelname)s %(threadName)s] %(message)s',
	)

	# Start server
	server_address = (SERVER_CONFIG['listen_host'], SERVER_CONFIG['listen_port'])
	app = App(server_address, Handler)

	thread = threading.Thread(target=app.serve_forever)
	thread.start()
	logging.info("Started serving at %s:%s" % server_address)

	try:
		# Recieve commands
		while True:
			cmd = stdin.readline()[:-1] # Cut out the newline character
			if cmd == "":
				continue
			
			logging.info("Received Console Command: " + cmd)
			if cmd == "shutdown":
				break
			elif cmd == "geninvitecode":
				code = random_string(10)
				with app.pool.acquire() as conn:
					sql = "INSERT INTO InviteCode (code, created_by) VALUES (%s, %s)"
					conn.execute(sql, (code, "console"))
					success = conn.rowcount == 1

				if success:
					logging.info("Console created invite code: %s" % code)
				else:
					logging.warn("Failed to create invite code.")

			elif "make_admin" in cmd:
				# TODO
				pass
	except KeyboardInterrupt as _:
		pass # Exit on keyboard interrupt

	logging.info("Shutting down...")
	app.shutdown()
	thread.join()
