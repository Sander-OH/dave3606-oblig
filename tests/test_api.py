from mock_database import MockDatabase
import json
import gzip
import unittest
from server import app, cache


class ApiTest(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

        # Clear cache before each test
        cache.clear()

        import server
        server.Database = MockDatabase

    def test_api_set(self):
        response = self.client.get("/api/set?id=123")

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        self.assertEqual(data["id"], "123")
        self.assertEqual(data["name"], "Test Set")
        self.assertEqual(data["year"], 2020)
        self.assertEqual(data["category"], "Test Category")
        self.assertEqual(data["image"], "test.png")

        self.assertEqual(len(data["inventory"]), 2)

        self.assertEqual(data["inventory"][0]["brick_type_id"], "3001")
        self.assertEqual(data["inventory"][0]["count"], 4)


    def test_sets_endpoint(self):
        response = self.client.get("/sets")

        # Status code
        self.assertEqual(response.status_code, 200)

        # Check headers
        self.assertEqual(response.headers["Content-Encoding"], "gzip")
        self.assertIn("text/html", response.content_type)

        # Decompress response
        decompressed = gzip.decompress(response.data).decode("utf-8")

        # Check that rows are rendered correctly
        self.assertIn('<a href="/set?id=123">123</a>', decompressed)
        self.assertIn('<td>Test Set</td>', decompressed)

        self.assertIn('<a href="/set?id=456">456</a>', decompressed)
        self.assertIn('<td>Another Set</td>', decompressed)