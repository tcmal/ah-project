# Starts the app

import os

from app import App

if __name__ == "__main__":
	# Don't proxy connections to localhost
	# This is needed in some environments
	# (namely, my school's computers)
	os.environ['NO_PROXY'] = 'localhost'

	# Create the main object then hand over control
	app = App()
	app.loop()

	# Save the config before exiting
	app.config.save()