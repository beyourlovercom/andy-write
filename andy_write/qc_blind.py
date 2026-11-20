"""Independent source holdout seal/check; cannot silently begin evaluation.

A truly blind holdout must not be used for engineering examples, threshold
selection or output comparison before reviewer ground truth is fixed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .io import ROOT

CONTRACT="andy-write-sealed-holdout-v1.2.3"

def check_holdout(manifest:dict,source_bytes:bytes,
                  calibration:dict|None=None,
                  independent_agreement:dict|None=None)->dict:
    if not isinstance(manifest,dict):
        raise ValueError("Holdout manifest must be a dictionary")
    if manifest.get("status")!="SEALED_UNSEEN_HOLDOUT_NO_EVALUATION":
        raise ValueError("Holdout is not sealed or was already used")
    if hashlib.sha256(source_bytes).hexdigest()!=manifest.get("sha256"):
        raise ValueError("Sealed source SHA-256 mismatch; refuse test")
    if len(source_bytes)!=manifest.get("bytes"):
        raise ValueError("Sealed source byte length mismatch")
    previous=manifest.get("testing",{})
    if (previous.get("rewrites_completed") or previous.get("labels_completed")
            or previous.get("training_access")):
        raise ValueError("Holdout contamination; cannot claim independent blind evaluation")
    calibration_status=calibration.get("calibration_status") if calibration else "NO_HUMAN_CALIBRATION"
    agreement_status=(independent_agreement.get("status")
                      if independent_agreement else "NO_INDEPENDENT_REVIEWERS")
    eligible=(calibration_status=="EXPLORATORY_ONLY_NEEDS_INDEPENDENT_HOLDOUT"
              and agreement_status=="AGREEMENT_COMPUTED_NOT_OWNER_APPROVED")
    # Even with reviewer data, a human Owner must explicitly authorize the
    # separate evaluation; this helper never launches a model or reads article.
    return {
       "contract":CONTRACT,
       "sha256":manifest["sha256"],
       "source_bytes":len(source_bytes),
       "sealed":True,
       "calibration_status":calibration_status,
       "reviewer_agreement_status":agreement_status,
       "engineering_prerequisites_ready":bool(eligible),
       "owner_explicit_unseal_approval":"PENDING",
       "automatic_model_evaluation_allowed":False,
       "status":("READY_FOR_SEPARATE_OWNER_UNSEAL_DECISION"
                 if eligible else "HOLDOUT_SEALED_WAITING_FOR_HUMAN_GOLDSET")
    }

def verify_private_holdout(manifest_path:Path,source_path:Path,
                           out_path:Path,
                           calibration_path:Path|None=None,
                           agreement_path:Path|None=None)->dict:
    private=(ROOT/".runs").resolve()
    locations=[p for p in (manifest_path,source_path,out_path,
                           calibration_path,agreement_path) if p is not None]
    if any(not p.resolve().is_relative_to(private) for p in locations):
        raise PermissionError("Blind source, manifests and reviews must stay in private .runs")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    calibration=json.loads(calibration_path.read_text(encoding="utf-8")) if calibration_path else None
    agreement=json.loads(agreement_path.read_text(encoding="utf-8")) if agreement_path else None
    receipt=check_holdout(manifest,source_path.read_bytes(),calibration,agreement)
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return receipt
