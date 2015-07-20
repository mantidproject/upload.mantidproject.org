"""Defines the WSGI application entry point for the upload server

In order to submit a file, it is necessary to POST a form with the
following fields:
  - author: Name of the author of the file.
  - mail: Email of the author.
  - comment: a description of the file or updates it is being done.
  - file: The file itself.
  - path: The folder where the file must be inserted.

If the values are all valid then the files are committed and uploaded
to the central repository using:
  - git add <file>
  - git commit -m "<comment>" --author "<author> <<email>>"
  - git push

The response body will be a json-encoded dictionary containing:
  - message: A string containing an information message on the outcome of the request. For
             success it is simply 'success'
  - detail: if an error occurred then further details are provided here
  - pub_date: the date and time of the upload in the format  %Y-%b-%d %H:%M:%S
  - shell: The commands that were run by the server

Only POST requests are accepted, any other type will result in a 405 error.

Several query parameters are understood:
 - remove=1: if included the file will be removed rather than uploaded
 - debug=1: if included then the update will happen in the sandbox repository
"""
import cgi
import httplib
import json
import os

# Map requests to handlers
# Each handler should have the following structure:
#   def foo_handle(environ)
#      # process the request
#      ...
#      ...
#      return Response(status_code, ...)
_REQUEST_HANDLERS = {
    'POST': 'handle_post'
}

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
def application(environ, start_response):
    """Called by the webserver when the URL is hit
      :param environ A dictionary of context variables
      :start_response A callback function that will the response to the client
    """
    # Find handler
    handle_attr = _REQUEST_HANDLERS.get(environ['REQUEST_METHOD'],
                                        'null_handler')
    response = globals()[handle_attr](environ)
    # Begin response
    start_response(response.status, response.headers)
    # It is important to return the content within another iterable. The caller
    # iterates over the returned iterable and sends data back with each iteration.
    # The list makes this happen in 1 go
    return [response.content]

# ------------------------------------------------------------------------------
# Handler methods
# ------------------------------------------------------------------------------
def handle_post(environ):
    script_form, error = ScriptUploadForm.create(environ)
    if error is not None:
        return Response(httplib.BAD_REQUEST, message=error[0], detail='\n'.join(error[1:]))

    # Process payload
    resp_body, error = update_central_repo(environ, script_form)
    # Response
    status = create_status_response(httplib.OK) if error is None else create_status_response(httplib.BAD_REQUEST)
    response_body = create_response_body('success', '')
    response_headers = create_response_headers(len(response_body))
    return status, response_headers, response_body

def null_handler(environ):
    return Response(httplib.METHOD_NOT_ALLOWED, message=u'Endpoint is ready to accept form uploads.')

# ------------------------------------------------------------------------------
# Repository update
# ------------------------------------------------------------------------------
def update_central_repo(environ, script_form):
    """This assumes that the script is running as a user who has permissions
    to push to the central github repository
    """
    pass
    #git_repo = GitRepository(environ["SCRIPT_REPOSITORY_PATH"])

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
class ScriptUploadForm(object):
    """Defines the incoming payload from the client
    """
    required_fields = ("author", "mail", "comment", "path", "file")

    @classmethod
    def create(cls, environ):
        request_fields = cgi.FieldStorage(fp=environ['wsgi.input'],
                                          environ=environ, keep_blank_values=1)
        # sanity check
        data = dict()
        missing, invalid = [], []
        for name in cls.required_fields:
            if name in request_fields:
                value = request_fields[name].value
                if value:
                    data[name] = value
                else:
                    invalid.append(name)
            else:
                missing.append(name)
        #endfor
        if len(missing) == 0 and len(invalid) == 0:
            return ScriptUploadForm(**data), None
        else:
            summary = 'Incomplete form information supplied.'
            detail = []
            if len(missing) > 0:
                detail.append('Missing fields: ' + ','.join(missing))
            if len(invalid) > 0:
                detail.append('Invalid fields: ' + ','.join(invalid))
            return None, (summary, "\n".join(detail))

    def __init__(self, author, mail, comment, path, file):
        self.author = author
        self.mail = mail
        self.comment = comment
        self.path = path
        self.file = file

class Response(object):

    def __init__(self, status_code, message, detail=None,
                 published_date=None, shell=None):
        self._create_status(status_code)
        self._create_body(message, detail,
                          published_date, shell)
        self._create_headers()

    def _create_status(self, code):
        self.status = "{0} {1}".format(str(code), httplib.responses[code])

    def _create_headers(self):
        self.headers = [
            ('Content-Type', 'application/json; charset=utf-8'),
            ('Content-Length', str(len(self.content)))
        ]

    def _create_body(self, message, detail, published_date, shell):
        detail = detail if detail is not None else ""
        pub_date = published_date if published_date is not None else ""
        shell = shell if shell is not None else ""
        data = dict(message=message, detail=detail, pub_date=pub_date, shell=shell)
        self.content = json.dumps(data, encoding='utf-8')

class GitRepository(object):
     """Models a git repo. Currently it needs to have been cloned first.
     """
     def __init__(self, path):
         if not os.path.exists(path):
             raise ValueError("Unable to find git repository at '{0}'. "\
                              "It must be have been cloned first.".format(path))
         self.root = path
