"""Defines the WSGI application entry point for the upload server

The server understands a single query parameter 'debug=1' and when set the
upload will got the sandbox testing repository
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
