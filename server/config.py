# Server configuration

import logging
import os

FILE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/uploads/"

SERVER_CONFIG = {
	# How many log messages to show
	# DEBUG - Detailed info on what the server is doing
	# INFO - General info on the server
	# WARNING - Potential data corruption or other problems
	# ERROR - Error serving one request, or a recoverable error
	# CRITICAL - Fatal error
	'log_level': logging.DEBUG,

	# Web Server Configuration

	# 127.0.0.1 only accepts from localhost
	# Use 0.0.0.0 to accept connections from other computers
	'listen_host': '127.0.0.1',
	
	# Port to listen on
	'listen_port': 80,

	# Database connection info
	'db_host': '127.0.0.1',
	'db_port': 3306,
	'db_username': 'root',
	'db_password': 'root',
	'db_database': 'secureVCS',
	
	# How many connections to the database to maintain
	'db_pool_size': 4
}