"""Reproducible *human* evidence review queue; no inferred factual approvals."""
from __future__ import annotations
import csv
from collections import Counter
from pathlib import Path
from .io import ROOT
from .claim_evidence import CONTRACT as CLAIM_CONTRACT

CATEGORIES=[
 ("WATERPROOF_ELECTRONICS",("waterproof","submerge","electronics","IPX")),
 ("HEAT_TEMPERATURE",("heat","hot","warming","sunlight","temperature","hair dryer")),
 ("LUBRICANT_CHEMICAL",("lubricant","oil","silicone-based","compatib","cleaner","fragrance","powder")),
 ("CLEANING_HYGIENE",("clean","wash","rinse","soap","disinfect","dry","condom")),
 ("STORAGE_MATERIAL",("store","storage","material","fabric","color","squeez")),
]
def category_for(claim:str)->str:
    c=claim.casefold()
    for category,keywords in CATEGORIES:
        if any(word.casefold() in c for word in keywords):
            return category
    return "GENERAL_HANDLING_OR_EDITORIAL"

def build_queue(report:dict,*,product_model:str|None=None)->dict:
    if report.get("contract")!=CLAIM_CONTRACT:
        raise ValueError("Unsupported important-claim report contract")
    claims=report.get("claims")
    if not isinstance(claims,list):
        raise ValueError("Missing claim list")
    rows=[]
    for item in claims:
        category=category_for(item["claim"])
        needs_model=("PRODUCT_OR_SAFETY_SPEC" in item["reason_codes"])
        rows.append({
            "claim_id":item["id"],
            "claim_sha256":item["claim_sha256"],
            "priority":item["importance"],
            "category":category,
            "claim":item["claim"],
            "current_evidence_state":item["status"],
            "manufacturer_model":product_model or "NOT_PROVIDED",
            "manufacturer_specific_evidence_required":needs_model,
            "source_url":"",
            "source_quote":"",
            "reviewer":"",
            "reviewer_decision":"PENDING",
            "reviewer_reason":"",
        })
    rows.sort(key=lambda r:(r["priority"]!="HIGH",r["category"],r["claim_id"]))
    high=[r for r in rows if r["priority"]=="HIGH"]
    groups=dict(Counter(row["category"] for row in high))
    return {
        "contract":"andy-write-human-evidence-queue-v1.2.3",
        "claim_report_sha256":report["draft_sha256"],
        "important_claims":len(rows),
        "high_priority":len(high),
        "medium_priority":len(rows)-len(high),
        "high_group_count":groups,
        "model_available":bool(product_model),
        "actual_human_fact_approvals":0,
        "status":"NEEDS_REAL_HUMAN_CLAIM_EVIDENCE",
        "rows":rows
    }

def export_queue(report:dict,out:Path,*,product_model:str|None=None)->dict:
    root=(ROOT/".runs").resolve()
    if not out.resolve().is_relative_to(root):
        raise PermissionError("Raw claim list and review queue must stay private")
    if out.suffix.lower()!=".csv":
        raise ValueError("Human evidence worklist must be .csv")
    payload=build_queue(report,product_model=product_model)
    out.parent.mkdir(parents=True,exist_ok=True)
    # Protect a human opening this CSV in spreadsheet apps from formula
    # injection. Full text remains private and source facts are not modified.
    def csv_safe(v):
        if isinstance(v,bool):
            return "YES" if v else "NO"
        s=str(v).replace("\r"," ").replace("\n"," ")
        return "'"+s if s.lstrip().startswith(("=","+","-","@")) else s
    with out.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(payload["rows"][0]) if
                              payload["rows"] else ["claim_id"])
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({k:csv_safe(v) for k,v in row.items()})
    return {k:v for k,v in payload.items() if k!="rows"}
