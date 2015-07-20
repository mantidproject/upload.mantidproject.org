"""Defines the WSGI application entry point for the upload server

In order to submit a file, it is necessary to POST a form with the
following fields:
  - author: Name of the author of the file.
  - email: Email of the author.
  - comment: a description of the file or updates it is being done.
  - file: The file itself.
  - path: The folder where the file must be inserted.

If the values are all valid then the files are committed and uploaded
to the central repository using:
  - git add <file>
  - git commit -m "<comment>" --author "<author> <<email>>"
  - git push

The response body will be a json-encoded dictionary containing:
  - message: one of two strings ['success', 'failure] depending on the outcome
  - detail: if an error occurred then further details are provided here
  - pub_date: the date and time of the upload in the format  %Y-%b-%d %H:%M:%S
  - shell: The commands that were run by the server

The server understands a single query parameter 'debug=1' and when set the
upload will go to the sandbox testing repository.
"""
import cgi
import os

# Map requests to handlers
_REQUEST_HANDLERS = {
#    'POST': 'handle_post'
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
    status, response_headers, response_body = globals()[handle_attr](environ)
    # Begin response
    start_response(status, response_headers)
    return [response_body]

# ------------------------------------------------------------------------------
# Handler methods
# ------------------------------------------------------------------------------
def null_handler(environ):
    status = '200 OK'
    response_body = "Ignored"
    response_headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body)))
    ]
    return status, response_headers, response_body
