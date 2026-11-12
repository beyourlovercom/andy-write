"""R3 static image task manifest; generation and visual verification are separate.

Metadata is intentionally NULL until a real image is created and reviewed.
"""
from __future__ import annotations
import hashlib
import pathlib
import re
from .io import now
from .content_quality import split_sections

def image_scene(heading: str) -> str:
    h = heading.lower()
    if "prepare" in h or "before the package" in h:
        return "flat lay showing a shipping order receipt, tape cutter, clear surface, phone camera, protective cloth"
    if "before you open" in h or "carton" in h:
        return "sealed cardboard shipment carton photographed from several angles, one scuffed corner visible"
    if "unpack" in h or "move" in h:
        return "careful two-person handling of a large padded package near a stable unpacking table"
    if "inspection" in h or "checklist" in h:
        return "well-lit inventory checklist beside foam packing, protected accessory bags and a phone camera"
    if "missing" in h or "damaged" in h:
        return "documenting a damaged carton corner with a phone, shipping paperwork nearby"
    if "clean" in h or "setup" in h:
        return "clean supported workspace with folded soft cloth and product care instruction booklet"
    return "practical non-explicit editorial still life representing the reader's question: " + heading

def plan_media(job: dict, article: str) -> dict:
    if not article.startswith("# "):
        raise ValueError("An article with Markdown H1 is required")
    h1 = article.splitlines()[0].lstrip("# ").strip()
    h2s = [s for s in split_sections(article) if s["heading"] != "Conclusion"]
    if not h2s:
        raise ValueError("No question-form H2 available for media planning")
    records = []
    scenes = [("cover", None, "sealed delivery carton on a clear inspection table, order receipt and phone camera")]
    scenes.extend((f"h2-{i:02}", s["heading"], image_scene(s["heading"]))
                  for i,s in enumerate(h2s, 1))
    for name, heading, scene in scenes:
        target = "Cover for: " + h1 if heading is None else "Illustrates: " + heading
        records.append({
            "id": name,
            "section": heading,
            "goal": target,
            "prompt": ("Create a practical, high-resolution, non-explicit editorial image: "
                       + scene + ". Neutral clear lighting, realistic materials, natural composition, "
                       "no text labels, no watermark, no identifiable person, no explicit anatomy."),
            "status": "generation_pending",
            "image_path": None,
            "image_sha256": None,
            "visual_review": "PENDING",
            "seo_metadata": {
                "title": None, "alt": None, "caption": None, "description": None
            }
        })
    return {
        "job_id": job["job_id"], "created_at": now(),
        "stage": "R3_MEDIA_PLANNING_ONLY",
        "assets": records,
        "note": "Image prompts are not generated images. Title/alt/caption/description must be based on inspected actual pixels after creation."
    }

def verify_media_manifest(manifest: dict) -> dict:
    failures = []
    ids = set()
    alts = set()
    for asset in manifest.get("assets", []):
        ident = asset.get("id")
        if not ident or ident in ids:
            failures.append({"id": ident, "problem": "duplicate_or_missing_id"})
        ids.add(ident)
        file = asset.get("image_path")
        declared_hash = asset.get("image_sha256")
        visual = asset.get("visual_review")
        if asset.get("status") != "visual_verified" or not file or not declared_hash:
            failures.append({"id": ident, "problem": "image_not_verified"})
        else:
            source = pathlib.Path(file)
            if not source.is_file() or source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                failures.append({"id": ident, "problem": "image_file_unavailable"})
            elif hashlib.sha256(source.read_bytes()).hexdigest() != declared_hash:
                failures.append({"id": ident, "problem": "image_checksum_mismatch"})
        if not isinstance(visual, dict) or not visual.get("reviewer") or not visual.get("reviewed_at"):
            failures.append({"id": ident, "problem": "visual_review_missing"})
        seo = asset.get("seo_metadata") or {}
        for field in ("title", "alt", "caption", "description"):
            if not seo.get(field):
                failures.append({"id": ident, "problem": "missing_" + field})
        if seo.get("alt") and seo["alt"].strip().lower() in alts:
            failures.append({"id": ident, "problem": "duplicate_alt"})
        if seo.get("alt"):
            alts.add(seo["alt"].strip().lower())
    return {"status": "READY" if manifest.get("assets") and not failures else "BLOCK",
            "issues": failures,
            "note": "This validates fields only, not visual accuracy; human/vision review is required."}
