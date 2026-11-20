"""Source-grounded hierarchical outline, no model or media generation."""
from __future__ import annotations
import re
from .io import hashtext
from .source import UNSAFE_ADVICE

H2 = re.compile(r"(?m)^## (?!#)(.+)\s*$")
H3 = re.compile(r"(?m)^### (?!#)(.+)\s*$")
# Source-only hazard triggers; these are REVIEW flags, not assertions that
# every described action is unsafe. Verify product-specific instructions.
SOURCE_CARE_REVIEW = re.compile(
    r"\b(?:powder|heat|hair dryers?|warm up|lubricat|oil|solvent|"
    r"silicone.based|wash|clean|soap|disinfect|boil|glue|dry|"
    r"bacteri|infection|melt|waterproof)\b",re.I)
SKIP = re.compile(r"^(?:conclusion|final thoughts?|references?|resources?)$",re.I)

def to_question(heading:str)->str:
    """Conservative editorial question from a real source title (no new claim)."""
    heading = re.sub(r"\s+"," ",heading.strip()).rstrip(".")
    lower=heading.lower()
    if heading.endswith("?"):
        return heading[0:1].upper()+heading[1:]
    if lower in ("what not to do","things to avoid","what to avoid"):
        return "What should you avoid?"
    if lower.startswith("how to "):
        obj=re.sub(r"\s+101$","",heading[7:],flags=re.I).strip().lower()
        return "How do you "+obj+"?"
    match = re.match(r"best positions (?:to )?try with (.+)",heading,re.I)
    if match:
        return "Which positions can you consider with " + match.group(1).lower() + "?"
    match = re.match(r"tips for .+ with (.+)",heading,re.I)
    if match:
        return "What practical tips apply when using " + match.group(1).lower() + "?"
    if lower.startswith("best positions"):
        return "Which positions may be suitable for this product?"
    if lower.startswith("tips for "):
        return "What practical tips should a first-time owner consider?"
    if lower.startswith("what "):
        return heading+"?"
    return "What should you know about "+heading[0:1].lower()+heading[1:]+ "?"

def source_hierarchy_plan(job:dict,catalog:dict,source:str)->list[dict]:
    if catalog.get("source_sha256") != hashtext(source):
        raise PermissionError("Source catalog hash does not match original article")
    matches=list(H2.finditer(source))
    if len(matches)<2:
        raise ValueError("Source hierarchy mode requires 2+ authentic H2 headings")
    plan=[]
    for i,m in enumerate(matches):
        title=m.group(1).strip()
        if SKIP.fullmatch(title):
            continue
        content=source[m.end():matches[i+1].start() if i+1<len(matches) else len(source)]
        descendants=[x.group(1).strip() for x in H3.finditer(content)]
        ids=[r["id"] for r in catalog.get("segments",[])
             if (len(r.get("excerpt","").strip())>=35
                 and r["excerpt"].strip()[:35] in content)][:12]
        if not ids:
            # Empty references are explicit, not silently invented.
            evidence_note="UNMAPPED_SOURCE_SEGMENTS"
        else:
            evidence_note="SOURCE_SEGMENTS_ATTACHED"
        caution=(bool(SOURCE_CARE_REVIEW.search(content))
                 or any(risk in content.lower() for risk in UNSAFE_ADVICE))
        plan.append({
            "id":f"SEC-{len(plan)+1:02d}",
            "heading":to_question(title),
            "source_heading":title,
            "topic":"source_derived",
            "brief":"Rework the source section using supported details; do not invent claims.",
            "source_heading_evidence":"AUTHENTIC_H2",
            "subheadings":descendants,
            "reference_segment_ids":ids,
            "source_segment_status":evidence_note,
            "manufacturer_material_review":caution,
            "h3_count":len(descendants),
        })
    if not plan:
        raise ValueError("No substantive original H2 headings")
    return plan
