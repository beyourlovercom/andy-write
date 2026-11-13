"""Public benchmark fetching is read-only and must not leak raw HTML to Git."""
from __future__ import annotations
import pathlib
import tempfile
import unittest
from unittest.mock import patch,Mock
from scripts.fetch_public_wp_benchmark import fetch

class QCFetchSafetyTests(unittest.TestCase):
    def test_non_private_output_refused_before_network(self):
        with patch("scripts.fetch_public_wp_benchmark.urllib.request.urlopen") as client:
            with self.assertRaisesRegex(ValueError,"Git-ignored"):
                fetch("https://kissself.com","some-public-post",
                      pathlib.Path("docs/competitor-body.json"))
            client.assert_not_called()

    def test_unsafe_slug_rejected(self):
        with patch("scripts.fetch_public_wp_benchmark.urllib.request.urlopen") as client:
            with self.assertRaisesRegex(ValueError,"Unsafe WP post slug"):
                fetch("https://kissself.com","../wp-admin",
                      pathlib.Path(".runs/test-post.json"))
            client.assert_not_called()

    def test_no_http_or_private_host(self):
        with patch("scripts.fetch_public_wp_benchmark.urllib.request.urlopen") as client:
            for site in ("http://kissself.com","https://localhost",
                         "https://127.0.0.1"):
                with self.subTest(site=site):
                    with self.assertRaises(ValueError):
                        fetch(site,"public-guide",pathlib.Path(".runs/test-post.json"))
            client.assert_not_called()

    def test_missing_or_unexpected_rest_rows_rejected(self):
        import json
        class Response:
            status=200
            def geturl(self):return "https://kissself.com/wp-json/wp/v2/posts?slug=public-guide"
            def read(self,n):return b"[]"
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with patch("scripts.fetch_public_wp_benchmark.urllib.request.urlopen",
                   return_value=Response()):
            with self.assertRaisesRegex(RuntimeError,"single matching"):
                fetch("https://kissself.com","public-guide",
                      pathlib.Path(".runs/test-public-no-row.json"))

if __name__=="__main__":
    unittest.main()
