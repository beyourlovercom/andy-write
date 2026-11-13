"""Owner policy: Codex CLI is only for rewriting a supplied article."""
from __future__ import annotations
import json
import pathlib
from .io import hashtext, resolved

POLICY_VERSION = "ANDY_WRITE_CODEX_REWRITE_ONLY_2026_11_13"
ALLOWED_REWRITE_STAGES = frozenset({
    "rewrite", "edit", "quality-chapters-1", "quality-chapters-2",
    "tighten-1", "tighten-2"
})

def permit_codex_stage(stage: str) -> None:
    if stage not in ALLOWED_REWRITE_STAGES:
        raise PermissionError("Codex CLI prohibited: only supplied-article rewriting is authorized")

def block_media_generation(kind: str) -> None:
    if kind.lower() in {"image", "video"}:
        raise PermissionError("Owner policy: image and video generation are disabled")

def verified_source_article(job: dict, directory: pathlib.Path) -> str:
    name = job.get("source_path")
    if not isinstance(name, str) or not name.strip():
        raise PermissionError("Codex requires an actual user-supplied article")
    if not job.get("source_url"):
        raise PermissionError("Article rewriting requires provenance")
    manifest = directory / "run-manifest.json"
    if not manifest.is_file():
        raise PermissionError("Source manifest is missing; run local research first")
    path = resolved(name)
    if not path.is_file():
        raise PermissionError("Original article is missing")
    original = path.read_text(encoding="utf-8")
    if len("".join(original.split())) < 900:
        raise PermissionError("Only substantive original articles may be rewritten")
    record = json.loads(manifest.read_text(encoding="utf-8"))
    if record.get("source_sha256") != hashtext(original):
        raise PermissionError("Source changed; refresh source processing first")
    return original
