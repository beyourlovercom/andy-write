"""Command line runner for R0–R2."""
from __future__ import annotations
import argparse
import json
import sys
from .io import read_job, outdir, resolved, write_json, hashtext, now
from .research import research
from .cache import cached_research
from .source import classify, evidence
from .outline import section_plan, markdown_outline
from .llm import prepare_prompt, write_openai
from .codex_cli import DEFAULT_MODEL, run_writing, summarize_usage
from .review import check
from .benchmark import scrape_qc_metrics, compare_draft
from .content_quality import audit
from .media import plan_media, verify_media_manifest

def run(job: dict):
    out = outdir(job)
    original = resolved(job["source_path"]).read_text(encoding="utf-8")
    pack, was_cached = cached_research(job, out)
    catalog = classify(original, job["source_url"])
    ledger = evidence(pack, catalog)
    sections = section_plan(job, catalog)
    outline = markdown_outline(job, sections, ledger)
    prompt = prepare_prompt(job, original, outline, catalog, ledger)
    write_json(out / "research-pack.json", pack)
    write_json(out / "source-catalog.json", catalog)
    write_json(out / "evidence-ledger.json", ledger)
    write_json(out / "section-plan.json", sections)
    (out / "outline.md").write_text(outline, encoding="utf-8")
    (out / "writing-prompt.md").write_text(prompt, encoding="utf-8")
    write_json(out / "run-manifest.json", {
        "job_id": job["job_id"], "created_at": now(), "source_sha256": hashtext(original),
        "research_mode": pack["collection_mode"], "research_cache_hit": was_cached,
        "steps_completed": ["R1 Research", "R1 Source", "R2 Outline", "R2 Prompt"],
        "prose_status": "NOT_GENERATED_BY_THIS_COMMAND", "wordpress_status": "UNTOUCHED"
    })
    print(json.dumps({"job_id": job["job_id"], "output": str(out),
                      "research_mode": pack["collection_mode"], "research_cache_hit": was_cached,
                      "research_sources_retrieved": sum(x.get("status") == "retrieved" for x in pack["sources"]),
                      "reference_segments": len(catalog["segments"]), "sections": len(sections),
                      "draft": "prompt ready; model authoring needs --write or imported reviewed text"},
                     indent=2))

def write(job: dict, model: str | None, provider: str, target: int,
          tolerance: float, max_revisions: int, force: bool):
    out = outdir(job)
    prompt_path = out / "writing-prompt.md"
    if not prompt_path.is_file():
        raise RuntimeError("Run research/source/outline first")
    if provider == "codex":
        result = run_writing(job, model or DEFAULT_MODEL, target, tolerance,
                             max_revisions, force)
        print(json.dumps({"status": result["status"], "job_id": job["job_id"],
             "model": result["model"], "target_words": target,
             "actual_words": result["actual_words"],
             "range": result["allowed_range"], "cache_hits": result["cache_hits"],
             "usage": summarize_usage(out), "local_final":
             str(out / "article-auto-final.md"),
             "factual_review": "PENDING", "wordpress": "UNTOUCHED"}, indent=2))
        return
    if provider == "openai":
        draft, receipt = write_openai(prompt_path.read_text(encoding="utf-8"),
                                      model or "gpt-6.1-terra")
        (out / "article-v1.md").write_text(draft + "\n", encoding="utf-8")
        write_json(out / "model-receipt.json", receipt)
        write_json(out / "review-v1.json", check(draft, job))
        print("OpenAI API draft saved locally; no WordPress publishing")
        return
    raise ValueError("Choose provider=codex or provider=openai")

def review(job: dict, path: str):
    if not path:
        raise ValueError("--draft PATH is required")
    dest = resolved(path)
    if not dest.is_file():
        raise FileNotFoundError(str(dest))
    result = check(dest.read_text(encoding="utf-8"), job)
    output = outdir(job) / ("review-" + dest.stem + ".json")
    write_json(output, result)
    print(json.dumps({"status": result["status"], "metrics": result["metrics"],
                      "issues": result["issues"], "report": str(output)}, indent=2))

def quality(job: dict, path: str):
    """Independent non-LLM editorial QA for a local article."""
    article_path = resolved(path)
    if not article_path.is_file():
        raise FileNotFoundError(str(article_path))
    out = outdir(job)
    research_path, source_path = out / "research-pack.json", out / "source-catalog.json"
    pack = json.loads(research_path.read_text(encoding="utf-8")) if research_path.is_file() else None
    catalog = json.loads(source_path.read_text(encoding="utf-8")) if source_path.is_file() else None
    body = article_path.read_text(encoding="utf-8")
    report = audit(body, job, pack, catalog)
    static = check(body, job)
    status = "REVIEW_REQUIRED" if report["issues"] or static["issues"] else "RULE_CHECK_PASS"
    output = out / ("quality-report-" + article_path.stem + ".json")
    write_json(output, {"job_id": job["job_id"], "path": str(article_path),
                       "status": status, "content": report, "static": static,
                       "caveat": "Editorial heuristics only; no AI-authorship prediction or fact approval."})
    print(json.dumps({
        "status": status, "report": str(output),
        "content_issues": [(v["code"], v.get("heading")) for v in report["issues"]],
        "source_specificity": [report["source_details_present"], report["eligible_source_detail_count"]],
        "links": {"internal": len(report["links"]["internal"]), "external": len(report["links"]["external"])},
        "introduction": report["introduction"]
    }, indent=2))

def media_plan(job: dict, path: str):
    article_path = resolved(path)
    if not article_path.is_file():
        raise FileNotFoundError(str(article_path))
    manifest = plan_media(job, article_path.read_text(encoding="utf-8"))
    out = outdir(job) / "media-manifest.json"
    write_json(out, manifest)
    validated = verify_media_manifest(manifest)
    print(json.dumps({"file": str(out), "stage": manifest["stage"],
                      "planned": len(manifest["assets"]),
                      "verified": 0, "publish_ready": validated["status"] == "READY"}, indent=2))

def benchmark(job: dict):
    bench = scrape_qc_metrics()
    dest = outdir(job) / "benchmark.json"
    article = outdir(job) / "article-v2.md"
    if article.exists():
        bench["comparison"] = compare_draft(bench, article.read_text(encoding="utf-8"))
    write_json(dest, bench)
    print(json.dumps({"sample_count": bench["sample_count"], "median": bench["median"],
                      "report": str(dest)}, indent=2))

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Andy Write V1.0 R0–R2")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "write", "pipeline", "usage", "review", "quality", "media-plan", "benchmark"):
        sp = sub.add_parser(name)
        sp.add_argument("--job", required=True)
        if name in ("write", "pipeline"):
            sp.add_argument("--provider", choices=["codex", "openai"], default="codex")
            sp.add_argument("--model", default=None)
            sp.add_argument("--target-words", type=int, default=1000)
            sp.add_argument("--tolerance", type=float, default=0.07)
            sp.add_argument("--max-revisions", type=int, default=1)
            sp.add_argument("--force", action="store_true")
        if name in ("review", "quality", "media-plan"):
            sp.add_argument("--draft", required=True)
    args = parser.parse_args(argv)
    try:
        job = read_job(args.job)
        if args.command in ("run", "pipeline"):
            run(job)
        if args.command in ("write", "pipeline"):
            write(job, args.model, args.provider, args.target_words,
                  args.tolerance, args.max_revisions, args.force)
        elif args.command == "review":
            review(job, args.draft)
        elif args.command == "quality":
            quality(job, args.draft)
        elif args.command == "media-plan":
            media_plan(job, args.draft)
        elif args.command == "usage":
            print(json.dumps(summarize_usage(outdir(job)), indent=2))
        elif args.command == "benchmark":
            benchmark(job)
        return 0
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Andy Write error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
