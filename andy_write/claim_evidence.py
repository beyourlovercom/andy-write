"""V1.2 important-claim to actually retrieved passage tracing (offline).

A topic/keyword match NEVER equals an entailed claim, credible study, true
manufacturer specification or editorial factual approval.
Owner original = writing provenance, not independent fact verification.
"""
from __future__ import annotations
from collections import Counter
import re
from urllib.parse import urlsplit

from .fidelity import content_terms, canonical, NUMERIC_WITH_UNIT, PARAGRAPH
from .io import hashtext, now

CONTRACT="andy-write-claim-evidence-v1.2.1"
SENTENCE=re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"“])|(?<=;)\s+")
LINK=re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
MARKUP=re.compile(r"(?m)^\s*(?:#{1,6}\s+|[-*]\s+|\d+[.)]\s+)")
MATERIAL=re.compile(
    r"\b(?:waterproof|water.resistant|IPX\d|submerg|material|silicone|"
    r"tpe|latex|lubricat|clean(?:ing)?|disinfect|saniti[sz]|"
    r"sterili[sz]|bacteria|infection|hypoallergenic|"
    r"allerg|boil|temperature|heat|powder|oil|safe|"
    r"toxic|medical|health|injur|damage|manufacturer)\b",re.I)
ABSOLUTE=re.compile(
    r"\b(?:all|always|never|guarantee(?:s|d)?|every|100%|"
    r"risk.free|completely safe|will not)\b",re.I)
DIRECTIVE=re.compile(
    r"\b(?:must|should|need to|avoid|do not|don't|check|verify|"
    r"follow|choose|recommended|works? with|compatible|use)\b",re.I)
NEGATION=re.compile(r"\b(?:no|not|never|cannot|can't|doesn't|don't|without|avoid)\b",re.I)
QUOTE_TOO_LONG=550

def sentences(draft:str)->list[dict]:
    """Source-positioned importance inventory. No claims are discarded silently."""
    result=[]
    paragraph_index=0
    heading=None
    for chunk in PARAGRAPH.split(draft):
        paragraph_index+=1
        if not chunk.strip():
            continue
        if chunk.lstrip().startswith("#"):
            heading=re.sub(r"^#{1,6}\s*","",chunk.strip()).strip()
            continue
        lines=[line.strip() for line in chunk.splitlines() if line.strip()]
        for line in lines:
            plain=MARKUP.sub("",line).strip()
            if not plain or plain.startswith("|"):
                continue
            for phrase in SENTENCE.split(plain):
                if len(content_terms(phrase))<5:
                    continue
                important=(bool(MATERIAL.search(phrase))
                           or bool(NUMERIC_WITH_UNIT.search(phrase))
                           or bool(ABSOLUTE.search(phrase))
                           or bool(DIRECTIVE.search(phrase)))
                if not important:
                    continue
                reasons=[]
                if MATERIAL.search(phrase): reasons.append("PRODUCT_OR_SAFETY_SPEC")
                if NUMERIC_WITH_UNIT.search(phrase):reasons.append("NUMERIC")
                if ABSOLUTE.search(phrase):reasons.append("UNIVERSAL")
                if DIRECTIVE.search(phrase):reasons.append("ACTION_OR_INSTRUCTION")
                result.append({
                    "id":f"CLM-{len(result)+1:04d}",
                    "claim":phrase.strip(),
                    "claim_sha256":hashtext(phrase.strip()),
                    "paragraph_index":paragraph_index,
                    "source_heading":heading,
                    "importance":"HIGH" if ("PRODUCT_OR_SAFETY_SPEC" in reasons or
                                             "NUMERIC" in reasons or
                                             "UNIVERSAL" in reasons) else "MEDIUM",
                    "reason_codes":reasons,
                    "inline_citation_urls":[x[1] for x in LINK.findall(phrase)]
                })
    return result

def validate_sources(sources:list[dict])->list[dict]:
    if not isinstance(sources,list):
        raise ValueError("Evidence bundle must be a list")
    seen=set()
    validated=[]
    for source in sources:
        if not isinstance(source,dict):
            raise ValueError("Evidence record must be an object")
        url=source.get("url")
        if not isinstance(url,str) or urlsplit(url).scheme!="https" or not urlsplit(url).hostname:
            raise ValueError("Evidence must link an actual HTTPS source URL")
        if url in seen:
            raise ValueError("Duplicate external evidence source")
        seen.add(url)
        if source.get("source_kind")!="public_web_retrieval" or \
           source.get("retrieval_status")!="retrieved":
            raise ValueError("Metadata-only/unretrieved source cannot be presented as evidence")
        method=source.get("retrieval_channel")
        if method not in ("direct_read_only_html", "web_read_only_quote"):
            raise ValueError("Evidence retrieval channel provenance required")
        date=source.get("retrieved_at")
        pieces=source.get("paragraphs")
        if not isinstance(date,str) or len(date)<10 or \
           not isinstance(pieces,list) or not pieces:
            raise ValueError("Source must have a retrieval time and actual extracted text")
        if len(pieces)>250:
            raise ValueError("Evidence bundle has too many paragraphs")
        if any(not isinstance(p,str) or len(p)>3000 for p in pieces):
            raise ValueError("Untrusted/oversize evidence paragraph")
        body="\n\n".join(pieces)
        if source.get("body_sha256")!=hashtext(body):
            raise ValueError("Evidence content SHA-256 mismatch")
        validated.append(source)
    return validated

def _support_score(claim:str, passage:str)->tuple[float,int]:
    # Denominator refers to distinct, non-stop claim terms. A small score
    # means the citation is not even topically aligned. A high score only
    # makes the passage worth manual entailment review.
    a=content_terms(claim)
    b=content_terms(passage)
    count=len(a&b)
    return (count/len(a) if a else 0.,count)

def _numeric_conflict(a:str,b:str)->bool:
    nums_a={re.sub(r"\s+","",x.casefold()) for x in NUMERIC_WITH_UNIT.findall(a)}
    nums_b={re.sub(r"\s+","",x.casefold()) for x in NUMERIC_WITH_UNIT.findall(b)}
    return bool(nums_a and nums_b and nums_a.isdisjoint(nums_b))

def find_candidates(claim:str,sources:list[dict],limit:int=3)->list[dict]:
    candidates=[]
    for source in sources:
        for i,passage in enumerate(source["paragraphs"],1):
            score,overlap=_support_score(claim,passage)
            if overlap<3 or score<.28:
                continue
            flip=bool(NEGATION.search(claim))!=bool(NEGATION.search(passage))
            numerical=_numeric_conflict(claim,passage)
            same=canonical(claim) in canonical(passage)
            state=("POTENTIAL_NEGATION_OR_NUMBER_CONFLICT" if flip or numerical else
                   "EXACT_WORDING_NEEDS_FACT_REVIEW" if same else
                   "TOPICAL_CANDIDATE_NEEDS_ENTAILMENT")
            candidates.append({
                "source_url":source["url"],"retrieved_at":source["retrieved_at"],
                "source_body_sha256":source["body_sha256"],
                "source_paragraph_number":i,
                "source_passage_sha256":hashtext(passage),
                "source_excerpt":passage[:QUOTE_TOO_LONG],
                "term_overlap_count":overlap,
                "claim_term_recall":round(score,4),
                "risk_state":state,
                "semantic_support_verified":False,
            })
    return sorted(candidates,key=lambda x:(
        x["risk_state"]=="POTENTIAL_NEGATION_OR_NUMBER_CONFLICT",
        -x["claim_term_recall"],-x["term_overlap_count"]))[:limit]

def trace_claims(draft:str,owner_original:str,
                 external_sources:list[dict]|None=None)->dict:
    if not owner_original or len("".join(owner_original.split()))<900:
        raise ValueError("Actual substantive Owner original required")
    if not draft.strip():
        raise ValueError("Actual rewritten article required")
    sources=validate_sources(external_sources or [])
    owner_paragraphs=[p.strip() for p in PARAGRAPH.split(owner_original)
                      if content_terms(p)]
    all_claims=sentences(draft)
    lines=[]
    for item in all_claims:
        owner_hits=[]
        for idx,phrase in enumerate(owner_paragraphs,1):
            score,common=_support_score(item["claim"],phrase)
            if common>=3 and score>=.35:
                owner_hits.append((score,idx,hashtext(phrase)))
        owner_hits.sort(reverse=True)
        external=find_candidates(item["claim"],sources)
        cited=set(item["inline_citation_urls"])
        linked=[x for x in external if x["source_url"] in cited]
        weak_inline=bool(cited) and not linked
        if linked:
            status="CITED_PASSAGE_ENTAILMENT_REVIEW"
        elif cited:
            status="CITATION_UNRELATED_OR_UNAVAILABLE"
        elif external:
            status="EXTERNAL_PASSAGE_CANDIDATE_UNCITED"
        elif owner_hits:
            status="OWNER_REFERENCE_ONLY_UNVERIFIED"
        else:
            status="NO_RELEVANT_EVIDENCE_FOUND"
        lines.append({
            **item,
            "status":status,
            "owner_original_only":bool(owner_hits) and not external,
            "owner_source_candidate":[{
                "paragraph_number":idx,"sha256":h,"term_recall":round(score,4)}
                for score,idx,h in owner_hits[:2]],
            "external_evidence_candidates":external,
            "citation_requires_relevance_review":weak_inline,
            "human_entailment_verification":"PENDING",
            "authoritative_manufacturer_document_present":False,
        })
    counts=Counter(x["status"] for x in lines)
    risk=Counter(x["importance"] for x in lines)
    return {
        "contract":CONTRACT,
        "draft_sha256":hashtext(draft),
        "owner_original_sha256":hashtext(owner_original),
        "source_count":len(sources),
        "retrieved_at":now(),
        "status":"HUMAN_FACT_EVIDENCE_REVIEW_REQUIRED",
        "publish_ready":False,
        "source_original_not_independent_proof":True,
        "semantic_support_verified":False,
        "summary":{
            "important_claims_total":len(lines),
            "high_importance":risk["HIGH"],
            "medium_importance":risk["MEDIUM"],
            "claims_with_cited_passage_candidate":counts["CITED_PASSAGE_ENTAILMENT_REVIEW"],
            "claims_with_uncited_external_candidate":counts["EXTERNAL_PASSAGE_CANDIDATE_UNCITED"],
            "claims_with_unrelated_or_unavailable_citation":counts["CITATION_UNRELATED_OR_UNAVAILABLE"],
            "owner_original_only_unverified":counts["OWNER_REFERENCE_ONLY_UNVERIFIED"],
            "no_relevant_external_or_owner_evidence":counts["NO_RELEVANT_EVIDENCE_FOUND"],
            "human_entailment_review_pending":len(lines),
            "confirmed_supported_claims":0,
        },
        "claims":lines,
        "limitations":[
           "A topical or exact quote is not entailment; fact verification requires a qualified human reviewer",
           "Owner-supplied original is editorial provenance and may itself be factually wrong",
           "Manufacturer/material instructions require actual product-specific authoritative manuals",
           "A fetched web source may be stale, untrustworthy or about a different product",
           "This is an offline deterministic index; no Codex, model or media calls",
        ]
    }

CLAIM_DECISIONS = {
    "SUPPORTED_BY_QUOTED_SOURCE",
    "SOURCE_DOES_NOT_SUPPORT",
    "SOURCE_CONTRADICTS_CLAIM",
    "SOURCE_UNAVAILABLE",
    "MANUFACTURER_SPEC_REQUIRED",
}
CLAIM_REVIEW_DECLARATION = (
    "I personally checked the exact claim against the cited source passage"
)

def apply_human_claim_reviews(report:dict,sources:list[dict],
                              reviews:list[dict])->dict:
    """Attach genuine reviewer decisions. No implicit human attestation or publish PASS.

    A verified passage's existence/provenance can be checked mechanically;
    whether it ENTAILS an important fact remains a human editorial judgment.
    """
    if report.get("contract")!=CONTRACT:
        raise ValueError("Unsupported claim-audit report")
    verified=validate_sources(sources)
    lookup={x["url"]:x for x in verified}
    claims={x["id"]:x for x in report.get("claims",[])}
    if not isinstance(reviews,list):
        raise ValueError("Human claim-review notes must be an array")
    if len(reviews)>len(claims):
        raise ValueError("More review notes than actual claims")
    seen=set()
    output=[]
    for note in reviews:
        if not isinstance(note,dict):
            raise ValueError("Invalid human claim review record")
        cid=note.get("claim_id")
        if cid not in claims or cid in seen:
            raise ValueError("Unknown or duplicate claim review ID")
        seen.add(cid)
        row=claims[cid]
        if note.get("claim_sha256")!=row["claim_sha256"]:
            raise ValueError("Claim text SHA-256 changed since reviewer inspected")
        if note.get("decision") not in CLAIM_DECISIONS:
            raise ValueError("Unrecognized claim-verification decision")
        reviewer=note.get("reviewer","")
        reason=note.get("reason","")
        if (not isinstance(reviewer,str) or len(reviewer.strip())<2
            or not isinstance(reason,str) or len(reason.strip())<24
            or note.get("reviewer_declaration")!=CLAIM_REVIEW_DECLARATION):
            raise ValueError("Actual human review declaration and rationale required")
        if note["decision"]=="SUPPORTED_BY_QUOTED_SOURCE":
            src=lookup.get(note.get("source_url"))
            if src is None:
                raise ValueError("A supported fact needs an actual fetched source URL")
            raw_quote=note.get("source_quote")
            if not isinstance(raw_quote,str) or len(raw_quote.strip())<20:
                raise ValueError("Evidence needs a substantial literal source quote")
            # The source quote must match a real paragraph in the cached document,
            # not a model-supplied fabricated passage or unrelated domain.
            paragraphs=src["paragraphs"]
            if not any(raw_quote in paragraph for paragraph in paragraphs):
                raise ValueError("Human source quote was not present in actual fetched text")
            if (("PRODUCT_OR_SAFETY_SPEC" in row["reason_codes"])
                and note.get("manufacturer_specific_confirmation") is not True):
                # Human must check real model-specific requirements separately:
                # a general government reference cannot establish toy compatibility.
                raise ValueError("Product/material claim requires model-specific confirmation")
        output.append({
            "claim_id":cid,"claim_sha256":row["claim_sha256"],
            "decision":note["decision"],
            "reviewer_record_sha256":hashtext(
                str(sorted(note.items()))),
        })
    counts=Counter(x["decision"] for x in output)
    return {
        "contract":"andy-write-human-claim-review-v1.2.1",
        "draft_sha256":report["draft_sha256"],
        "reviewed_claim_count":len(output),
        "important_claim_count":len(claims),
        "pending_claim_count":len(claims)-len(output),
        "decision_counts":dict(counts),
        "owner_release_approval":"PENDING",
        "automatic_publish_ready":False,
        "human_review_notes_hashed":output,
        "status":"OWNER_FACT_REVIEW_PENDING",
    }

def claim_review_sheet(report:dict)->str:
    """Private human-facing full claim list; kept Git-ignored under .runs."""
    if report.get("contract")!=CONTRACT:
        raise ValueError("Unsupported report")
    lines=[
        "# Andy Write — Important Claims vs Actual Source Passages",
        "",
        "All entries require HUMAN semantic/factual review; linked sources do not",
        "automatically prove a claim. Owner original = editorial reference ONLY.",
        "If a product/material specification is involved, obtain an actual",
        "manufacturer/model reference; do not substitute general government links.",
        "",
        "| ID | Priority | Proposed factual statement | Best external excerpt location | Status |",
        "|---|---|---|---|---|",
    ]
    for item in sorted(report.get("claims",[]),
                       key=lambda x:(x["importance"]!="HIGH",x["id"])):
        text=item["claim"].replace("|","/").replace("\n"," ").strip()[:175]
        loc=item["external_evidence_candidates"]
        link=(loc[0]["source_url"]+" (paragraph "+
              str(loc[0]["source_paragraph_number"])+")") if loc else "NONE"
        lines.append("| "+" | ".join([
            item["id"],item["importance"],text,
            link,item["status"]])+" |")
    lines.extend([
        "",
        "## Verification steps",
        "",
        "1. Read EACH full factual claim and the cited institution/manufacturer",
        "   paragraph in context; do not infer support from title/HTTP 200.",
        "2. Mark actual quote, retrieved URL, claim ID/hash and review reason.",
        "3. Reject unrelated claims, negation reversals, unsourced quantities",
        "   and general claims presented as model-specific specifications.",
        "4. Re-run qc-claims --notes after genuine human annotations.",
        "5. All claims and the final article remain publish-blocked until",
        "   a separate Owner-controlled review and release approval.",
        "",
        "This worksheet contains private draft text; never commit it.",
    ])
    return "\n".join(lines)+"\n"
