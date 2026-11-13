"""Data persistence with job isolation; never persist credentials."""
from __future__ import annotations
import hashlib
import json
import pathlib
import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent

def read_job(path: str | pathlib.Path) -> dict:
    source = pathlib.Path(path)
    if not source.is_absolute():
        source = ROOT / source
    job = json.loads(source.read_text(encoding="utf-8"))
    required = ("job_id", "brand", "topic", "target_title", "source_path", "source_url", "output_dir")
    missing = [key for key in required if not job.get(key)]
    if missing:
        raise ValueError(f"Missing job fields: {', '.join(missing)}")
    if "/" in job["job_id"] or ".." in job["job_id"]:
        raise ValueError("Invalid job ID")
    brand_path = ROOT / "configs" / "brands" / (job["brand"] + ".json")
    if not brand_path.is_file():
        raise ValueError("No brand profile for this job")
    brand = json.loads(brand_path.read_text(encoding="utf-8"))
    if brand.get("editorial_source_policy") == "user_supplied_reference_required":
        original = resolved(job["source_path"])
        if not original.is_file() or not original.read_text(encoding="utf-8").strip():
            raise RuntimeError("User-supplied reference is required before drafting")
    return job

def resolved(relative: str) -> pathlib.Path:
    candidate = (ROOT / relative).resolve()
    if not candidate.is_relative_to(ROOT):
        raise ValueError("Path escapes Andy Write repository")
    return candidate

def outdir(job: dict) -> pathlib.Path:
    p = resolved(job["output_dir"])
    if not p.is_relative_to((ROOT / ".runs").resolve()):
        raise ValueError("Job output must remain in gitignored .runs/")
    p.mkdir(parents=True, exist_ok=True)
    return p

def write_json(path: pathlib.Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def hashtext(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
