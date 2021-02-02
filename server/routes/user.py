# Routes related to Users
# Specifically:
#   Registering
#   Authenticating
#   Generating Invite Codes
#   Getting a list of users

import base64
import datetime
import json
import random
from math import floor

from rsa import RSAKeypair
from rsa.classes import PUB_KEY_START, PUB_KEY_END
from routes.common import send_bad_request, send_server_error, is_authorised, send_json
from utils import random_string, has_keys

# POST /register
# Inputs: invite_code, name, bio, public_key
# Attempts to register a new user
# Outputs: Details of new user OR 'Not valid'
def register(req, res):
	# Get inputs from request
	## Check they all exist first
	if not req.body or not has_keys(req.body, ("invite_code", "name", "bio", "public_key")):
		## Error otherwise
		return send_bad_request(res, "Malformed Request")
	
	invite_code = req.body['invite_code']
	name = req.body['name']
	bio = req.body['bio']
	public_key = req.body['public_key']

	# Verify name, bio and public key
	valid = len(name) <= 50 and len(name) > 0 and len(bio) <= 250 # bio can be empty

	## Check if the public key is valid
	try:
		deserialised = RSAKeypair.deserialise(public_key)
		assert deserialised.is_public
	except Exception as _:
		valid = False

	## Error otherwise
	if not valid:
		return send_bad_request(res, "Invalid name, bio or public key")

	# Verify invite code is valid and exists
	code_valid = False
	if len(invite_code) == 10 and invite_code.isalnum(): # Is alpha numeric and 10 chars long
		## Check database
		with req.db as conn:
			# Check one that's not used by a user exists
			sql = "SELECT COUNT(*) AS valid FROM InviteCode WHERE code = %s AND code NOT IN (SELECT invite_code FROM User);"
			conn.execute(sql, (invite_code,))
			result = conn.fetchone()
			code_valid = result[0] > 0

	# Error otherwise
	if not code_valid:
		return send_bad_request(res, "Invalid Invite Code")

	# Add the user to the database
	with req.db as conn:
		## Convert public key to what ends up in the database
		processed_pk = deserialised.to_binary_hex()

		sql = "INSERT INTO User (name, bio, public_key, is_admin, invite_code) VALUES (%s, %s, X%s, 0, %s)"
		success = True
		try:
			conn.execute(sql, (name, bio, processed_pk, invite_code))
			success = conn.rowcount == 1
		except Exception as _: # Probably duplicate name
			success = False

	if success:
		# Return details of new user
		return send_json(res, {
			'success': True,
			'name': name,
			'bio': bio,
			'public_key': public_key,
		})
	else:
		# OR Error
		return send_bad_request(res, "Username already taken")

# POST /auth/getChallenge
# Inputs: username
# Get the authentication challenge for that user
def getChallenge(req, res):
	# Get user to try and sign in as
	if not req.body or not "username" in req.body.keys():
		## Error otherwise
		return send_bad_request(res, "Malformed Request")

	username = req.body['username']

	# Generate random string
	challenge_string = random_string(10)

	# Save to database along with time generated (if user exists)
	with req.db as conn:
		sql = "UPDATE User SET last_challenge_issued = %s, challenge_issued_at = NOW() WHERE name = %s"
		conn.execute(sql, (challenge_string, username))
		updated = conn.rowcount == 1

	if updated:
		# Return challenge
		return send_json(res, {
			'success': True,
			'challenge_string': challenge_string,
		})
	else:
		# Error if user doesn't exist
		return send_bad_request(res, "User Not Found")

# POST /auth/submitChallenge
# Inputs: username, challenge_answer
# Try to authenticate as user
def submitChallenge(req, res):
	# Get inputs from request
	## Check they all exist first
	if not req.body or not has_keys(req.body, ("username", "challenge_answer")):
		## Error otherwise
		return send_bad_request(res, "Malformed Request")
	
	username = req.body['username']
	challenge_answer = req.body['challenge_answer']

	# Get user from database (OR error)
	with req.db as conn:
		sql = "SELECT HEX(public_key), last_challenge_issued, challenge_issued_at FROM User WHERE name = %s"
		conn.execute(sql, (username,))
		result = conn.fetchone()

	if not result:
		return send_bad_request(res, "User Not Found or Invalid challenge")

	pk_hexstring = result[0]
	last_challenge_issued = result[1]
	challenge_issued_at = result[2]

	# Verify challenge issued within 10 minutes (OR error)
	mins_since = (datetime.datetime.now() - challenge_issued_at).seconds / 60
	if mins_since > 10:
		return send_bad_request(res, "Challenge timed out")

	# Decrypt signed challenge with public key
	key = RSAKeypair.from_binary_hex(pk_hexstring)

	# Verify equal to last challenge issued (OR error)
	message = bytearray(key.decrypt_signed(challenge_answer)).decode('ascii')
	if message == False or message != last_challenge_issued:
		return send_bad_request(res, "User Not Found or Invalid challenge")

	# Generate random session token
	cookie_val = res.server.session_store.new()
	
	# Store it as session token for this user
	session = res.server.session_store.get(cookie_val)
	session.username = username

	# Return session token
	req.cookies['session'] = cookie_val
	req.cookies['session']['max-age'] = 2 * 60 * 60
	req.cookies['session']['path'] = '/'

	res.send_response(200)
	res.send_header('Content-Type', 'application/json')
	res.send_header('Set-Cookie', str(req.cookies).replace('Set-Cookie: ', ''))
	res.end_headers()
	res.wfile.write(json.dumps({
		'success': True,
		'session_cookie': cookie_val,
		'username': username
	}).encode('ascii'))

# GET /admin/genInviteCode
# Generate a new invitecode, as long as you're an admin
def genInviteCode(req, res):
	# Verify authorisation
	if not is_authorised(req):
		# Error otherwise
		return send_bad_request(res, 'No Session')

	# Verify user is admin
	with req.db as conn:
		sql = "SELECT COUNT(*) FROM user WHERE name = %s AND is_admin = 1"
		conn.execute(sql, (req.session.username,))

		count = conn.fetchone()[0]
		is_admin = count == 1

	if not is_admin:
		# Error otherwise
		return send_bad_request(res, "Not an admin")

	# Generate random string
	invite_code = random_string(10)

	# Save to database as invite code
	with req.db as conn:
		sql = "INSERT INTO invitecode (code, created_by) VALUES (%s, %s)"
		conn.execute(sql, (invite_code, req.session.username))

		success = conn.rowcount == 1

	if success:
		# Return invite code
		return send_json(res, {
			'success': True,
			'invite_code': invite_code
		})
	else:
		# This shouldn't happen
		send_server_error(res)

# GET /directory
# Return all users on the server (as long as you're authenticated)
def directory(req, res):
	# Verify the user's authorisation (OR error)
	if not is_authorised(req):
		return send_bad_request(res, "No Session")

	# Get the users from the database
	users = []
	with req.db as conn:
		sql = "SELECT name, bio, is_admin, HEX(public_key) FROM User WHERE name != 'console'"
		conn.execute(sql)

		for row in conn:
			users.append({
				'name': row[0],
				'bio': row[1],
				'is_admin': row[2] == 1,
				'public_key': RSAKeypair.binary_hex_to_serialised(row[3])
			})

	# Return them
	return send_json(res, {
		'success': True,
		'users': users
	})