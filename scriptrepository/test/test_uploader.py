import httplib2
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib import urlencode
from webtest import TestApp

# Our application
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from uploader.app import application

# Local server
TEST_APP = None
# Temporary git repository path
TEMP_GIT_REPO_PATH = os.path.join(tempfile.gettempdir(), "scriptrepository_unittest")

SCRIPT_CONTENT = \
"""
def hello(name):
    print "Hello, World"
"""

# ------------------------------------------------------------------------------
def setUpModule():
    global TEST_APP
    TEST_APP = TestApp(application)
    os.mkdir(TEMP_GIT_REPO_PATH)
    start_dir = os.getcwd()
    os.chdir(TEMP_GIT_REPO_PATH)
    subprocess.check_output("git init", stderr=subprocess.STDOUT, shell=True)
    os.chdir(start_dir)

def tearDownModule():
    shutil.rmtree(TEMP_GIT_REPO_PATH)

# ------------------------------------------------------------------------------

class ScriptUploadServerTest(unittest.TestCase):

    # ---------------- Success cases ---------------------
    def test_app_returns_200_for_successful_upload(self):
        extra_environ = {"SCRIPT_REPOSITORY_PATH": TEMP_GIT_REPO_PATH}
        data = dict(author='Joe Bloggs', mail='first.last@domain.com', comment='Test comment', path='./muon')
        response = TEST_APP.post('/', extra_environ=extra_environ,
                                 params=data, upload_files=[("file", "userscript.py", SCRIPT_CONTENT)])
        expected_resp = {
            'status': '200 OK',
            'content-length': 65,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected=dict(message='success', detail='',
                                                 pub_date='', shell=''), actual=response.body)

    # ---------------- Failure cases ---------------------

    def test_app_returns_405_for_non_POST_requests(self):
        response = TEST_APP.get('/', expect_errors=True)
        expected_resp = {
            'status': '405 Method Not Allowed',
            'content-length': 99,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected=dict(message='Endpoint is ready to accept form uploads.', detail='',
                                                 pub_date='', shell=''), actual=response.body)

    def test_POST_of_form_without_all_information_produces_400_error(self):
        data = dict(author='Joe Bloggs', mail='first.last@domain.com', comment='Test comment', path='./muon')
        response = TEST_APP.post('/', data, expect_errors=True)
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
        data = dict(author='', mail='joe.bloggs', comment='', path='')
        response = TEST_APP.post('/', data, expect_errors=True)
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

    def test_server_without_correct_environment_returns_500_error(self):
        data = dict(author='Joe Bloggs', mail='first.last@domain.com', comment='Test comment', path='./muon')
        response = TEST_APP.post('/', data, upload_files=[("file", "userscript.py", SCRIPT_CONTENT)],
                                 expect_errors=True)
        expected_resp = {
            'status': '500 Internal Server Error',
            'content-length': 102,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected=dict(message='Server Error. Please contact Mantid support.', detail='',
                                                 pub_date='', shell=''), actual=response.body)

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
