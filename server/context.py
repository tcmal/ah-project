# Passed to route handlers, containing all the relevant information for that request

from urllib.parse import unquote
from http.cookies import SimpleCookie
import json

# Contains all the information about a request
class Context:
	def __init__(self, path, headers, rfile, sessionStore, has_body, pool):
		# Parse URL parameters
		self.params = {}
		if "?" in path:
			try:
				## URL Parameters are of the format ?a=b&c=d&e=%20space

				## Just the part after ?
				param_part = path.split("?")[-1]

				## Split into each segment (a=b, c=d, e=%20space)
				segments = param_part.split("&")

				## Decode each one
				for segment in segments:
					## Seperate key & value
					key, value = segment.split("=")

					## Url decode it as well
					self.params[key] = unquote(value)
			except:
				# If it fails, Probably invalid formatting, so just ignore it
				pass

		# Parse cookies
		self.cookies = SimpleCookie(str(headers['Cookie']))

		# Get session, if applicable
		self.session = None
		
		## If there's a session cookie
		if 'session' in self.cookies.keys():
			## Try to get it from the session store
			self.session = sessionStore.get(self.cookies['session'].value)

		# Store the rest of the headers
		self.headers = headers

		# Get a connection from the pool
		self.db = pool.acquire()

		# Parse body, if applicable
		if has_body:
			# Load the raw body
			self.raw_body = rfile.read(int(self.headers['Content-Length']))
			self.body = None

			# If there's a content type, try to do stuff with it
			if 'Content-Type' in headers.keys():
				contentType = headers['Content-Type']

				# Parse JSON
				if contentType == "application/json":
					self.body = json.loads(self.raw_body)
				elif "multipart/form-data" in contentType:
					# Multipart is split up by the boundary specified in the header
					boundary = bytes(contentType.split("boundary=")[-1], 'ascii')

					self.parts = {}
					part = b""
					part_type = ""
					part_name = ""
					had_type = False
					had_name = False

					# Loop through each line of data
					for line in self.raw_body.split(b"\r\n")[1:]:

						# If there's a boundary, end of this part
						if boundary in line:
							# Parse it if it's JSON
							if part_type == "application/json":
								self.parts[part_name] = json.loads(part)
							else:
								# Otherwise just put it there, trimming \r\n off the start and end
								self.parts[part_name] = part[2:-2]

							part = b""
							part_type = ""
							part_name = ""
							had_type = False
							had_name = False

						# Part name is specified by Content-Disposition, so get it if we see it
						elif not had_name and b"Content-Disposition: " in line:
							part_name = line.decode('ascii').split("name=")[-1].replace("\"", "")
						# Part type is specified by Content-Type
						elif not had_type and b"Content-Type: " in line:
							part_type = line.decode('ascii').split("Content-Type: ")[-1]
						elif had_name and had_type and part == b"":
							continue
						else:
							# Otherwise just add it to the part
							part += line + b"\r\n"
