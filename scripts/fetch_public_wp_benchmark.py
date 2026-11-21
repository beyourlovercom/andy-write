#!/usr/bin/env python3
"""Read-only bounded public WordPress benchmark fetch to private .runs only.

Do not publish, alter the remote site, scrape authenticated endpoints or
send competitor article bodies to any writing model.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
if __package__ in (None, ""):
    import sys
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from andy_write.io import ROOT
from andy_write.research import validate_public_url

LIMIT=1000000
FIELDS="id,slug,date,modified,link,title,content,excerpt"
def fetch(site:str,slug:str,dest:pathlib.Path,*,
          published_from:str|None=None,published_through:str|None=None)->dict:
    site=site.rstrip("/")
    validate_public_url(site)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",slug):
        raise ValueError("Unsafe WP post slug")
    if (published_from is None) != (published_through is None):
        raise ValueError("Explicit date bounds require both endpoints")
    if published_from is None:
        start,end=date(2025,11,1),date(2025,12,31)
    else:
        start,end=date.fromisoformat(published_from),date.fromisoformat(published_through)
        if start>end:
            raise ValueError("Public benchmark date bounds are reversed")
    private=(ROOT/".runs").resolve()
    output=dest.resolve()
    if not output.is_relative_to(private):
        raise ValueError("Public benchmark source must remain in Git-ignored .runs")
    host=urllib.parse.urlsplit(site).hostname
    query=urllib.parse.urlencode({"slug":slug,"per_page":1,"_fields":FIELDS})
    url=site+"/wp-json/wp/v2/posts?"+query
    validate_public_url(url)
    req=urllib.request.Request(url,headers={"User-Agent":"AndyWriteQCBenchmark/1.2 (read-only)"})
    with urllib.request.urlopen(req,timeout=22) as resp:
        if resp.status!=200:
            raise RuntimeError("Public WP REST fetch returned non-200 status")
        final=resp.geturl()
        if (urllib.parse.urlsplit(final).scheme!="https" or
            urllib.parse.urlsplit(final).hostname!=host):
            raise RuntimeError("Public benchmark redirected to another site")
        raw=resp.read(LIMIT+1)
    if len(raw)>LIMIT:
        raise RuntimeError("Source exceeded safe benchmark size limit")
    data=json.loads(raw.decode("utf-8"))
    if not isinstance(data,list) or len(data)!=1:
        raise RuntimeError("No single matching public article; do not guess")
    record=data[0]
    if record.get("slug")!=slug:
        raise RuntimeError("Public REST article slug differs from requested identity")
    publication=date.fromisoformat(record.get("date","")[:10])
    if not start<=publication<=end:
        raise ValueError("Public article publication outside explicit benchmark window")
    link=urllib.parse.urlsplit(record["link"])
    if link.scheme!="https" or (link.hostname or "").removeprefix("www.") != host.removeprefix("www."):
        raise RuntimeError("REST article URL host mismatch")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(record,ensure_ascii=False)+"\n",encoding="utf-8")
    return {
      "id":record["id"],"date":record["date"],
      "modified":record.get("modified"),"url":record["link"],
      "local_private_file":str(output),
      "original_2025_snapshot_verified":False,
      "original_publication_revision_verified":False,
      "publication_window":{"start":start.isoformat(),"end":end.isoformat()},
      "warning":"Public WP REST gives current revision, not necessarily first published body"
    }

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--site",required=True)
    parser.add_argument("--slug",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--published-from",default=None,
                        help="Explicit YYYY-MM-DD start for a non-2025 benchmark")
    parser.add_argument("--published-through",default=None,
                        help="Explicit YYYY-MM-DD end for a non-2025 benchmark")
    args=parser.parse_args(argv)
    result=fetch(args.site,args.slug,pathlib.Path(args.out),
                 published_from=args.published_from,
                 published_through=args.published_through)
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    sys.exit(main())
