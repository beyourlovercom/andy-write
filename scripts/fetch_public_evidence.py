#!/usr/bin/env python3
"""Fetch 1-5 explicitly supplied official public source pages for local QA."""
import argparse
import json
import pathlib
import sys
if __package__ in (None,""):
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from andy_write.evidence_fetch import fetch_pack

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",action="append",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    print(json.dumps(fetch_pack(args.url,pathlib.Path(args.out)),indent=2))
if __name__=="__main__":
    main()
