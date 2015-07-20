import httplib2
import json
import os
import sys
import unittest
from urllib import urlencode
from webtest import TestApp

# Our application
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "application"))
from server import application

# Local server URL
HOST = 'localhost'
PORT = 80
URL = 'http://{0}:{1}/'.format(HOST, PORT)
TEST_APP = None

# ------------------------------------------------------------------------------
def setUpModule():
    global TEST_APP
    TEST_APP = TestApp(application)

# ------------------------------------------------------------------------------

class ScriptUploadServerTest(unittest.TestCase):

    # ---------------- Failure cases ---------------------

    def test_app_returns_405_for_non_POST_requests(self):
        response = TEST_APP.get('/', status=405)
        expected_resp = {
            'status': '405 Method Not Allowed',
            'content-length': 99,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected=dict(message='Endpoint is ready to accept form uploads.', detail='',
                                                 pub_date='', shell=''), actual=response.body)

    def test_POST_of_form_without_all_information_produces_400_error(self):
        data = dict(author='Joe Bloggs', mail='first.last@domain.com', comment='Test comment', path='muon')
        response = TEST_APP.post('/', data,
                                 status=400)
        expected_resp = {
            'status': '400 Bad Request',
            'content-length': 115,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected=dict(message='Incomplete form information supplied.',
                                                 detail='Missing fields: file', pub_date='', shell=''),
                                   actual=response.body)

    def test_POST_of_form_with_invalid_fields_produces_400_error(self):
        data = dict(author='', mail='', comment='', path='')
        response = TEST_APP.post('/', data,
                                 status=400)
        expected_resp = {
            'status': '400 Bad Request',
            'content-length': 157,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        expected_content = dict(message='Incomplete form information supplied.',
                                detail='Missing fields: file\nInvalid fields: author,mail,comment,path',
                                pub_date='', shell='')
        self.check_replied_content(expected=expected_content,
                                   actual=response.body)

    # def xtest_server_without_correct_environment_returns_500_error(self):
    #     http = httplib2.Http()
    #     data = dict(author='Joe Bloggs', mail='first.last@domain.com',
    #                 comment='Test comment', path='muon', file=)

    #     resp, content = http.request(uri=URL, method='POST', body=urlencode(data))
    #     expected_resp = {
    #         'status': '500',
    #         'content-length': '157',
    #         'content-type': 'application/json; charset=utf-8'
    #     }
    #     self.check_response(expected=expected_resp, actual=resp)
    #     expected_content = dict(message='Incomplete form information supplied.',
    #                             detail='', pub_date='', shell='')
    #     self.check_replied_content(expected=expected_content,
    #                                actual=content)

    # -------------------------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------------------------

    def check_response(self, expected, actual):
        self.assertEquals(expected['status'], actual.status)
        self.assertEquals(expected['content-type'], actual.content_type)
        self.assertEquals(expected['content-length'], actual.content_length)

    def check_replied_content(self, expected, actual):
        self.assertEquals(json.dumps(expected), actual)


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
