"""Ingest verified generated raster assets into a review-only media manifest.

The generator and the visual inspector are separate. Machine-assisted visual
review is never represented as Owner approval or permission to publish.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import struct
from .io import now, outdir, write_json
from .media import plan_media

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
SEO_FIELDS = ("title", "alt", "caption", "description")

def png_dimensions(path: pathlib.Path) -> tuple[int, int]:
    with path.open("rb") as f:
        header = f.read(24)
    if len(header) != 24 or not header.startswith(PNG_MAGIC) or header[12:16] != b"IHDR":
        raise ValueError("Not a real PNG raster image")
    width, height = struct.unpack(">II", header[16:24])
    if width < 1200 or height < 675 or not 1.65 <= width / height <= 1.9:
        raise ValueError(f"Unexpected dimensions: {width}x{height}")
    return width, height

def normalize_observations(data: object) -> list[dict]:
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for key in ("images", "observations", "assets"):
            if isinstance(data.get(key), list):
                return [r for r in data[key] if isinstance(r, dict)]
    raise ValueError("Expected JSON array of actual pixel observations")

def title_clean(value: str, max_length: int) -> str:
    txt = re.sub(r"\s+", " ", str(value).strip())
    if not 10 <= len(txt) <= max_length:
        raise ValueError("Empty or overlong image SEO field")
    if re.search(r"\b(placeholder|lorem ipsum|image prompt)\b", txt, re.I):
        raise ValueError("Image metadata contains placeholder text")
    return txt

def import_observations(job: dict, article: str, observations: object) -> dict:
    directory = outdir(job)
    image_dir = (directory / "media").resolve()
    manifest_file = directory / "media-manifest.json"
    if manifest_file.is_file():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    else:
        manifest = plan_media(job, article)
    all_obs = normalize_observations(observations)
    by_id = {}
    for obs in all_obs:
        key = obs.get("id")
        if key and key not in by_id:
            by_id[key] = obs
    accepted, rejected = [], []
    alt_seen = set()
    for item in manifest["assets"]:
        ident = item["id"]
        image_file = image_dir / (ident + ".png")
        observation = by_id.get(ident)
        try:
            if not observation:
                raise ValueError("No actual visual inspection record")
            if not observation.get("tool_generated"):
                raise ValueError("No verified image-generation tool result")
            if observation.get("reviewer") != "codex_image_vision_review":
                raise ValueError("Unknown machine vision reviewer")
            if observation.get("matches_article_section") is not True:
                raise ValueError("Image does not match target H2 scene")
            if observation.get("mismatches"):
                raise ValueError("Visual inspection flagged image mismatches")
            objects = observation.get("visible_objects") or []
            if len(objects) < 2 or not observation.get("observed_scene"):
                raise ValueError("Visual description is not grounded in observed objects")
            if not image_file.resolve().is_relative_to(image_dir):
                raise ValueError("Image path escapes private job directory")
            width, height = png_dimensions(image_file)
            data = image_file.read_bytes()
            metadata = observation.get("seo_metadata") or {}
            # Some AI agents use _draft names; accept draft values only if
            # grounded by the visual observation, never by the prompt alone.
            normalized = {field: title_clean(
                metadata.get(field) or observation.get(field + "_draft") or "",
                145 if field == "alt" else (100 if field == "title" else 300 if field == "caption" else 450))
                for field in SEO_FIELDS}
            alt_key = normalized["alt"].casefold()
            if alt_key in alt_seen:
                raise ValueError("Duplicate Alt text across article assets")
            alt_seen.add(alt_key)
            item.update({
                "status": "vision_review_pass",
                "image_path": str(image_file),
                "image_sha256": hashlib.sha256(data).hexdigest(),
                "image_width": width, "image_height": height,
                "visual_review": {
                    "reviewer": "codex_image_vision_review",
                    "reviewed_at": now(),
                    "observed_scene": observation["observed_scene"],
                    "visible_objects": objects,
                    "mismatches": [],
                    "human_review": "PENDING"
                },
                "seo_metadata": normalized,
                "ai_generated": True,
                "authentic_product_photograph": False,
            })
            accepted.append(ident)
        except (ValueError, OSError, TypeError) as err:
            item["status"] = "rejected_or_pending"
            item["review_error"] = str(err)
            rejected.append({"id": ident, "reason": str(err)})
    manifest["stage"] = "R3_VISION_CANDIDATES"
    manifest["imported_at"] = now()
    manifest["human_review"] = "PENDING"
    write_json(manifest_file, manifest)
    return {
        "status": "READY_FOR_OWNER_REVIEW" if len(accepted) == len(manifest["assets"]) else "PARTIAL",
        "accepted": accepted, "rejected": rejected,
        "asset_count": len(manifest["assets"]),
        "publish_ready": False,
        "manifest": str(manifest_file)
    }

def review_ready(manifest: dict) -> dict:
    """Images are candidates only. Publisher must also require owner approval."""
    complete = []
    for item in manifest.get("assets", []):
        review = item.get("visual_review")
        if item.get("status") == "vision_review_pass" and isinstance(review, dict):
            if review.get("human_review") == "PENDING":
                complete.append(item)
    return {
        "review_ready": bool(manifest.get("assets")) and len(complete) == len(manifest["assets"]),
        "vision_reviewed": len(complete),
        "total": len(manifest.get("assets", [])),
        "publish_ready": False
    }
