"""Private, stratified, human-labeling packets for source-to-rewrite QC.

A packet is a REVIEW WORKSHEET, not a model judgement. Never export raw
source/target excerpts to GitHub, Notion, or a production website.
"""
from __future__ import annotations
import pathlib
from .io import ROOT, hashtext
from .fidelity import PARAGRAPH, inspect_fidelity
from .qc_reverse import MATERIAL, ABSOLUTE

GOLDSET_VERSION="andy-write-human-qc-goldset-v1.2"
LABEL_OPTIONS=[
    "SEMANTICALLY_RETAINED",
    "RETAINED_WITH_QUALIFICATIONS",
    "INTENTIONALLY_OMITTED_UNSAFE_OR_INAPPLICABLE",
    "LOST_USEFUL_INFORMATION",
    "UNSUPPORTED_ADDITION",
    "NOT_COMPARABLE",
    "INDETERMINATE",
]

def build_goldset(source:str, draft:str, size:int=12)->dict:
    if not 4 <= size <= 40:
        raise ValueError("Manual label sample size must be 4-40")
    report=inspect_fidelity(source,draft)
    original=PARAGRAPH.split(source)
    rewritten=PARAGRAPH.split(draft)
    units=sorted(report["units"]+report["short_or_heading_units"],
                 key=lambda x:x["source_paragraph_number"])
    if len(units)<size:
        raise ValueError("Insufficient real source paragraphs for sample")
    # Distribute throughout original, then balance safety-relevant passages.
    # Never assign semantic labels automatically.
    indexed={x["source_id"]:x for x in units}
    picked=[]
    for i in range(size):
        index=round((i+.5)*(len(units)-1)/size)
        candidate=units[index]
        if candidate["source_id"] not in picked:
            picked.append(candidate["source_id"])
    concerns=[x for x in units if (
        MATERIAL.search(original[x["source_paragraph_number"]-1])
        or ABSOLUTE.search(original[x["source_paragraph_number"]-1]))]
    if concerns and len(picked)>=4:
        # Retain most early-to-late coverage while reserving a few seats for
        # material-specific questions. Replacements are deterministic.
        for n,item in enumerate(concerns[:min(3,len(concerns))]):
            if item["source_id"] not in picked:
                # Preserve first and LAST position for real chronological spread.
                slot = len(picked)-2-n
                if slot > 0:
                    picked[slot] = item["source_id"]
    # Deduplicate after potential substitutions and fill from remaining units.
    picked=list(dict.fromkeys(picked))
    for item in units:
        if len(picked)>=size: break
        if item["source_id"] not in picked:
            picked.append(item["source_id"])
    picked=sorted(picked[:size],
                  key=lambda sid:indexed[sid]["source_paragraph_number"])
    sample=[]
    for sid in picked:
        item=indexed[sid]
        idx=item["source_paragraph_number"]-1
        loc=item.get("target_paragraphs")
        target=(rewritten[loc[0]-1:loc[1]]
                if loc and loc[0] <= len(rewritten) else [])
        sample.append({
            "source_id":sid,"source_sha256":item["source_sha256"],
            "source_paragraph":item["source_paragraph_number"],
            "source_text_for_private_review":original[idx].strip(),
            "target_window_hint":list(loc) if loc else None,
            "target_text_for_private_review":"\n\n".join(target)[:750],
            "machine_state":item["state"],
            "material_claim_review_candidate":bool(
                MATERIAL.search(original[idx]) or ABSOLUTE.search(original[idx])),
            "proposed_label":None,"reviewer":None,"reviewer_rationale":None,
            "owner_confirmation":"PENDING",
        })
    return {
        "contract":GOLDSET_VERSION,"source_sha256":hashtext(source),
        "draft_sha256":hashtext(draft),
        "sample_count":len(sample),
        "total_source_paragraphs":len(original),
        "sampled_source_paragraphs":[x["source_paragraph"] for x in sample],
        "label_options":LABEL_OPTIONS,
        "labels_are_human_provided":False,
        "gold_standard_semantic_score":None,
        "owner_approval":"PENDING",
        "sampling_method":"deterministic spread + safety-relevant source paragraph priority",
        "privacy":"private .runs only, contains original excerpts",
        "cases":sample,
    }

def write_goldset(source:str,draft:str,output:pathlib.Path,size:int=12)->dict:
    from .io import write_json
    root=(ROOT/".runs").resolve()
    target=output.resolve()
    if not target.is_relative_to(root):
        raise ValueError("Goldset packet contains original prose; use private .runs only")
    pack=build_goldset(source,draft,size)
    target.parent.mkdir(parents=True,exist_ok=True)
    write_json(target,pack)
    return {k:v for k,v in pack.items() if k!="cases"}
