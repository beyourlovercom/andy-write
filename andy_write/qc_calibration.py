"""V1.2 human-goldset calibration. NO automatic human labels or semantic PASS.

The 12 real Torso samples remain unchanged until a human reviewer supplies
independent decisions. A model-assisted suggestion cannot be used as truth.
This routine validates immutable source/draft hashes and the reviewer record.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json

from .fidelity import inspect_fidelity, PARAGRAPH
from .io import hashtext
from .qc_goldset import GOLDSET_VERSION, LABEL_OPTIONS

CONTRACT = "andy-write-human-calibration-v1.2.1"
POSITIVE = {"SEMANTICALLY_RETAINED", "RETAINED_WITH_QUALIFICATIONS"}
NEGATIVE = {"LOST_USEFUL_INFORMATION",
            "INTENTIONALLY_OMITTED_UNSAFE_OR_INAPPLICABLE"}
EXCLUDED = {"UNSUPPORTED_ADDITION", "NOT_COMPARABLE", "INDETERMINATE"}
# This is the human's declaration, not proof of identity.
REVIEW_DECLARATION = "I personally compared the complete original and rewritten passage"
THRESHOLD_OPTIONS = [(r,a) for r in (0.40,0.50,0.58,0.65,0.72)
                     for a in (0.30,0.40,0.50,0.60)]

def validate_packet(packet:dict, source:str, draft:str)->list[dict]:
    if packet.get("contract") != GOLDSET_VERSION:
        raise ValueError("Unknown or obsolete 12-item goldset version")
    if packet.get("source_sha256")!=hashtext(source) or \
       packet.get("draft_sha256")!=hashtext(draft):
        raise ValueError("Source or draft SHA-256 changed; previous labels are stale")
    cases=packet.get("cases")
    if not isinstance(cases,list) or len(cases)!=12 or packet.get("sample_count")!=12:
        raise ValueError("V1.2 calibration requires exactly the frozen 12 source cases")
    parts=PARAGRAPH.split(source)
    if not isinstance(packet.get("sampled_source_paragraphs"),list) or \
       len(packet["sampled_source_paragraphs"])!=12:
        raise ValueError("Goldset paragraph positions missing")
    ids=set()
    for row in cases:
        idx=row.get("source_paragraph")
        if not isinstance(idx,int) or not 1<=idx<=len(parts):
            raise ValueError("Unknown source paragraph number")
        sid="SRC-P"+str(idx).zfill(4)
        if row.get("source_id")!=sid or sid in ids:
            raise ValueError("Duplicate or tampered source ID")
        if row.get("source_sha256")!=hashtext(parts[idx-1]):
            raise ValueError("Source paragraph content/hash mismatch")
        if row.get("source_text_for_private_review","").strip()!=parts[idx-1].strip():
            raise ValueError("Original passage changed since sampling")
        ids.add(sid)
    if [x["source_paragraph"] for x in cases]!=packet["sampled_source_paragraphs"]:
        raise ValueError("Goldset selection was altered")
    return cases

def _check_human_note(note:dict, case:dict, draft:str)->dict:
    label=note.get("label")
    if label not in LABEL_OPTIONS:
        raise ValueError("Unknown semantic label")
    if note.get("source_id")!=case["source_id"] or \
       note.get("source_sha256")!=case["source_sha256"]:
        raise ValueError("Stale human source evidence")
    name=note.get("reviewer")
    if not isinstance(name,str) or len(name.strip())<2:
        raise ValueError("Human reviewer name required")
    if any(x in name.casefold() for x in ("chatgpt","codex","ai-automatic","unreviewed")):
        raise ValueError("Model-generated labels cannot impersonate a reviewer")
    if note.get("reviewer_declaration")!=REVIEW_DECLARATION:
        raise ValueError("Independent human passage-comparison declaration required")
    rationale=note.get("reason")
    if not isinstance(rationale,str) or len(rationale.strip())<24:
        raise ValueError("Substantive human rationale required")
    target=note.get("target_quote","")
    if label in POSITIVE:
        if not isinstance(target,str) or len(target.strip())<20 or \
           target not in draft:
            raise ValueError("Retained meaning must cite a real draft passage")
    # Negative labels may cite the relevant passage; absence can be meaningful.
    elif target and (not isinstance(target,str) or target not in draft):
        raise ValueError("Negative note quotes an invented passage")
    return {"source_id":case["source_id"],"label":label,
            "reviewer_record_sha256":hashtext(json.dumps(note,sort_keys=True)),
            "reviewer":name.strip()[:120]}

def machine_positive(row:dict, *, recall:float, anchors:float)->bool:
    if row["state"]=="EXACT_TEXT_PRESENT":
        return True
    # Source note/headings may be faithfully paraphrased, but the matcher has
    # no calibrated linguistic score for those: don't manufacture one.
    if row["state"]=="SHORT_OR_HEADING_REVIEW":
        return False
    return (row.get("lexical_recall",0)>=recall
            and row.get("distinctive_anchor_recall",0)>=anchors
            and row.get("distinctive_anchor_count",0)>=2)

def _confusion(rows:list[tuple[dict,bool]],recall:float,anchors:float)->dict:
    tp=fp=fn=tn=0
    for row,actual in rows:
        predicted=machine_positive(row,recall=recall,anchors=anchors)
        if predicted and actual:tp+=1
        elif predicted:fp+=1
        elif actual:fn+=1
        else:tn+=1
    precision=tp/(tp+fp) if tp+fp else None
    sensitivity=tp/(tp+fn) if tp+fn else None
    f1=(2*precision*sensitivity/(precision+sensitivity)
        if precision is not None and sensitivity is not None
        and precision+sensitivity else None)
    return {"tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "precision":round(precision,4) if precision is not None else None,
            "recall":round(sensitivity,4) if sensitivity is not None else None,
            "f1":round(f1,4) if f1 is not None else None}

def calibrate(packet:dict, source:str, draft:str,
              annotations:list[dict]|None=None)->dict:
    cases=validate_packet(packet,source,draft)
    current=inspect_fidelity(source,draft)
    byid={x["source_id"]:x for x in
          current["units"]+current["short_or_heading_units"]}
    result={
        "contract":CONTRACT,"source_sha256":hashtext(source),
        "draft_sha256":hashtext(draft),
        "sample_ids":[x["source_id"] for x in cases],
        "sample_count":12,"human_labels_present":0,
        "approved_human_label_count":0,
        "gold_standard_semantic_accuracy":None,
        "calibrated_threshold":None,
        "baseline_threshold":{"lexical_recall":0.58,"distinctive_anchor_recall":0.50},
        "owner_approval":"PENDING",
        "auto_apply_calibration":False,
        "sample_machine_state_counts":dict(Counter(x.get("machine_state","UNKNOWN")
                                                    for x in cases)),
        "baseline_machine_positive_count":sum(
            x.get("machine_state") in ("EXACT_TEXT_PRESENT","LEXICAL_CANDIDATE")
            for x in cases),
        "status":"AWAITING_HUMAN_LABELS",
        "limitations":[
           "AI preliminary suggestions are not human labels",
           "12 labels are a small exploratory calibration, not independent validation",
           "Source headings/shorts have no valid automatic semantic score",
           "Reviewer declaration is a recorded assertion, not identity verification",
        ]
    }
    if annotations is None:
        return result
    if not isinstance(annotations,list):
        raise ValueError("Annotations must be a JSON list")
    if len(annotations)!=12:
        raise ValueError("Exactly 12 human label records are required; no partial PASS")
    bynote={}
    for note in annotations:
        sid=note.get("source_id") if isinstance(note,dict) else None
        if not isinstance(sid,str) or sid in bynote:
            raise ValueError("Duplicate or invalid review source ID")
        bynote[sid]=note
    if set(bynote)!={x["source_id"] for x in cases}:
        raise ValueError("Human labels must match the frozen 12 sample IDs")
    validated=[_check_human_note(bynote[x["source_id"]],x,draft) for x in cases]
    summary=Counter(row["label"] for row in validated)
    pairs=[(byid[row["source_id"]],row["label"] in POSITIVE)
           for row in validated if row["label"] in POSITIVE|NEGATIVE]
    result["human_labels_present"]=len(validated)
    result["approved_human_label_count"]=0  # Owner acceptance is a separate gate
    result["label_distribution"]=dict(summary)
    result["excluded_from_binary_metrics"]=len(validated)-len(pairs)
    result["reviewer_record_hashes"]=[x["reviewer_record_sha256"] for x in validated]
    result["status"]="HUMAN_LABELS_READY_FOR_OWNER_VERIFICATION"
    if len(pairs)<8 or sum(v for _,v in pairs)<3 or sum(not v for _,v in pairs)<3:
        result["calibration_status"]="INSUFFICIENT_BALANCED_GOLDSET"
        return result
    # Fixed baseline is measurable. Candidates are displayed, NEVER applied
    # automatically; training and eval on same twelve cases is overfitting risk.
    result["baseline_confusion"]=_confusion(pairs,0.58,0.50)
    baseline_predictions=[machine_positive(row,recall=.58,anchors=.50)
                          for row,_ in pairs]
    result["baseline_machine_prediction_classes"]=len(set(baseline_predictions))
    if len(set(baseline_predictions))<2:
        result["calibration_status"]="NO_POSITIVE_NEGATIVE_PREDICTION_DIVERSITY"
        result["status"]="NEEDS_DIVERSE_HUMAN_HOLDOUT"
        result["followup_sampling"]="Add independently human-labeled exact, lexical, semantic-paraphrase and deliberate-omission examples"
        return result
    options=[]
    for recall,anchor in THRESHOLD_OPTIONS:
        c=_confusion(pairs,recall,anchor)
        options.append({"lexical_recall":recall,
                        "distinctive_anchor_recall":anchor,**c})
    options.sort(key=lambda x:(
        -(x["f1"] if x["f1"] is not None else -1),
        x["fp"],x["fn"],abs(x["lexical_recall"]-0.58)))
    result["exploratory_candidates"]=options[:5]
    result["calibration_status"]="EXPLORATORY_ONLY_NEEDS_INDEPENDENT_HOLDOUT"
    result["status"]="OWNER_REVIEW_OF_EXPLORATORY_CALIBRATION_REQUIRED"
    return result

def reviewer_agreement(packet:dict,source:str,draft:str,
                       first:list[dict]|None,second:list[dict]|None)->dict:
    """Independent double-blind labels and Cohen's kappa; no auto Owner approval."""
    cases=validate_packet(packet,source,draft)
    base={
      "contract":"andy-write-independent-reviewer-agreement-v1.2.2",
      "source_sha256":hashtext(source),"draft_sha256":hashtext(draft),
      "sample_count":len(cases),
      "first_reviewer_verified_count":0,
      "second_reviewer_verified_count":0,
      "exact_agreement_percent":None,
      "cohens_kappa":None,
      "disagreement_ids":[],
      "owner_approval":"PENDING",
      "status":"TWO_INDEPENDENT_HUMAN_REVIEWS_REQUIRED"
    }
    if first is None or second is None:
        return base
    if not isinstance(first,list) or not isinstance(second,list):
        raise ValueError("Each reviewer must supply 12 separate human notes")
    if len(first)!=len(cases) or len(second)!=len(cases):
        raise ValueError("Two complete 12-item reviewer reports required")
    canonical={x["source_id"]:x for x in cases}
    def validated(notes:list[dict])->dict:
        output={}
        for record in notes:
            if not isinstance(record,dict):
                raise ValueError("Invalid reviewer annotation")
            sid=record.get("source_id")
            if sid not in canonical or sid in output:
                raise ValueError("Reviewer data missing, duplicate or unknown source ID")
            output[sid]=_check_human_note(record,canonical[sid],draft)
        return output
    a,b=validated(first),validated(second)
    names_a={x["reviewer"] for x in a.values()}
    names_b={x["reviewer"] for x in b.values()}
    if len(names_a)!=1 or len(names_b)!=1 or names_a==names_b:
        raise ValueError("Independent reports must be from two distinct reviewers")
    labels=[(a[x["source_id"]]["label"],b[x["source_id"]]["label"])
            for x in cases]
    same=sum(x==y for x,y in labels)
    n=len(labels)
    pa=Counter(x for x,y in labels)
    pb=Counter(y for x,y in labels)
    prob=sum(pa[x]*pb[x] for x in LABEL_OPTIONS)/(n*n)
    observed=same/n
    kappa=(observed-prob)/(1-prob) if prob<1 else (
        1.0 if observed==1 else None)
    base.update({
      "first_reviewer_verified_count":n,
      "second_reviewer_verified_count":n,
      "first_reviewer_id_sha256":hashtext(list(names_a)[0]),
      "second_reviewer_id_sha256":hashtext(list(names_b)[0]),
      "exact_agreement_percent":round(observed*100,2),
      "cohens_kappa":round(kappa,4) if kappa is not None else None,
      "disagreement_ids":[cases[i]["source_id"] for i,(x,y) in enumerate(labels)
                          if x!=y],
      "arbitration_required":same!=n,
      "owner_approval":"PENDING",
      "status":"REQUIRES_OWNER_ARBITRATION" if same!=n else
               "AGREEMENT_COMPUTED_NOT_OWNER_APPROVED"
    })
    return base
