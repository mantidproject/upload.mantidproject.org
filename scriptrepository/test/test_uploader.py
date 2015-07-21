import datetime
import httplib2
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
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
# Temporary git repository path
TEMP_GIT_REMOTE_PATH = os.path.join(tempfile.gettempdir(), "scriptrepository_unittest_remote")

SCRIPT_CONTENT = \
"""
def hello(name):
    print "Hello, World"
"""

# ------------------------------------------------------------------------------
def setUpModule():
    global TEST_APP
    TEST_APP = TestApp(application)
    _setup_test_git_repos()

def tearDownModule():
    shutil.rmtree(TEMP_GIT_REPO_PATH)
    shutil.rmtree(TEMP_GIT_REMOTE_PATH)

def _setup_test_git_repos():
    os.mkdir(TEMP_GIT_REMOTE_PATH)
    start_dir = os.getcwd()

    # Init the remote
    os.chdir(TEMP_GIT_REMOTE_PATH)
    subprocess.check_output("git init", stderr=subprocess.STDOUT, shell=True)
    # Create a commit so we can use reset
    readme = os.path.join(TEMP_GIT_REMOTE_PATH, "README.md")
    open(readme, 'w').write("foo")
    subprocess.check_output("git add .; git commit -m'Initial commit';exit 0",
                            stderr=subprocess.STDOUT, shell=True)
    # Clone this so that the clone will have a remote
    os.chdir(os.path.dirname(TEMP_GIT_REPO_PATH))
    cmd = "git clone {0} {1}; exit 0".format(TEMP_GIT_REMOTE_PATH, TEMP_GIT_REPO_PATH)
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)

    # Go back to where we started
    os.chdir(start_dir)


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
            'content-length': 85,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected_json=dict(message='success', detail='',
                                                      pub_date=self._now_as_str(), shell=''),
                                   actual_str=response.body)

    # ---------------- Failure cases ---------------------

    def test_app_returns_405_for_non_POST_requests(self):
        response = TEST_APP.get('/', expect_errors=True)
        expected_resp = {
            'status': '405 Method Not Allowed',
            'content-length': 99,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected_json=dict(message='Endpoint is ready to accept form uploads.', detail='',
                                                      pub_date='', shell=''), actual_str=response.body)

    def test_POST_of_form_without_all_information_produces_400_error(self):
        data = dict(author='Joe Bloggs', mail='first.last@domain.com', comment='Test comment', path='./muon')
        response = TEST_APP.post('/', data, expect_errors=True)
        expected_resp = {
            'status': '400 Bad Request',
            'content-length': 115,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected_json=dict(message='Incomplete form information supplied.',
                                                      detail='Missing fields: file', pub_date='', shell=''),
                                   actual_str=response.body)

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
        self.check_replied_content(expected_json=expected_content,
                                   actual_str=response.body)

    def test_script_over_max_size_returns_400_error(self):
        extra_environ = {"SCRIPT_REPOSITORY_PATH": TEMP_GIT_REPO_PATH}
        data = dict(author='Joe Bloggs', mail='first.last@domain.com', comment='Test comment', path='./muon')
        # Write a "big" file
        big_script = tempfile.NamedTemporaryFile(delete=False)
        limit = 1024*1024
        for i in range(limit + 1):
            big_script.write("1")
        big_script.close()

        response = TEST_APP.post('/', extra_environ=extra_environ, expect_errors=True,
                                 params=data, upload_files=[("file", big_script.name)])
        os.remove(big_script.name)
        expected_resp = {
            'status': '400 Bad Request',
            'content-length': 109,
            'content-type': 'application/json'
        }
        self.check_response(expected=expected_resp, actual=response)
        self.check_replied_content(expected_json=dict(message='File is too large.', detail='Maximum filesize is 1048576 bytes',
                                                      pub_date='', shell=''), actual_str=response.body)


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
        self.check_replied_content(expected_json=dict(message='Server Error. Please contact Mantid support.', detail='',
                                                      pub_date='', shell=''), actual_str=response.body)

    # -------------------------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------------------------

    def check_response(self, expected, actual):
        self.assertEquals(expected['status'], actual.status)
        self.assertEquals(expected['content-type'], actual.content_type)
        self.assertEquals(expected['content-length'], actual.content_length)

    def check_replied_content(self, expected_json, actual_str):
        actual_json = json.loads(actual_str)
        # Check the published date manually
        actual_pub_date = actual_json["pub_date"]
        del actual_json["pub_date"]
        expected_pub_date = expected_json["pub_date"]
        del expected_json["pub_date"]

        self.assertEquals(expected_json, actual_json)
        # The pub_date is simply checked that the date portion agrees
        if (expected_pub_date != actual_pub_date) and (expected_pub_date != ''):
            # create full datetime objects from both
            expected_date = datetime.datetime.strptime(expected_pub_date, "%Y-%b-%d %H:%M:%S")
            try:
                actual_date = datetime.datetime.strptime(actual_pub_date, "%Y-%b-%d %H:%M:%S")
            except ValueError:
                self.fail("response pub_date '{0}' cannot be parsed as a datetime object".format(actual_pub_date))
            # Just check the dates
            self.assertEquals(self._date_as_str(expected_date.date()), self._date_as_str(actual_date))

    def _now_as_str(self):
        return datetime.date.today().strftime("%Y-%b-%d %H:%M:%S")

    def _date_as_str(self, date):
        return date.strftime("%Y-%b-%d")

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
