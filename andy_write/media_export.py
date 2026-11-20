"""Export reviewed low-weight previews from actual generated PNG originals.

Never re-encode or overwrite originals in .runs. Preview assets are for
Owner/GitHub review only, not approved WordPress media.
"""
from __future__ import annotations
import json
import pathlib
import re
import shutil
import subprocess
from .io import ROOT, outdir, write_json
from .content_quality import split_sections
from .media_workflow import review_ready

def export_review_preview(job: dict, article: str, *,
                          quality: int = 84) -> dict:
    if not 60 <= quality <= 95:
        raise ValueError("WebP review quality must be between 60 and 95")
    cwebp = shutil.which("cwebp")
    if cwebp is None:
        raise RuntimeError("cwebp is required to create a WebP preview")
    r = outdir(job)
    path = r / "media-manifest.json"
    if not path.exists():
        raise RuntimeError("No R3 media manifest; import generated images first")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    audit = review_ready(manifest)
    if not audit["review_ready"]:
        raise RuntimeError("Review preview blocked: missing or rejected images")
    output = ROOT / "examples" / "output" / "media-review" / job["job_id"]
    output.mkdir(parents=True, exist_ok=True)
    exported = []
    for item in manifest["assets"]:
        source = pathlib.Path(item["image_path"])
        if not source.is_file():
            raise RuntimeError("Generated original missing before preview export")
        name = item["id"] + ".webp"
        dest = output / name
        proc = subprocess.run(
            [cwebp, "-quiet", "-q", str(quality), "-m", "6",
             str(source), "-o", str(dest)], capture_output=True,
            text=True, timeout=45)
        if proc.returncode or not dest.exists() or dest.stat().st_size < 1000:
            raise RuntimeError(f"WebP review preview failed: {item['id']}")
        exported.append({
            "id": item["id"], "section": item.get("section"),
            "preview": name,
            "bytes": dest.stat().st_size,
            "original_sha256": item["image_sha256"],
            "seo_metadata": item["seo_metadata"],
            "machine_visual_review": item["visual_review"],
            "human_approval": "PENDING",
            "ai_generated": True,
            "authentic_product_photograph": False,
        })
    write_json(output / "manifest-review.json", {
        "job_id": job["job_id"], "scope": "GitHub review only; AI-generated illustrative scenes, not authenticated product photos; not WordPress uploaded",
        "assets": exported,
        "human_approval": "PENDING",
        "wordpress_publish_allowed": False,
    })
    article_lines = article.splitlines()
    if not article_lines or not article_lines[0].startswith("# "):
        raise ValueError("Article H1 is missing")
    images = {x["section"]: x for x in exported if x["section"]}
    cover = next(x for x in exported if x["id"] == "cover")
    cover_meta = cover["seo_metadata"]
    cover_markdown = (f'![{cover_meta["alt"]}](./media-review/{job["job_id"]}/{cover["preview"]})'
                      + "\n\n" + f'*AI-generated illustration — {cover_meta["caption"]}*')
    rendered = [article_lines[0], "", cover_markdown]
    for line in article_lines[1:]:
        rendered.append(line)
        if line.startswith("## "):
            section = line[3:].strip()
            if section in images:
                image = images[section]
                seo = image["seo_metadata"]
                rendered.extend(["", f'![{seo["alt"]}](./media-review/{job["job_id"]}/{image["preview"]})',
                                 "", f'*AI-generated illustration — {seo["caption"]}*'])
    dest = ROOT / "examples" / "output" / (job["job_id"] + "-with-media-review.md")
    dest.write_text("\n".join(rendered).rstrip()+"\n", encoding="utf-8")
    return {
        "preview_markdown": str(dest),
        "assets_exported": len(exported),
        "asset_dir": str(output),
        "assets_total_bytes": sum(x["bytes"] for x in exported),
        "human_approval": "PENDING",
        "wordpress_upload": "NOT_PERFORMED",
    }
