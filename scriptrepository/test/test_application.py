import httplib2
import json
import os
import sys
import unittest
from urllib import urlencode
from wsgi_intercept import httplib2_intercept, add_wsgi_intercept

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "application"))
from server import application

# Local server URL
HOST = 'localhost'
PORT = 80
URL = 'http://{0}:{1}/'.format(HOST, PORT)

# ------------------------------------------------------------------------------
def setUpModule():
    def make_app():
        return application
    httplib2_intercept.install()
    add_wsgi_intercept(HOST, PORT, make_app)

def tearDownModule():
    httplib2_intercept.uninstall()
# ------------------------------------------------------------------------------

class ScriptUploadServerTest(unittest.TestCase):

    # ---------------- Failure cases ---------------------

    def test_app_returns_405_for_non_POST_requests(self):
        http = httplib2.Http()
        resp, content = http.request(URL)
        expected_resp = {
            'status': '405',
            'content-length': '99',
            'content-type': 'application/json; charset=utf-8'
        }
        self.check_response(expected=expected_resp, actual=resp)
        self.check_replied_content(expected=dict(message='Endpoint is ready to accept form uploads.', detail='',
                                                          pub_date='', shell=''), actual=content)

    def test_POST_of_form_without_all_information_produces_400_error(self):
        http = httplib2.Http()
        data = dict(author='Joe Bloggs', mail='first.last@domain.com', comment='Test comment', path='muon')
        resp, content = http.request(uri=URL, method='POST', body=urlencode(data))
        expected_resp = {
            'status': '400',
            'content-length': '115',
            'content-type': 'application/json; charset=utf-8'
        }
        self.check_response(expected=expected_resp, actual=resp)
        self.check_replied_content(expected=dict(message='Incomplete form information supplied.',
                                                 detail='Missing fields: file', pub_date='', shell=''),
                                   actual=content)

    def test_POST_of_form_with_invalid_fields_produces_400_error(self):
        http = httplib2.Http()
        data = dict(author='', mail='', comment='', path='')
        resp, content = http.request(uri=URL, method='POST', body=urlencode(data))
        expected_resp = {
            'status': '400',
            'content-length': '157',
            'content-type': 'application/json; charset=utf-8'
        }
        self.check_response(expected=expected_resp, actual=resp)
        self.check_replied_content(expected=dict(message='Incomplete form information supplied.',
                                                 detail='Missing fields: file\nInvalid fields: author,mail,comment,path',
                                                 pub_date='', shell=''),
                                   actual=content)

    # -------------------------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------------------------

    def check_response(self, expected, actual):
        self.assertEquals(expected, actual)

    def check_replied_content(self, expected, actual):
        self.assertEquals(json.dumps(expected), actual)


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
