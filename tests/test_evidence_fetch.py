"""Untrusted public evidence must be bounded and never escape private runtime."""
from __future__ import annotations
import pathlib
from unittest.mock import patch
import unittest
from andy_write.evidence_fetch import (
    approved_url,fetch,fetch_pack,SafeSameHostRedirect
)

class _Response:
    status=200
    headers={"Content-Type":"text/html; charset=utf-8"}
    def __init__(self,url="https://consumer.ftc.gov/articles/online-shopping"):
        self.url=url
    def geturl(self):return self.url
    def read(self,n):
        return (b"<html><body>"
                b"<p>Keep a record of a customer order and save receipts "
                b"when documenting an online transaction.</p>"
                b"<p>Check the merchant return policy in advance of an online "
                b"purchase and save messages for your records.</p></body></html>")
    def __enter__(self):return self
    def __exit__(self,*a):return None

class EvidenceFetchTests(unittest.TestCase):
    def test_disallow_unreviewed_domain_and_non_https(self):
        for bad in ("http://consumer.ftc.gov/articles/online-shopping",
                    "https://example.com/verify",
                    "https://localhost/personal",
                    "https://127.0.0.1/"):
            with self.subTest(url=bad):
                with self.assertRaises(ValueError):
                    approved_url(bad)

    def test_private_output_required_before_network(self):
        with patch("andy_write.evidence_fetch.fetch") as remote:
            with self.assertRaisesRegex(PermissionError,".runs"):
                fetch_pack(["https://consumer.ftc.gov/articles/online-shopping"],
                           pathlib.Path("docs/source-full-copy.json"))
            remote.assert_not_called()

    def test_actual_extracted_text_requires_provenance(self):
        class Opener:
            def open(self,*a,**kw):return _Response()
        with patch("andy_write.evidence_fetch.urllib.request.build_opener",
                   return_value=Opener()):
            source=fetch("https://consumer.ftc.gov/articles/online-shopping")
        self.assertEqual(source["source_kind"],"public_web_retrieval")
        self.assertEqual(source["retrieval_channel"],"direct_read_only_html")
        self.assertEqual(len(source["paragraphs"]),2)
        self.assertTrue(source["body_sha256"])
        self.assertFalse(source["semantic_support_verified"])

    def test_http_error_is_never_forged_as_retrieved(self):
        class Broken:
            def open(self,*a,**kw):raise RuntimeError("HTTP 403")
        with patch("andy_write.evidence_fetch.urllib.request.build_opener",
                   return_value=Broken()):
            with self.assertRaisesRegex(RuntimeError,"403"):
                fetch("https://www.cdc.gov/niosh/ergonomics/")

    def test_cross_host_redirect_blocked(self):
        handler=SafeSameHostRedirect()
        from urllib.request import Request
        with self.assertRaises(RuntimeError):
            handler.redirect_request(
                Request("https://consumer.ftc.gov/articles/online-shopping"),
                None,301,"Moved",{},
                "https://www.cdc.gov/niosh/ergonomics/")

if __name__=="__main__":
    unittest.main()
