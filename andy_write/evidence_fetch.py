"""Read-only, fail-closed public institutional evidence snapshot collector.

This fetches actual web paragraph content for OFFLINE claim-to-source review.
A retrieved institutional page is not proof a specific claim is true.
Never send content to Codex or upload to an external publishing service.
"""
from __future__ import annotations
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlsplit
import urllib.request

from .io import ROOT, hashtext, now
from .research import validate_public_url

CONTRACT="andy-write-curated-evidence-snapshot-v1.2.1"
MAX_BYTES=1600000
MAX_PARAS=250
ALLOWED_ROOTS=("ftc.gov","cdc.gov","fda.gov","nih.gov","nhs.uk","hse.gov.uk",
               "gov.uk","who.int")

def approved_url(url:str)->str:
    validate_public_url(url)
    host=(urlsplit(url).hostname or "").lower()
    if not any(host==root or host.endswith("."+root) for root in ALLOWED_ROOTS):
        raise ValueError("Unapproved public evidence domain; use explicit allowlist")
    return url

class SafeSameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        approved_url(newurl)
        old=(urlsplit(req.full_url).hostname or "").removeprefix("www.")
        new=(urlsplit(newurl).hostname or "").removeprefix("www.")
        # No cross-host redirects; prevents sending request to arbitrary
        # endpoints even when original is a trusted public organization.
        if old != new:
            raise RuntimeError("Cross-host evidence redirect blocked")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]
        self.blocked=0
        self.out=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","svg","noscript","template"):
            self.blocked+=1
        if tag in ("p","li","h1","h2","h3") and not self.blocked:
            self.stack.append([tag,[]])
    def handle_data(self,text):
        if not self.blocked:
            for unit in self.stack:
                unit[1].append(text)
    def handle_endtag(self,tag):
        if tag in ("script","style","svg","noscript","template"):
            self.blocked=max(0,self.blocked-1)
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                _,parts=self.stack.pop(i)
                passage=" ".join(" ".join(parts).split())
                if 35<=len(passage)<=3000:
                    self.out.append(passage)
                break

def fetch(url:str)->dict:
    approved_url(url)
    client=urllib.request.build_opener(SafeSameHostRedirect())
    request=urllib.request.Request(
        url,headers={"User-Agent":"AndyWriteEvidenceAudit/1.2 (read-only)",
                     "Accept":"text/html"})
    with client.open(request,timeout=20) as response:
        if response.status!=200:
            raise RuntimeError("Public evidence page not HTTP 200")
        approved_url(response.geturl())
        if response.headers.get("Content-Type","").split(";")[0].strip().lower() \
           not in ("text/html","application/xhtml+xml"):
            raise RuntimeError("Evidence page is not HTML")
        raw=response.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise RuntimeError("Evidence page exceeds bounded public HTML limit")
    parser=Paragraphs()
    parser.feed(raw.decode("utf-8",errors="replace"))
    passages=list(dict.fromkeys(parser.out))
    if not passages:
        raise RuntimeError("No verifiable HTML paragraphs extracted")
    if len(passages)>MAX_PARAS:
        # Explicitly fail rather than imply the page was analyzed in full.
        raise RuntimeError("Evidence page has too many paragraphs; use focused excerpt")
    body="\n\n".join(passages)
    return {
      "contract":CONTRACT,"source_kind":"public_web_retrieval",
      "retrieval_channel":"direct_read_only_html",
      "retrieval_status":"retrieved",
      "url":url,"retrieved_at":now(),
      "body_sha256":hashtext(body),"paragraphs":passages,
      "evidence_scope":"Retrieved paragraphs, not human fact verification",
      "semantic_support_verified":False,
      "generated_media":False,
    }

def fetch_pack(urls:list[str], path:Path)->dict:
    private=(ROOT/".runs").resolve()
    output=path.resolve()
    if not output.is_relative_to(private):
        raise PermissionError("Evidence page excerpts must remain in .runs")
    if not 1<=len(urls)<=5 or len(urls)!=len(set(urls)):
        raise ValueError("Specify 1-5 distinct curated official evidence URLs")
    for url in urls:
        approved_url(url)
    records=[fetch(url) for url in urls]
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n")
    return {"sources":len(records),
            "urls":[x["url"] for x in records],
            "output_path":str(output),
            "factual_verification":"PENDING"}
