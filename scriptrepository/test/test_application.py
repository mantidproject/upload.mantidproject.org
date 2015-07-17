import httplib2
import os
import sys
import unittest

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

    def test_app_ignores_non_POST_requests(self):
        http = httplib2.Http()
        resp, content = http.request(URL)
        expected_resp = {
            'status': '200',
            'content-length': '7',
            'content-type': 'application/json',
            'content-location': 'http://localhost:80/'
        }
        self.assertEquals(expected_resp, resp)
        self.assertEquals(b'Ignored', content)

    def test_POST_of_non_form_data_is_ignored(self):
        data = "{'a': 'b', 'c': 'd'}"
        http = httplib2.Http()
        resp, content = http.request(
            uri=URL,
            method='POST',
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            body=data
        )
        expected_resp = {
            'status': '200',
            'content-length': '7',
            'content-type': 'application/json'
        }
        self.assertEquals(expected_resp, resp)
        self.assertEquals(b'Ignored', content)

    def test_POST_of_form_without_all_information_produces_400_error(self):
        pass

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
