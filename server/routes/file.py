# Routes related to most file-related operations, including:
#   Creating
#   Downloading
#   Uploading
#   Listing
#   Getting history

import json
import time
from os import path
import base64

from routes.common import send_bad_request, is_authorised, send_json, send_not_found
from rsa import RSAKeypair
from hash import sha256
from statement import HistoryStatement
from utils import archive_filename, has_keys

# POST /file/create
def create(req, res):
	# Get inputs from request

	## Check they're all there
	if (not has_keys(req.parts, ('meta', 'data')) or
		not has_keys(req.parts['meta'], ('name', 'statement'))):
		return send_bad_request(res)

	filename = req.parts['meta']['name']
	statement_signed = req.parts['meta']['statement']
	data = bytearray(req.parts['data'])

	# Verify authorisation
	if not is_authorised(req):
		# OR error
		return send_bad_request(res, 'No Session')

	# Verify the name is valid

	## Name is < 250 and > 0
	if len(filename) > 250 or filename == "":
		# OR error
		return send_bad_request(res, "Invalid Filename")

	# Verify the history statement (OR error)

	## Get the user's public key
	with req.db as conn:
		sql = "SELECT HEX(public_key) FROM User WHERE name = %s"
		conn.execute(sql, (req.session.username,))
		user_row = conn.fetchone()

	## This would mean the user's been deleted which shouldn't happen
	if user_row == None:
		req.session.username = None
		return send_bad_request(res, "Invalid session")

	## Deserialise the public key
	public_key = RSAKeypair.from_binary_hex(user_row[0])

	## Decrypt the statement
	statement_decrypted = public_key.decrypt_signed(statement_signed)

	if statement_decrypted == False:
		## If we fail to decrypt it, error
		return send_bad_request(res, "Invalid History Statement")

	## Deserialise it
	statement = HistoryStatement.from_bytes(statement_decrypted)

	## hashPrev should be all 0s
	if not all([x == 0 for x in statement.hashPrev]):
		return send_bad_request(res, "Invalid History Statement - hashPrev should be all 0s")

	## hashUploaded should match the hash of the uploaded data
	hashData = sha256(data)

	if statement.hashUploaded != hashData:
		return send_bad_request(res, "Invalid History Statement - hashUploaded doesn't match")

	## Username should match session
	if statement.username != req.session.username:
		return send_bad_request(res, "Invalid History Statement - username doesn't match")

	# Save the file to disk

	## created_at is now for consistency
	created_at = int(time.time())

	## Decide on the name for it
	fs_name = archive_filename(filename, created_at, req.session.username)

	## Create and write the file
	with open(fs_name, "wb") as file:
		file.write(data)

	# Add to the database
	with req.db as conn:
		## Add the file first
		sql = "INSERT INTO File (owner, name) VALUES (%s, %s)"
		conn.execute(sql, (req.session.username, filename))
		file_id = conn.lastrowid

		## Add the first history statement
		statement_signed_bytes = base64.b64decode(statement_signed.replace('---SIGNED MESSAGE---', ''))
		sql = "INSERT INTO HistoryStatement (file_id, created_at, alleged_username, payload) VALUES (%s, from_unixtime(%s), %s, %s)"
		conn.execute(sql, (file_id, created_at, req.session.username, statement_signed_bytes))

	# Return success
	return send_json(res, {
		'success': True,
		'file_id': file_id,
		'file_name': filename,
		'file_owner': req.session.username,
		'statement_hashUploaded': statement.hashUploaded.hex(),
		'statement_comment': statement.comment
	})

# GET /file/getHistory?id=1
def getHistory(req, res):
	# Get inputs from request
	if not 'id' in req.params:
		return send_bad_request(res, 'id is missing')

	file_id = req.params['id']

	# Verify the user's authorisation (OR error)
	if not is_authorised(req):
		return send_bad_request(res, "No Session")

	# Verify they have read access to the file (OR error)
	with req.db as conn:
		# Subquery gets file ids that user owns or that have a read access permission for this user
		# Then the outer query gets the rest of the requested file info if it's in the subquery and not archived
		# ie this only returns a row if we have read access to the file id
		sql = """SELECT owner, name, is_read_only, is_archived FROM file
				WHERE id = %s AND id IN (
					SELECT file.id FROM file WHERE file.owner = %s 
					UNION SELECT file.id FROM file, accesspermission WHERE
						file.id = accesspermission.file_id AND 
						accesspermission.username = %s AND 
						accesspermission.allow_read = 1
				) AND file.is_archived = 0;"""

		conn.execute(sql, (file_id, req.session.username, req.session.username))
		file = conn.fetchone()

	if file == None:
		# Error otherwise
		return send_not_found(res, "File not found")

	# This is what we'll return to the client
	file = {
		'owner': file[0],
		'name': file[1],
		'is_read_only': file[2],
		'is_archived': file[3],
		'history': [] # This is where we'll put the history
	}

	# Get the file history from the database
	with req.db as conn:
		sql = "SELECT alleged_username, created_at, HEX(payload) FROM historystatement WHERE file_id = %s ORDER BY created_at ASC;"
		conn.execute(sql, (file_id,))

		## For each row
		for row in conn:
			# Add it to the history
			file['history'].append({
				'alleged_username': row[0],
				'created_at': row[1].strftime("%Y-%m-%d %H:%M:%S"),
				'payload': '---SIGNED MESSAGE---\n' + base64.b64encode(bytes.fromhex(row[2])).decode('ascii') + '\n---SIGNED MESSAGE---'
			})

	# Return it
	return send_json(res, {
		'success': True,
		'file': file
	})

def upload(req, res):
	# Get inputs from request
	## Check they're all there
	if (not has_keys(req.parts, ('meta', 'data')) or
		not has_keys(req.parts['meta'], ('file_id', 'statement'))):
		return send_bad_request(res)

	file_id = req.parts['meta']['file_id']
	statement_signed = req.parts['meta']['statement']
	data = req.parts['data']

 	# Verify the users’ authorisation (OR error) 
	if not is_authorised(req):
 		return send_bad_request(res, "No Session")

	# Verify they have write access to the file (OR error) 
	with req.db as conn:
		# Subquery gets file ids that user owns or that have a write access permission for this user
		# Then the outer query gets the rest of the requested file info if it's in the subquery and not readonly
		# ie this only returns a row if we have write access to the file id
		sql = """SELECT owner, name, is_read_only, is_archived
			FROM file
				WHERE id = %s AND id IN (
					SELECT file.id FROM file WHERE file.owner = %s 
					UNION SELECT file.id FROM file, accesspermission WHERE
						file.id = accesspermission.file_id AND 
						accesspermission.username = %s AND 
						accesspermission.allow_write = 1
				) AND file.is_read_only = 0;"""

		conn.execute(sql, (file_id, req.session.username, req.session.username))
		file = conn.fetchone()

	if file == None:
		return send_not_found(res, "File not found or isn't writable")

	file = {
		'owner': file[0],
		'name': file[1],
		'is_read_only': file[2],
		'is_archived': file[3],
	}

	# Verify their history statement
	## Get the uploader's public key
	with req.db as conn:
		sql = "SELECT HEX(public_key) FROM User WHERE name = %s"
		conn.execute(sql, (req.session.username,))
		pk_hex = conn.fetchone()[0]

	pk = RSAKeypair.from_binary_hex(pk_hex)

	## Decrypt and deserialise the uploaded statement
	statement_decrypted = pk.decrypt_signed(statement_signed)
	statement = HistoryStatement.from_bytes(statement_decrypted)

	## Get the latest history statement
	with req.db as conn:
		sql = "SELECT HEX(payload) FROM HistoryStatement WHERE file_id = %s ORDER BY created_at DESC LIMIT 1"
		conn.execute(sql, (file_id,))
		prev_statement = conn.fetchone()

	prev_statement = bytearray(bytes.fromhex(prev_statement[0]))

	## Hash it
	expected_hashPrev = sha256(prev_statement)

	## Check hashPrev is what we expect
	if statement.hashPrev != expected_hashPrev:
		return send_bad_request(res, "hashPrev is invalid")

	## Verify their history statement matches the file they’re uploading (OR validity error) 
	expected_hashUploaded = sha256(bytearray(data))
	if statement.hashUploaded != expected_hashUploaded:
		return send_bad_request(res, "hashUploaded is invalid")

	## Verify it matches their session's username
	if statement.username != req.session.username:
		return send_bad_request(res, "username is invalid")

	# Save the file to disk
	## created_at is now for consistency
	created_at = int(time.time())

	## Decide on the name for it
	fs_name = archive_filename(file['name'], created_at, req.session.username)

	## Create and write the file
	with open(fs_name, "wb") as file:
		file.write(data)

	# Save the history statement to the database
	with req.db as conn:
		## Turn the signed statement into raw bytes
		statement_signed_bytes = base64.b64decode(statement_signed.replace('---SIGNED MESSAGE---', ''))

		sql = "INSERT INTO HistoryStatement (file_id, created_at, alleged_username, payload) VALUES (%s, from_unixtime(%s), %s, %s)"
		conn.execute(sql, (file_id, created_at, req.session.username, statement_signed_bytes))

	# Respond with success
	send_json(res, {
		'success': True
	})

def list(req, res):
	# Verify the user's authentication (OR error)
	if not is_authorised(req):
		return send_bad_request(res, "No Session")

	# Get all the files they have access to
	files = []
	with req.db as conn:
		sql = """SELECT id, owner, name, is_read_only, 1 FROM file
			WHERE file.owner = %s AND file.is_archived = 0
			UNION
			SELECT id, owner, name, is_read_only, accesspermission.allow_write FROM file, accesspermission
			WHERE file.is_archived = 0 AND accesspermission.file_id = file.id AND
			accesspermission.username = %s
			AND accesspermission.allow_read = 1;"""
		conn.execute(sql, (req.session.username, req.session.username))

		for row in conn:
			files.append({
				'id': row[0],
				'owner': row[1],
				'name': row[2],
				'is_read_only': row[3] == 1,
				'user_can_write': row[4] == 1
			})

	# Return them
	send_json(res, {
		'success': True,
		'files': files
	})

def download(req, res):
	# Get inputs from request
	if not req.params or not req.params['file_id']:
		return send_bad_request(res)

	file_id = req.params['file_id']

	# Verify the users’ authorisation (OR error)
	if not is_authorised(req):
		return send_bad_request(res, "No Session")

	# Verify they have read access to the file (OR error)
	with req.db as conn:
		# This only returns a row if the file exists and the user has read access
		# It will also get some info about the most recent history statement, from which we can find
		# the file
		sql = """SELECT file.name, UNIX_TIMESTAMP(historystatement.created_at), historystatement.alleged_username
			FROM file, historystatement
			WHERE id = %s AND id IN (
				SELECT file.id FROM file WHERE file.owner = %s 
				UNION SELECT file.id FROM file, accesspermission WHERE
					file.id = accesspermission.file_id AND 
					accesspermission.username = %s AND 
					accesspermission.allow_read = 1
			) AND file.is_archived = 0 AND historystatement.file_id = file.id
			ORDER BY historystatement.created_at DESC
			LIMIT 1;"""

		conn.execute(sql, (file_id, req.session.username, req.session.username))
		row = conn.fetchone()

	if row == None:
		return send_not_found(res, "File not found")

	# Find the location of the latest iteration on disk
	filename = row[0]
	created_at = row[1]
	prev_username = row[2]

	file_on_disk = archive_filename(filename, created_at, prev_username)

	# Respond with the contents of that file
	res.send_response(200)
	# octet-stream means we don't know the type, ie it is arbritrary binary
	res.send_header('Content-Type', 'application/octet-stream')
	res.end_headers()
	with open(file_on_disk, "rb") as f:
		res.wfile.write(f.read())