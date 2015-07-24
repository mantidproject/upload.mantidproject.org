upload.mantidproject.org
========================

Here you will find the web application that is responsible for interacting
with Mantid and the scriptrepository to allow uploading of new files.

The application itself uses only packages found in the Python standard library but it requires the `git` command to be accessible and executable. A clone of the repository is required and the web server must ensure that the `SCRIPT_REPOSITORY_PATH` environment points to the cloned copy. The webserver must also have permissions to write to those files and directories.


Docker Test Image
=================

The application can be tested under Apache using the provided `Dockerfile`
in the parent directory.

To build the image run (assuming you are in this directory):
```
docker build --rm -t scriptuploads
```
where it will be tagged `scriptuploads`.

Run the image in a new container with
```
docker run -p 5000:80 --rm --name=apache2.2 martyngigg/wsgi-test
```
where the container name is `apache2.2` and port 5000 on the host is mapped to port 80 on container.
