# Common functions for routes, specifically ones related to dealing with http

import json

# Returns true if the user is logged in
def is_authorised(req):
	return req.session != None and req.session.username != None

# Send the given body as a JSON response with the given code (default=200 OK)
def send_json(handler, body, code=200):
	handler.send_response(code)
	handler.send_header('Content-Type', 'application/json')
	handler.end_headers()
	handler.wfile.write(json.dumps(body).encode('ascii'))

# Default 404 handler (when no route is found)
def send_not_found(handler, message="404 Not Found"):
	send_json(handler, {
		'success': False,
		'message': message
	}, 404)

# Default 503 handler (Internal Server Error)
def send_server_error(handler):
	send_json(handler, {
		'success': False,
		'message': "503 Internal Server Error"
	}, 503)

# Default 400 handler (Bad Request)
def send_bad_request(handler, message="Bad Request"):
	send_json(handler, {
		'success': False,
		'message': "%s" % message
	}, 400)

