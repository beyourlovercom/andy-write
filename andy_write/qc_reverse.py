"""Deterministic QC blueprint analysis of public benchmark articles.

Public articles are read-only; only derived measures are committed.
The full competitor HTML stays in .runs and is NEVER used as prose
to generate a substitute article. No Codex, LLM, media or WordPress writes.
"""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from html import unescape
from urllib.parse import urlsplit
import re
from typing import Any
from .io import hashtext, now

QC_VERSION = "andy-write-qc-reverse-v1.2"
WORDS = re.compile(r"\b[\w]+(?:['’-][\w]+)*\b",re.UNICODE)
PERCENT = re.compile(r"\b\d+(?:\.\d+)?\s?%")
STAT = re.compile(r"\b(?:p\s*[=<>]\s*0\.\d+|(?:\d+\s?%))",re.I)
MATERIAL = re.compile(r"\b(?:IPX[4-9]|disinfect|steriliz|hypoallergenic|"
                      r"body[- ]safe|bacteri|infection|medical|antibacterial|"
                      r"boil|waterproof|submerg|silicone|heat|temperature|powder|lubric|oil)\b",re.I)
ABSOLUTE = re.compile(r"\b(?:always|never|guaranteed|safe for all|any toy|"
                      r"all toys|every toy|without risk|100% safe)\b",re.I)


class BodyInspector(HTMLParser):
    """Only content.rendered, not webpage headers/menus/sidebars."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags=Counter()
        self.headers=[]
        self.text=[]
        self.paragraphs=[]
        self.links=[]
        self.images=[]
        self._active=[]
        self._buffer=[]
        self._in_ignored=0
        self._level=0

    def handle_starttag(self,tag:str,attrs:list[tuple[str,str|None]])->None:
        attrs=dict(attrs)
        self.tags[tag]+=1
        if tag in ("script","style","svg","noscript","template"):
            self._in_ignored+=1
        if tag=="a":
            self.links.append({"href":attrs.get("href") or "",
                               "rel":attrs.get("rel") or ""})
        if tag=="img":
            self.images.append({"alt":attrs.get("alt") or "",
                                "loading":attrs.get("loading") or "",
                                "src_present":bool(attrs.get("src") or attrs.get("data-src"))})
        if tag in ("p","h1","h2","h3","h4","li","blockquote"):
            self._active.append([tag,[]])

    def handle_data(self,data:str)->None:
        if self._in_ignored or not data.strip():
            return
        self.text.append(data)
        for unit in self._active:
            unit[1].append(data)

    def handle_endtag(self,tag:str)->None:
        if tag in ("script","style","svg","noscript","template"):
            self._in_ignored=max(0,self._in_ignored-1)
        for i in range(len(self._active)-1,-1,-1):
            if self._active[i][0]==tag:
                type_,parts=self._active.pop(i)
                text=" ".join(" ".join(parts).split())
                if text:
                    if type_=="p": self.paragraphs.append(text)
                    if type_.startswith("h"): self.headers.append((type_,text))
                break


def classify_links(links:list[dict],site_host:str)->dict:
    domains=Counter()
    intra=0
    offsite=0
    commerce_internal=0
    for item in links:
        href=item.get("href") or ""
        if href.startswith(("#","mailto:","tel:","javascript:")):
            continue
        parts=urlsplit(href)
        if parts.scheme not in ("http","https"):
            continue
        host=(parts.hostname or "").lower()
        if not host:continue
        if host in (site_host,"www."+site_host) or host.removeprefix("www.")==site_host:
            intra+=1
            if re.search(r"/(?:product|shop|cart|checkout|collections)/",parts.path,re.I):
                commerce_internal+=1
        else:
            offsite+=1
            domains[host]+=1
    return {"internal_link_instances":intra,"external_link_instances":offsite,
            "unique_external_domains":len(domains),
            "external_domains":sorted(domains),
            "internal_commerce_link_instances":commerce_internal}

def score_paragraph_risks(paragraphs:list[str])->dict:
    flagged=[]
    for i,body in enumerate(paragraphs,1):
        reasons=[]
        if STAT.search(body):reasons.append("QUANTIFIED_CLAIM_REVIEW")
        if MATERIAL.search(body):reasons.append("MATERIAL_SAFETY_REVIEW")
        if ABSOLUTE.search(body):reasons.append("UNIVERSAL_CLAIM_REVIEW")
        if reasons:
            flagged.append({
                "paragraph_index":i,"reason_codes":reasons,
                "paragraph_sha256":hashtext(body),
                "percent_tokens":PERCENT.findall(body)[:6]
            })
    counts=Counter(code for entry in flagged for code in entry["reason_codes"])
    return {
        "flagged_paragraph_count":len(flagged),
        "reason_counts":dict(counts),
        "example_review_ids":[v["paragraph_index"] for v in flagged[:16]],
        "risk_receipts":flagged[:45],
        "warning":"Candidates from language patterns; not verified false claims"
    }

def html_qc_profile(html:str,*,url:str,date:str,modified:str,
                    article_id:int|str|None=None)->dict:
    if not url.startswith("https://"):
        raise ValueError("Public canonical HTTPS URL required")
    inspector=BodyInspector()
    inspector.feed(html)
    full=" ".join(" ".join(inspector.text).split())
    # Text inside HTML data is not scraped word-for-word into the committed
    # benchmark; only metrics and public section-heading metadata.
    if len(WORDS.findall(full)) < 300:
        raise ValueError("Article body seems too short for QC reverse engineering")
    host=urlsplit(url).hostname or ""
    lk=classify_links(inspector.links,host.removeprefix("www."))
    h2=[t for level,t in inspector.headers if level=="h2"]
    h3=[t for level,t in inspector.headers if level=="h3"]
    paragraphs=inspector.paragraphs
    words=len(WORDS.findall(full))
    word_lengths=[len(WORDS.findall(p)) for p in paragraphs]
    images=inspector.images
    toc=bool(re.search(r"table of contents|contents|on this page",full,re.I))
    faq=any(re.search(r"\bFAQ\b|frequently asked questions",heading,re.I)
            for heading in h2+h3)
    takeaway=any(re.search(r"key takeaways|summary|at a glance",title,re.I)
                 for title in h2+h3)
    risks=score_paragraph_risks(paragraphs)
    return {
        "contract":QC_VERSION,"retrieved_at":now(),
        "url":url,"source_post_id":article_id,
        "original_publication_date":date,
        "last_public_modified":modified,
        "original_2025_snapshot_verified":False,
        "analysis_scope":"current public revision of article first published in 2025",
        "derived_only":True,"source_content_sha256":hashtext(html),
        "structure":{
            "words_approx":words,"h2_count":len(h2),"h3_count":len(h3),
            "h4_count":sum(x[0]=="h4" for x in inspector.headers),
            "heading_h2_examples":h2[:10],
            "paragraph_count":len(paragraphs),
            "paragraph_word_median":sorted(word_lengths)[len(word_lengths)//2] if word_lengths else None,
            "paragraphs_over_140_words":sum(n>140 for n in word_lengths),
            "table_count":inspector.tags["table"],
            "unordered_list_count":inspector.tags["ul"],
            "ordered_list_count":inspector.tags["ol"],
            "list_items":inspector.tags["li"],
            "blockquote_count":inspector.tags["blockquote"],
            "images_count":len(images),
            "images_with_nonempty_alt":sum(bool(x["alt"].strip()) for x in images),
            "faq_heading_present":faq,"key_takeaways_heading_present":takeaway,
            "table_of_contents_text_present":toc,
        },
        "links":lk,"risk_review":risks,
        "interpretation_limits":[
            "Page first published in 2025 but edited later; original 2025 body not verified",
            "Word count and HTML tag counts are not quality or search-ranking scores",
            "Offsite links are not necessarily valid evidence for nearby claims",
            "A risk-language flag is not a factual error until checked by a reviewer",
            "Do not treat competitor article as Owner-authored input for Codex rewriting"
        ],
    }

def markdown_qc_profile(article:str,*,source_label:str)->dict:
    text=re.sub(r"(?m)^\s*<!--.*?-->\s*$","",article)
    headings=[(len(m.group(1)),m.group(2).strip())
              for m in re.finditer(r"(?m)^(#{1,4})\s+(.+)$",text)]
    paras=[p for p in re.split(r"\n\s*\n",text)
           if p.strip() and not p.strip().startswith(("#","|","-","1. ","[image:"))]
    links=[{"href":u} for u in re.findall(r"\]\((https?://[^)]+)\)",text)]
    # Count only actual markdown tables with a divider row.
    tables=len(re.findall(r"(?m)^\|[\s:\-|]+\|\s*$",text))
    imgs=re.findall(r"!\[([^\]]*)\]\(([^)]+)\)",text)
    host=urlsplit(source_label).hostname or "pairdoll.com"
    words=len(WORDS.findall(re.sub(r"\]\((https?://[^)]+)\)","]",text)))
    result={
        "contract":QC_VERSION,"source_label":source_label,
        "source_kind":"local_existing_owner_artifact",
        "structure":{
            "words_approx":words,
            "h2_count":sum(x[0]==2 for x in headings),
            "h3_count":sum(x[0]==3 for x in headings),
            "h4_count":sum(x[0]==4 for x in headings),
            "heading_h2_examples":[h[1] for h in headings if h[0]==2][:10],
            "paragraph_count":len(paras),
            "table_count":tables,
            "unordered_list_count":len(re.findall(r"(?m)^[-*]\s",text)),
            "ordered_list_count":len(re.findall(r"(?m)^\d+[.)]\s",text)),
            "images_count":len(imgs),
            "images_with_nonempty_alt":sum(bool(alt.strip()) for alt,_ in imgs),
            "faq_heading_present":any("faq" in h[1].lower() for h in headings),
            "key_takeaways_heading_present":any("takeaways" in h[1].lower() for h in headings)
        },
        "links":classify_links(links,host),
        "risk_review":score_paragraph_risks(paras),
    }
    return result

def compare_structure(benchmark:dict,ours:dict)->dict:
    b=benchmark["structure"]; a=ours["structure"]
    same=["words_approx","h2_count","h3_count","table_count",
          "images_count","images_with_nonempty_alt"]
    return {
        "comparison_type":"STRUCTURAL_ONLY_NOT_QUALITY_OR_RANKING",
        "benchmark_post_id":benchmark.get("source_post_id"),
        "rows":[{"metric":key,"benchmark":b.get(key),"andy_write":a.get(key),
                 "delta":a[key]-b[key]}
                for key in same if isinstance(a.get(key),int) and isinstance(b.get(key),int)],
        "important_context":"Different topics and intent, so absolute structural counts do not establish superiority",
        "release_gate":"Factual/human source-fidelity review still required"
    }

def skill_gap_actions(benchmark:dict,ours:dict)->list[dict]:
    """Reusable Skill tickets: Never prescribe copying benchmark counts."""
    bench=benchmark["structure"]
    my=ours["structure"]
    def action(code:str,skill:str,why:str,gate:str)->dict:
        return {"id":code,"skill":skill,"observed_gap":why,
                "acceptance_gate":gate,"status":"PROPOSED_FOR_SKILL_REGRESSION"}
    actions=[
        action("QC_CLAIM_TO_SOURCE_TRACE","andy-write-quality",
               "Benchmark has "+str(benchmark["links"]["external_link_instances"])
               +" outbound links and "+str(bench["words_approx"])+
               " words; link volume does not establish evidence validity.",
               "For product safety claims, require verified source relevance or an explicit NEEDS_REVIEW result."),
        action("QC_PRODUCT_SPEC_SCOPE","andy-write-source",
               "Benchmark has "+str(benchmark["risk_review"]["flagged_paragraph_count"])+
               " pattern-flagged paragraphs needing actual editorial review.",
               "Do not universalize model-specific waterproof, material, cleaning, temperature or disinfection requirements."),
        action("QC_CONDITIONAL_STRUCTURE","andy-write-outline",
               "Benchmark has nested H3/tables/FAQ; draft has fewer structured elements with a much shorter word budget.",
               "Only add H3, decision tables and FAQ if intent and source evidence justify them; no numeric quota."),
        action("QC_LINK_RELEVANCE","andy-write-quality",
               "Benchmark has links to multiple external site categories, not all of which necessarily provide supporting evidence.",
               "Audit anchor-to-claim relevance, avoid competitor e-commerce outbound links, and disclose unverified citations."),
        action("QC_EDITOR_REPETITION","andy-write-editor",
               "Numerous lists, callouts and tables can aid scanning or produce repetitive filler.",
               "Compare actionable information density and redundant passages using real examples, not length."),
    ]
    if my["images_count"] == 0:
        actions.append(action(
            "QC_MEDIA_POLICY","andy-write-media",
            "Existing draft lacks actual embedded image files; benchmark includes images with Alt text.",
            "Review existing or Owner-supplied media only. Image/video generation remains prohibited."))
    return actions
