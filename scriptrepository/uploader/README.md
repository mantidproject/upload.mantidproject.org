WSGI Upload Server
==================

A small Python application using the wsgi interface to receive multipart form data indicating a script to upload to the mantid script repository at https://www.github.com/mantidproject/scriptrepository

Requirements:

* A web server providing >= v3.0 of the wsgi interface so that it supports chunked transfer encoding natively

The Dockerfile is provided for testing to setup a mirror of the server it is currently running on.

Testing requires the following packages:

* `httplib2`
* `wsgi_intercept`
