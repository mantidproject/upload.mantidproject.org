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

Only POST requests are accepted, any other type will result in a 405 error.

Several query parameters are understood:
 - remove=1: if included the file will be removed rather than uploaded
 - debug=1: if included then the update will happen in the sandbox repository
"""
from __future__ import absolute_import, print_function

import httplib
import os
import time

from .base import ScriptUploadForm, ServerResponse
from .repository import GitCommitInfo, GitRepository

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

# Maximum allowed file size
MAX_FILESIZE_BYTES=1*1024*1024

# Comitter's name
GIT_COMMITTER_NAME = "mantid-publisher"

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

    # size limit
    if script_form.filesize > MAX_FILESIZE_BYTES:
        return ServerResponse(httplib.BAD_REQUEST, message="File is too large.",
                              detail="Maximum filesize is {0} bytes".format(MAX_FILESIZE_BYTES))

    git_repo = GitRepository(script_repo_path)
    return push_to_repository(script_form, git_repo)


def push_to_repository(script_form, git_repo):
    filepath, error = script_form.write_script_to_disk(git_repo.root)
    if error:
        return ServerResponse(httplib.INTERNAL_SERVER_ERROR, message=error[0],
                              detail="\n".join(error[1:]))

    commit_info = GitCommitInfo(author=script_form.author,
                                email=script_form.mail,
                                filelist=[filepath],
                                committer=GIT_COMMITTER_NAME)
    error = git_repo.commit_and_push(commit_info)
    if error:
        return ServerResponse(httplib.INTERNAL_SERVER_ERROR,
                              message=error[0],
                              detail="\n".join(error[1:]))
    else:
        return ServerResponse(httplib.OK, message="success",
                              published_date=published_date(filepath))

def published_date(filepath):
    timeformat = "%Y-%b-%d %H:%M:%S"
    stat = os.stat(filepath)
    modified_time = int(stat.st_mtime)
    # The original code added 2 minutes to the modification date of the file
    # so we preserve this behaviour here
    return time.strftime(timeformat, time.gmtime(modified_time + 120))
