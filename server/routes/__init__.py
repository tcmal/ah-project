# Maps route handling functions to the actual URL / method to accept them on

from routes import user, file, permissions

# Also re-export these for convenience
from routes.common import send_bad_request, send_not_found, send_server_error

GET_ROUTES = {
	'/admin/genInviteCode': user.genInviteCode,
	'/directory': user.directory,

	'/files': file.list,
	'/file/getHistory': file.getHistory,
	'/file/download': file.download,
	'/file/getPermissions': permissions.getPermissions
}

POST_ROUTES = {
	'/register': user.register,
	'/auth/getChallenge': user.getChallenge,
	'/auth/submitChallenge': user.submitChallenge,

	'/file/create': file.create,
	'/file/upload': file.upload,
	'/file/setPermissions': permissions.setPermissions,
	'/file/setOptions': permissions.setOptions
}