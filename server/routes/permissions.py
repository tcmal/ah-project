from utils import has_keys
from routes.common import send_bad_request, is_authorised, send_not_found, send_json

# GET /file/getPermissions?file_id=1
def getPermissions(req, res):
	# Get inputs from request
	if not 'file_id' in req.params.keys():
		return send_bad_request(res)

	file_id = req.params['file_id']

	# Verify authentication (or error)
	if not is_authorised(req):
		return send_bad_request(res, "No Session")

	# Check the user querying is the owner of the file
	with req.db as conn:
		sql = "SELECT COUNT(*) FROM File WHERE id = %s AND owner = %s"
		conn.execute(sql, (file_id, req.session.username))
		is_valid = conn.fetchone()[0] > 0

	# Error otherwise
	if not is_valid:
		return send_not_found(res, "File not found or you're not the owner")

	# Get all permissions for file
	permissions = {}

	## Query the db
	with req.db as conn:
		sql = "SELECT username, allow_read, allow_write FROM AccessPermission WHERE file_id = %s"
		conn.execute(sql, (file_id,))
		for row in conn:
			permissions[row[0]] = {
				'allow_read': row[1],
				'allow_write': row[2]
			}

	# Return a response
	send_json(res, {
		'success': True,
		'permissions': permissions
	})

# POST /file/setPermissions
def setPermissions(req, res):
	# Get inputs from request
	if not req.body or not has_keys(req.body, ('file_id', 'target', 'allow_read', 'allow_write')):
		return send_bad_request(res)

	file_id = req.body['file_id']
	target_username = req.body['target']
	allow_write = req.body['allow_write']
	# If we can write, we must also be able to read
	allow_read = req.body['allow_read'] or allow_write

	# Verify authentication (or error)
	if not is_authorised(req):
		return send_bad_request(res, "No Session")

	# Special case: Don't allow console any permissions
	if target_username == "console":
		return send_bad_request(res, "User not found")

	# Get file to change
	with req.db as conn:
		## This only returns the file if the user owns it
		sql = """SELECT COUNT(*) FROM file
			WHERE id = %s AND owner = %s AND file.is_archived = 0;"""
		conn.execute(sql, (file_id, req.session.username))

		exists = conn.fetchone()[0] == 1

	if not exists:
		# OR error
		return send_not_found(res, "Invalid file ID (or file is archived)")

	# Add the new access permission, or amend it if it exists
	with req.db as conn:
		sql = """INSERT INTO AccessPermission (file_id, username, allow_read, allow_write)
			VALUES (%s, %s, %s, %s)
			ON DUPLICATE KEY UPDATE allow_read = %s, allow_write = %s;"""

		try:
			conn.execute(sql, (file_id, target_username, allow_read, allow_write, allow_read, allow_write))
		except:
			# Probably the username is wrong
			return send_not_found(res, "User not found")

	# Return success 
	send_json(res, {
		'success': True,
		'target_username': target_username,
		'allow_write': allow_write,
		'allow_read': allow_read
	})

# POST /file/setOptions
def setOptions(req, res):
	# Get inputs from request
	if not req.body or not has_keys(req.body, ('file_id', 'is_archived', 'is_read_only')):
		return send_bad_request(res)

	file_id = req.body['file_id']
	is_archived = req.body['is_archived']
	is_read_only = req.body['is_read_only'] or is_archived

	# Verify authentication (or error)
	if not is_authorised(req):
		return send_bad_request(res, "No Session")

	# Update the file in the database 
	with req.db as conn:
		sql = "UPDATE File SET is_archived = %s, is_read_only = %s WHERE id = %s AND owner = %s"
		conn.execute(sql, (is_archived, is_read_only, file_id, req.session.username))

		success = conn.rowcount == 1

	if success:
		# Return success
		send_json(res, {
			'success': True,
			'id': file_id,
			'is_archived': is_archived,
			'is_read_only': is_read_only
		})
	else:
		# Either file doesn't exist or it's not owned by this user
		send_not_found(res, "File not found")