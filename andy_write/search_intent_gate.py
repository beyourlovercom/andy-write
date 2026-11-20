"""Dev-only bridge from Search Intent V1.1 handoff to Andy Write Source/Outline.

This module consumes the *existing* Skill's report and validated contract. It
never performs SERP retrieval, changes the Owner scope, or approves publication.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

from .io import ROOT, now, write_json

FLAG = "ANDY_WRITE_SEARCH_INTENT_R7_ENABLED"
ENV = "ANDY_WRITE_ENV"
VALIDATOR = ROOT / "skills/andy-write-search-intent/scripts/validate_contract.py"
VERSION = "andy-write-search-intent/v1"


class SearchIntentGateError(RuntimeError):
    """Research may exist, but Source/Outline must not begin."""


def enabled() -> bool:
    value = os.environ.get(FLAG, "0")
    if value not in ("0", "1"):
        raise SearchIntentGateError(f"{FLAG} must be 0 or 1")
    if value == "1" and os.environ.get(ENV) != "dev":
        raise SearchIntentGateError("Search Intent R7 may run only with ANDY_WRITE_ENV=dev")
    return value == "1"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _receipt(out: pathlib.Path, entry: dict) -> None:
    """Keep every distinct evidence decision; retries do not duplicate it."""
    folder = out / "search-intent-decisions"
    folder.mkdir(parents=True, exist_ok=True)
    identity = _sha(json.dumps({k: v for k, v in entry.items() if k != "checked_at"},
                               sort_keys=True, ensure_ascii=False).encode())
    path = folder / (identity + ".json")
    if not path.exists():
        try:
            with path.open("x", encoding="utf-8") as handle:
                json.dump(entry, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
        except FileExistsError:
            pass
    write_json(out / "search-intent-decision.json", entry)


def _fail(out: pathlib.Path, base: dict, reason: str, gate: str = "BLOCK") -> None:
    entry = {**base, "gate": gate, "next_stage": "STOP", "reason": reason}
    _receipt(out, entry)
    raise SearchIntentGateError(f"Search Intent {gate}: {reason}")


def enforce(job: dict, owner_scope: dict, out: pathlib.Path) -> dict:
    """Allow Source only on canonical PASS and exact frozen Owner-scope match."""
    if not enabled():
        return {"status": "DISABLED"}
    private = (ROOT / ".runs").resolve()
    if not out.resolve().is_relative_to(private):
        raise SearchIntentGateError("Search Intent artifacts must stay inside private .runs")
    base = {"version": VERSION, "job_id": job["job_id"],
            "owner_scope_fingerprint": owner_scope["scope_fingerprint"],
            "checked_at": now(), "publish_ready": False}
    contract_file = out / "intent_contract.json"
    report_file = out / "intent_report.md"
    if not contract_file.is_file() or not report_file.is_file():
        _fail(out, base, "V1.1 intent_contract.json and intent_report.md are required")
    raw = contract_file.read_bytes()
    report_raw = report_file.read_bytes()
    base.update({"contract_sha256": _sha(raw), "report_sha256": _sha(report_raw)})
    if not report_raw.strip():
        _fail(out, base, "Intent report is empty")
    try:
        contract = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        _fail(out, base, "Intent contract is invalid JSON")
    validation = subprocess.run([sys.executable, str(VALIDATOR), str(contract_file)],
                                capture_output=True, text=True, timeout=8, check=False)
    if validation.returncode:
        _fail(out, base, "V1.1 contract validation failed: " +
              (validation.stderr.strip() or "unknown error")[:650])
    target = job.get("target_keyword")
    expected = job.get("search_intent_scope")
    if not isinstance(target, str) or not target.strip() or not isinstance(expected, dict):
        _fail(out, base, "Owner target_keyword and explicit search_intent_scope required")
    if contract.get("target_keyword") != target:
        _fail(out, base, "Target keyword differs from Owner job")
    site = job.get("brand_domain")
    if not isinstance(site, str) or contract.get("site", "").lower() != site.lower():
        _fail(out, base, "Target site differs from Owner job")
    scope = contract["scope"]
    for field in ("audience", "market_country", "language", "device"):
        if not isinstance(expected.get(field), str) or scope[field] != expected[field]:
            _fail(out, base, f"Search Intent {field} differs from Owner job")
    if scope.get("owner_scope_contract_id") != owner_scope["scope_fingerprint"]:
        _fail(out, base, "Owner Scope Contract fingerprint is missing or changed")
    if scope.get("owner_requirements_preserved") is not True:
        _fail(out, base, "Owner P0 preservation was not confirmed")
    gate = contract["gate"]
    if gate != "PASS":
        _fail(out, base, "QC returned " + gate + "; Owner review/evidence required", gate)
    entry = {**base, "gate": "PASS", "next_stage": "SOURCE", "reason":
             "Validated Skill contract and exact Owner scope; Dev-only progression"}
    _receipt(out, entry)
    return entry
