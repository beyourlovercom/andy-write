"""Public benchmark fetching is read-only and must not leak raw HTML to Git."""
from __future__ import annotations
import pathlib
import tempfile
import unittest
from unittest.mock import patch,Mock
from scripts.fetch_public_wp_benchmark import fetch
from andy_write.io import ROOT

class QCFetchSafetyTests(unittest.TestCase):
    def test_explicit_2026_window_only_and_exact_slug(self):
        (ROOT / ".runs").mkdir(exist_ok=True)
        record = {"id": 313, "slug": "public-cleaning", "date": "2026-05-27T12:00:00",
                  "modified": "2026-07-28T10:00:00",
                  "link": "https://kissself.com/public-cleaning.html",
                  "content": {"rendered": "<p>Synthetic fixture only.</p>"}}
        class Response:
            status = 200
            def geturl(self):
                return "https://kissself.com/wp-json/wp/v2/posts?slug=public-cleaning"
            def read(self, n):
                return __import__("json").dumps([record]).encode("utf-8")
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
        with tempfile.TemporaryDirectory(dir=ROOT / ".runs") as folder:
            target = pathlib.Path(folder) / "post.json"
            with patch("scripts.fetch_public_wp_benchmark.urllib.request.urlopen",
                       return_value=Response()):
                with self.assertRaisesRegex(ValueError,"publication outside"):
                    fetch("https://kissself.com", "public-cleaning", target)
                report = fetch("https://kissself.com", "public-cleaning", target,
                               published_from="2026-01-01", published_through="2026-12-31")
            self.assertEqual(report["id"], 313)
            self.assertTrue(target.is_file())
            self.assertFalse(report["original_publication_revision_verified"])
            record["slug"] = "other-article"
            with patch("scripts.fetch_public_wp_benchmark.urllib.request.urlopen",
                       return_value=Response()):
                with self.assertRaisesRegex(RuntimeError,"slug differs"):
                    fetch("https://kissself.com", "public-cleaning", target,
                          published_from="2026-01-01", published_through="2026-12-31")

    def test_bad_date_bounds_refused_before_network(self):
        with patch("scripts.fetch_public_wp_benchmark.urllib.request.urlopen") as client:
            with self.assertRaisesRegex(ValueError,"both endpoints"):
                fetch("https://kissself.com", "public-cleaning",
                      ROOT / ".runs" / "throwaway.json",published_from="2026-01-01")
            with self.assertRaisesRegex(ValueError,"reversed"):
                fetch("https://kissself.com", "public-cleaning",
                      ROOT / ".runs" / "throwaway.json",
                      published_from="2026-12-31",published_through="2026-01-01")
            client.assert_not_called()

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
