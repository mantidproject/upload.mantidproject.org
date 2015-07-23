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
from urlparse import parse_qs

from .base import ScriptRemovalForm, ScriptUploadForm, ServerResponse
from .errors import BadRequestException, InternalServerError, RequestException
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
COMMITTER_NAME = "mantid-publisher"

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
    try:
        script_form, debug = parse_request(environ)
    # except BadRequestException, err:
    #     return err.response()

    # try:
        local_repo_root = get_local_repo_path(environ, debug)
    # except InternalServerError, err:
    #     return err.response()

    # # Process payload
    # try:
        return update_central_repo(local_repo_root, script_form)
    except RequestException, err:
        return err.response()

def null_handler(environ):
    return ServerResponse(httplib.METHOD_NOT_ALLOWED, message=u'Endpoint is ready to accept form uploads.')

# ------------------------------------------------------------------------------
# Request checks
# ------------------------------------------------------------------------------
def parse_request(environ):
    """Check the request return the type to the caller
    """
    query_params = parse_qs(environ["QUERY_STRING"])
    is_upload = ("remove" not in query_params)
    debug = ("debug" in query_params)

    if is_upload:
        cls = ScriptUploadForm
    else:
        cls = ScriptRemovalForm
    script_form, error = cls.create(environ)
    if error:
        raise BadRequestException(summary=error[0], detail='\n'.join(error[1:]))

    return script_form, debug

def get_local_repo_path(environ, debug):
    envvar = 'SCRIPT_REPOSITORY_PATH'
    if debug:
        envvar += "_DEBUG"
    try:
        return environ[envvar]
    except KeyError:
        raise InternalServerError()

# ------------------------------------------------------------------------------
# Repository update
# ------------------------------------------------------------------------------
def update_central_repo(local_repo_root, script_form):
    """This assumes that the script is running as a user who has permissions
    to push to the central github repository
    """
    git_repo = GitRepository(local_repo_root)
    # size limit
    if script_form.filesize > MAX_FILESIZE_BYTES:
        raise BadRequestException("File is too large.",
                                  "Maximum filesize is {0} bytes".format(MAX_FILESIZE_BYTES))

    return push_to_repository(script_form, git_repo)

def push_to_repository(script_form, git_repo):
    filepath, error = script_form.write_script_to_disk(git_repo.root)
    if error:
        raise InternalServerError(error[0], "\n".join(error[1:]))

    commit_info = GitCommitInfo(author=script_form.author,
                                email=script_form.mail,
                                comment=script_form.comment,
                                filelist=[filepath],
                                committer=COMMITTER_NAME)

    error = git_repo.commit_and_push(commit_info)
    if error:
        raise InternalServerError(error[0], "\n".join(error[1:]))

    return ServerResponse(httplib.OK, message="success",
                          published_date=published_date(filepath))

def published_date(filepath):
    timeformat = "%Y-%b-%d %H:%M:%S"
    stat = os.stat(filepath)
    modified_time = int(stat.st_mtime)
    # The original code added 2 minutes to the modification date of the file
    # so we preserve this behaviour here
    return time.strftime(timeformat, time.gmtime(modified_time + 120))
