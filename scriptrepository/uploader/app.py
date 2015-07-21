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
from __future__ import absolute_import, print_function

import httplib
import os

from .base import ScriptUploadForm, ServerResponse

# Map requests to handlers
# Each handler should have the following structure:
#   def foo_handle(environ)
#      # process the request
#      ...
#      ...
#      return ServerResponse(status_code, ...)
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
        return ServerResponse(httplib.BAD_REQUEST, message=error[0], detail='\n'.join(error[1:]))

    # Process payload
    return update_central_repo(environ, script_form)

def null_handler(environ):
    return ServerResponse(httplib.METHOD_NOT_ALLOWED, message=u'Endpoint is ready to accept form uploads.')

# ------------------------------------------------------------------------------
# Repository update
# ------------------------------------------------------------------------------
def update_central_repo(environ, script_form):
    """This assumes that the script is running as a user who has permissions
    to push to the central github repository
    """
    try:
        script_repo_path = environ["SCRIPT_REPOSITORY_PATH"]
    except KeyError:
        environ["wsgi.errors"].write("Invalid server configuration: SCRIPT_REPOSITORY_PATH environment variable not defined.\n")
        return ServerResponse(httplib.INTERNAL_SERVER_ERROR, message="Server Error. Please contact Mantid support.")

    return ServerResponse(httplib.OK, message="success")


class GitRepository(object):
     """Models a git repo. Currently it needs to have been cloned first.
     """
     def __init__(self, path):
         if not os.path.exists(path):
             raise ValueError("Unable to find git repository at '{0}'. "\
                              "It must be have been cloned first.".format(path))
         self.root = path
