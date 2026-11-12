"""R1 research. Curated URL retrieval is deliberately NOT described as SERP."""
from __future__ import annotations
import json
import ipaddress
import os
import re
import subprocess
import urllib.parse
from html.parser import HTMLParser
from .io import now

class PageExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._inside_title = False
        self._ignored = 0
        self.text_parts = []
        self._last_tag = ""

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg", "nav", "footer"):
            self._ignored += 1
        if tag == "title":
            self._inside_title = True
        self._last_tag = tag

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg", "nav", "footer") and self._ignored:
            self._ignored -= 1
        if tag == "title":
            self._inside_title = False

    def handle_data(self, data):
        value = " ".join(data.split())
        if not value or self._ignored:
            return
        if self._inside_title:
            self.title += " " + value
        elif self._last_tag in ("p", "h1", "h2", "h3", "li"):
            self.text_parts.append(value)

def validate_public_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    if parsed.username or parsed.password:
        raise ValueError("Credentials in source URLs are forbidden")
    if parsed.scheme != "https" or not host or host in ("localhost", "127.0.0.1"):
        raise ValueError("Only public HTTPS source URLs are permitted")
    if any(part in host for part in ("@", " ", "\\", "%")) or host.endswith((".local", ".internal")):
        raise ValueError("Unsafe URL")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if not ip.is_global:
            raise ValueError("Private network URL forbidden")
    return url

def curl_read(url: str, timeout: int = 16) -> tuple[int, str]:
    validate_public_url(url)
    # curl uses the OS certificate store on macOS; fail closed on HTTP/SSL errors.
    result = subprocess.run([
        "curl", "-L", "--proto", "=https", "--proto-redir", "=https",
        "--max-redirs", "3", "--connect-timeout", "6", "--max-time", str(timeout),
        "--silent", "--show-error", "-w", "\n__ANDY_HTTP__%{http_code}",
        "--max-filesize", "1200000", url
    ], capture_output=True, text=True, timeout=timeout + 3)
    marker = "\n__ANDY_HTTP__"
    if marker not in result.stdout:
        raise RuntimeError(f"Source fetch failed ({result.returncode}): {result.stderr.strip()[:160]}")
    payload, code = result.stdout.rsplit(marker, 1)
    return int(code), payload

def curl_secret_query(url: str, timeout: int = 18) -> tuple[int, str]:
    """Keep SerpApi key out of process arguments and saved reports."""
    validate_public_url(url)
    if '"' in url or "\n" in url:
        raise ValueError("Unsafe search URL")
    proc = subprocess.run(
        ["curl", "-L", "--proto", "=https", "--proto-redir", "=https",
         "--silent", "--show-error", "--max-time", str(timeout),
         "-w", "\n__ANDY_HTTP__%{http_code}", "--config", "-"],
        input='url = "' + url + '"\n', capture_output=True,
        text=True, timeout=timeout + 3)
    marker = "\n__ANDY_HTTP__"
    if marker not in proc.stdout:
        raise RuntimeError("Live search failed without a valid HTTP response")
    body, code = proc.stdout.rsplit(marker, 1)
    return int(code), body

def collect_curated(job: dict) -> dict:
    records = []
    for pos, url in enumerate(job.get("research_urls", []), start=1):
        doc = {"id": f"SRC-WEB-{pos:03}", "url": url, "collection_method": "curated_url_fetch",
               "retrieved_at": now(), "verification": "retrieval_only"}
        try:
            status, html = curl_read(url)
            doc["http_status"] = status
            if status != 200:
                raise RuntimeError(f"HTTP {status}")
            parser = PageExtractor()
            parser.feed(html)
            doc["title"] = parser.title.strip()
            doc["excerpt"] = " ".join(parser.text_parts)[:500]
            doc["status"] = "retrieved"
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as err:
            doc["status"] = "unavailable"
            doc["error"] = str(err)[:200]
        records.append(doc)
    return {"collection_mode": "curated_url_fetch_NOT_SERP", "queries_not_executed": job.get("queries", []),
            "retrieved_at": now(), "sources": records, "organic_rankings": None}

def collect_serpapi(job: dict) -> dict:
    key = os.environ.get("SERPAPI_API_KEY")
    if not key:
        raise RuntimeError("SERPAPI_API_KEY absent; cannot claim live Google SERP collection")
    output = []
    for query in job.get("queries", []):
        params = {"engine": "google", "q": query, "hl": "en", "gl": "us", "num": 10, "api_key": key}
        uri = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
        # API key is only used in the process invocation; never store the URL.
        status, body = curl_secret_query(uri, timeout=18)
        if status != 200:
            raise RuntimeError(f"SerpApi failed HTTP {status}")
        data = json.loads(body)
        if "error" in data:
            raise RuntimeError(f"SerpApi error: {str(data['error'])[:150]}")
        for item in data.get("organic_results", []):
            url = item.get("link", "")
            try:
                validate_public_url(url)
            except ValueError:
                continue
            output.append({"id": f"SRC-SERP-{len(output)+1:03}", "url": url,
                           "title": item.get("title"), "snippet": item.get("snippet"),
                           "position": item.get("position"), "query": query, "collection_method": "serpapi_live"})
    return {"collection_mode": "serpapi_live", "retrieved_at": now(),
            "queries_executed": job.get("queries", []), "sources": output}

def research(job: dict) -> dict:
    mode = job.get("research_mode", "curated")
    if mode == "curated":
        return collect_curated(job)
    if mode == "serpapi":
        return collect_serpapi(job)
    raise ValueError("Unknown research mode; use curated or serpapi")
