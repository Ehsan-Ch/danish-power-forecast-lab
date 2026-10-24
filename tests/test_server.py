import threading
import unittest
import urllib.request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from nordcast.server import Handler

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def test_public_assets(self):
        for path in ('/','/web/core.mjs','/reports/benchmark/results.json'):
            with urllib.request.urlopen(self.base+path) as r:self.assertEqual(r.status,200);self.assertTrue(r.read())
    def test_private_and_traversal_blocked(self):
        for path in ('/data/prices.json','/nordcast/data.py','/../README.md','/%2e%2e/README.md','/reports/benchmark/paper.sqlite'):
            with self.assertRaises(HTTPError) as e:urllib.request.urlopen(self.base+path)
            self.assertEqual(e.exception.code,404)
