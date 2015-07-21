"""A set of helpers to aid handling a request to upload a script file
"""
from __future__ import absolute_import, print_function

import cgi
import httplib
import json
import re

# Email regex
MAIL_RE = re.compile(r'[^@]+@[^@]+\.[^@]+')

# ------------------------------------------------------------------------------
class ScriptUploadForm(object):
    """Defines the incoming payload from the client and the fields that
       are expected
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
                if cls.validate_field(name, value):
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

    @classmethod
    def validate_field(cls, name, value):
        if name == "mail":
            return (MAIL_RE.match(value) is not None)
        elif name == "path":
            return ('./' in value and '../' not in value)
        else:
            return (value != '')

    def __init__(self, author, mail, comment, path, file):
        self.author = author
        self.mail = mail
        self.comment = comment
        self.path = path
        self.file = file

# ------------------------------------------------------------------------------

class ServerResponse(object):

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
