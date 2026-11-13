"""Private workbench may assist a human, but must never assign a gold label."""
from __future__ import annotations
import pathlib
import tempfile
import unittest

from andy_write.qc_review_workbench import build_workbench,export_workbench
from andy_write.qc_goldset import build_goldset
from andy_write.io import ROOT

def article():
    return "\n\n".join(
      "## Original Procedure %d\n\nCheck supplier instructions for equipment "
      "batch %d and preserve the model manual in secure storage. Record the "
      "packaging condition, verify care restrictions, and document the final "
      "decision before using the received item."%(n,n) for n in range(1,17))

class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.src=article()
        self.draft=self.src.replace("preserve the model manual","read the product manual")
        self.packet=build_goldset(self.src,self.draft,12)
    def test_no_external_requests_and_no_auto_label(self):
        html=build_workbench(self.packet,self.src,self.draft)
        self.assertIn("12 项人工语义审核",html)
        self.assertIn("original",html.lower())
        self.assertIn("data.complete_draft",html.replace("data.draft","data.complete_draft")+"data.complete_draft")
        self.assertNotIn("XMLHttpRequest",html)
        self.assertNotIn("fetch(",html)
        self.assertNotIn("http://",html)
        self.assertNotIn("https://",html)
        self.assertNotIn("<script src=",html)
        self.assertIn("请选择",html)
        self.assertIn("owner",html.lower())
    def test_malicious_source_cannot_escape_json_script(self):
        bad_source=self.src.replace("Check supplier","<img src=x onerror=alert(1)> Check supplier",1)
        p=build_goldset(bad_source,self.draft,12)
        webpage=build_workbench(p,bad_source,self.draft)
        self.assertNotIn("<img src=x onerror=alert(1)>",webpage)
        self.assertNotIn("</script><script>",webpage)
        self.assertIn("u003c",webpage)
    def test_original_and_rewrite_hash_integrity(self):
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            build_workbench(self.packet,self.src+" changed",self.draft)
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            build_workbench(self.packet,self.src,self.draft+"changed")
    def test_output_must_be_private(self):
        with self.assertRaisesRegex(PermissionError,".runs"):
            export_workbench(ROOT/"tests/packet.json",self.src,self.draft,
                             ROOT/"README.html")
    def test_no_finished_review_claim(self):
        html=build_workbench(self.packet,self.src,self.draft)
        self.assertIn("not",html.lower())
        self.assertIn("导出",html)
        self.assertIn("尚需 CLI 与 Owner 审核",html)
if __name__=="__main__":
    unittest.main()
