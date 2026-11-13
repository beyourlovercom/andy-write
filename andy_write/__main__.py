"""Command line runner for R0–R2."""
from __future__ import annotations
import argparse
import json
import sys
from .io import ROOT, read_job, outdir, resolved, write_json, hashtext, now
from .research import research
from .cache import cached_research
from .source import classify, evidence
from .outline import section_plan, markdown_outline
from .llm import prepare_prompt, write_openai
from .rewrite_contract import CONTRACT_VERSION, validate_prepared_prompt
from .fidelity import inspect_fidelity, review_sheet
from .qc_reverse import html_qc_profile, markdown_qc_profile, compare_structure, skill_gap_actions
from .qc_goldset import write_goldset
from .qc_calibration import calibrate
from .claim_evidence import trace_claims, apply_human_claim_reviews, claim_review_sheet
from .usage_policy import verified_source_article
from .codex_cli import DEFAULT_MODEL, run_writing, summarize_usage
from .review import check
from .benchmark import scrape_qc_metrics, compare_draft
from .content_quality import audit
from .media import plan_media, verify_media_manifest
from .media_workflow import import_observations, review_ready
from .media_export import export_review_preview

def run(job: dict):
    out = outdir(job)
    original = resolved(job["source_path"]).read_text(encoding="utf-8")
    pack, was_cached = cached_research(job, out)
    catalog = classify(original, job["source_url"])
    ledger = evidence(pack, catalog)
    sections = section_plan(job, catalog, original)
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
        "writing_prompt_sha256": hashtext(prompt),
        "rewrite_source_contract_version": CONTRACT_VERSION,
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
             "factual_review": "PENDING",
             "source_fidelity_review": result["source_fidelity"]["status"],
             "publish_ready": result["publish_ready"],
             "wordpress": "UNTOUCHED"}, indent=2))
        return
    if provider == "openai":
        full_prompt, source_receipt = validate_prepared_prompt(job, out)
        draft, receipt = write_openai(full_prompt, model or "gpt-6.1-terra")
        receipt["source_contract"] = source_receipt
        original = verified_source_article(job, out)
        mapping = inspect_fidelity(original, draft, source_ref=job["source_url"])
        write_json(out / "source-fidelity-report.json", mapping)
        (out / "source-fidelity-review.md").write_text(
            review_sheet(mapping), encoding="utf-8")
        evidence_path = out / "approved-evidence-snapshots.json"
        public_sources = (json.loads(evidence_path.read_text(encoding="utf-8"))
                          if evidence_path.is_file() else [])
        fact_trace = trace_claims(draft, original, public_sources)
        write_json(out / "claim-evidence-review.json", fact_trace)
        (out / "claim-evidence-review.md").write_text(
            claim_review_sheet(fact_trace), encoding="utf-8")
        receipt["claim_evidence_status"] = fact_trace["status"]
        receipt["claim_evidence_summary"] = fact_trace["summary"]
        receipt["source_fidelity_status"] = mapping["status"]
        receipt["publish_ready"] = False
        receipt["release_gate"] = "OWNER_HUMAN_FIDELITY_AND_FACT_REVIEW_REQUIRED"
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
    # Quality CLI is an actual release-oriented quality report, unlike a
    # syntactic static PASS. All significant claims need independent review.
    try:
        original = verified_source_article(job, out)
    except (FileNotFoundError, ValueError, PermissionError, RuntimeError):
        original = None
    evid_file = out / "approved-evidence-snapshots.json"
    external = (json.loads(evid_file.read_text(encoding="utf-8"))
                if evid_file.is_file() else [])
    facts = trace_claims(body, original, external) if original else None
    if facts:
        write_json(out / "claim-evidence-review.json", facts)
        (out / "claim-evidence-review.md").write_text(
            claim_review_sheet(facts), encoding="utf-8")
    # No automatic factual or semantic pass even when static checks pass.
    status = "REVIEW_REQUIRED"
    output = out / ("quality-report-" + article_path.stem + ".json")
    write_json(output, {"job_id": job["job_id"], "path": str(article_path),
                       "status": status, "content": report, "static": static,
                       "fact_claims": facts["summary"] if facts else None,
                       "fact_review":"PENDING" if facts else "SOURCE_GATE_MISSING",
                       "publish_ready":False,
                       "caveat": "Static structural QA cannot establish factual approval, "
                       "semantic fidelity or human authorship."})
    print(json.dumps({
        "status": status, "report": str(output),
        "content_issues": [(v["code"], v.get("heading")) for v in report["issues"]],
        "source_specificity": [report["source_details_present"], report["eligible_source_detail_count"]],
        "links": {"internal": len(report["links"]["internal"]), "external": len(report["links"]["external"])},
        "introduction": report["introduction"],
        "important_fact_claims": facts["summary"]["important_claims_total"] if facts else None,
        "human_fact_review": "PENDING" if facts else "SOURCE_GATE_MISSING",
        "publish_ready": False
    }, indent=2))

def media_plan(job: dict, path: str):
    article_path = resolved(path)
    if not article_path.is_file():
        raise FileNotFoundError(str(article_path))
    out = outdir(job) / "media-manifest.json"
    if out.is_file():
        old = json.loads(out.read_text(encoding="utf-8"))
        if any(asset.get("status") == "vision_review_pass"
               for asset in old.get("assets", [])):
            raise RuntimeError("Existing generated media cannot be overwritten by media-plan")
    manifest = plan_media(job, article_path.read_text(encoding="utf-8"))
    write_json(out, manifest)
    validated = verify_media_manifest(manifest)
    print(json.dumps({"file": str(out), "stage": manifest["stage"],
                      "planned": len(manifest["assets"]),
                      "verified": 0, "publish_ready": validated["status"] == "READY"}, indent=2))

def media_import(job: dict):
    out = outdir(job)
    obs = out / "media" / "visual-observations.json"
    if not obs.is_file():
        raise RuntimeError("Image visual observations not found; no images marked as passed")
    article = out / "article-auto-final.md"
    if not article.is_file():
        raise RuntimeError("Approved local article candidate missing")
    observations = json.loads(obs.read_text(encoding="utf-8"))
    result = import_observations(job, article.read_text(encoding="utf-8"), observations)
    print(json.dumps(result, indent=2))

def media_export(job: dict):
    out = outdir(job)
    article = out / "article-auto-final.md"
    if not article.is_file():
        raise RuntimeError("Local article candidate missing")
    result = export_review_preview(job, article.read_text(encoding="utf-8"))
    print(json.dumps(result, indent=2))

def fidelity(source_path: str, draft_path: str, report_path: str,
             notes_path: str | None = None):
    """Offline-only, source-to-draft traceability for any article or brand."""
    source_file = resolved(source_path)
    draft_file = resolved(draft_path)
    output = resolved(report_path)
    private_dir = (ROOT / ".runs").resolve()
    if not output.is_relative_to(private_dir):
        raise ValueError("Fidelity report must remain in ignored .runs directory")
    if not source_file.is_file() or not draft_file.is_file():
        raise FileNotFoundError("Fidelity source and draft must be existing files")
    if not source_file.is_relative_to(private_dir):
        raise PermissionError("Original source must be in private ignored .runs")
    notes = None
    if notes_path:
        p = resolved(notes_path)
        if not p.is_relative_to(private_dir):
            raise PermissionError("Reviewer notes must stay in private .runs")
        notes = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(notes, list):
            raise ValueError("Reviewer notes must be a JSON array")
    result = inspect_fidelity(
        source_file.read_text(encoding="utf-8"),
        draft_file.read_text(encoding="utf-8"),
        source_ref=source_path, reviewer_notes=notes)
    write_json(output, result)
    review_path = output.with_suffix(".review.md")
    review_path.write_text(review_sheet(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(output),
                      "manual_review_sheet": str(review_path),
                      "summary": result["summary"],
                      "caveat": result["metric_scope"]}, indent=2))

def qc_calibrate(packet_path:str,source_path:str,draft_path:str,
                 annotations_path:str|None,report_path:str):
    private=(ROOT/".runs").resolve()
    inputs=[resolved(packet_path),resolved(source_path),resolved(draft_path),
            resolved(report_path)]
    if annotations_path:
        inputs.append(resolved(annotations_path))
    if any(not p.is_relative_to(private) for p in inputs):
        raise PermissionError("Human calibration data and outputs stay in private .runs")
    if any(not p.is_file() for p in inputs[:3]):
        raise FileNotFoundError("Frozen packet, original and article draft required")
    annotations=(json.loads(resolved(annotations_path).read_text(encoding="utf-8"))
                 if annotations_path else None)
    result=calibrate(
        json.loads(resolved(packet_path).read_text(encoding="utf-8")),
        resolved(source_path).read_text(encoding="utf-8"),
        resolved(draft_path).read_text(encoding="utf-8"),
        annotations)
    write_json(resolved(report_path),result)
    print(json.dumps({k:v for k,v in result.items()
                      if k in ("status","sample_count","human_labels_present",
                               "calibration_status","owner_approval",
                               "baseline_confusion","calibrated_threshold")},
                     indent=2))


def qc_claims(source_path:str,draft_path:str,sources_path:str|None,
              report_path:str,notes_path:str|None=None):
    private=(ROOT/".runs").resolve()
    required=[resolved(source_path),resolved(report_path)]
    if sources_path:
        required.append(resolved(sources_path))
    if notes_path:
        required.append(resolved(notes_path))
    if any(not p.is_relative_to(private) for p in required):
        raise PermissionError("Source, external evidence and claim report stay in private .runs")
    draft=resolved(draft_path)
    if not resolved(source_path).is_file() or not draft.is_file():
        raise FileNotFoundError("Existing Owner original and rewritten article required")
    external=(json.loads(resolved(sources_path).read_text(encoding="utf-8"))
              if sources_path else [])
    result=trace_claims(
        draft.read_text(encoding="utf-8"),
        resolved(source_path).read_text(encoding="utf-8"),external)
    write_json(resolved(report_path),result)
    resolved(report_path).with_suffix(".review.md").write_text(
        claim_review_sheet(result),encoding="utf-8")
    if notes_path:
        notes=json.loads(resolved(notes_path).read_text(encoding="utf-8"))
        review=apply_human_claim_reviews(result,external,notes)
        write_json(resolved(report_path).with_suffix(".human-review.json"),review)
    print(json.dumps({"status":result["status"],
                      "report":str(resolved(report_path)),
                      "summary":result["summary"],
                      "publish_ready":result["publish_ready"]},indent=2))


def qc_goldset(source_path:str,draft_path:str,report_path:str,size:int):
    from .io import ROOT
    root=(ROOT/".runs").resolve()
    original=resolved(source_path)
    if not original.is_relative_to(root):
        raise ValueError("Owner source for human labels must remain private")
    target=resolved(draft_path)
    if not original.is_file() or not target.is_file():
        raise FileNotFoundError("Actual source and existing draft files are required")
    receipt=write_goldset(original.read_text(encoding="utf-8"),
                          target.read_text(encoding="utf-8"),
                          resolved(report_path),size)
    print(json.dumps(receipt,indent=2))

def qc_profile(post_file: str, draft_file: str, report_file: str,
               draft_url: str):
    """Offline only. A competitor article is a STRUCTURE BENCHMARK, not a writing source."""
    from .io import ROOT
    private = (ROOT / ".runs").resolve()
    post_path = resolved(post_file)
    report_path = resolved(report_file)
    draft_path = resolved(draft_file)
    if not post_path.is_relative_to(private) or not report_path.is_relative_to(private):
        raise ValueError("Competitor HTML and QC report must stay in private .runs")
    if not post_path.is_file() or not draft_path.is_file():
        raise FileNotFoundError("Private public-post snapshot and existing draft required")
    source = json.loads(post_path.read_text(encoding="utf-8"))
    if isinstance(source, list):
        if len(source) != 1:
            raise ValueError("One exact WordPress article required")
        source = source[0]
    if (not isinstance(source, dict) or
        not source.get("date","").startswith(("2025-11","2025-12"))):
        raise ValueError("Benchmark article must have 2025 November/December date")
    html = source["content"]["rendered"]
    profile = html_qc_profile(html,url=source["link"],date=source["date"],
                              modified=source.get("modified",""),
                              article_id=source.get("id"))
    current = markdown_qc_profile(draft_path.read_text(encoding="utf-8"),
                                   source_label=draft_url)
    result = {
        "benchmark": profile,
        "andy_write_existing_draft": current,
        "comparison": compare_structure(profile,current),
        "skill_change_candidates": skill_gap_actions(profile,current),
        "owner_policy": "SKILL_FIRST + EVIDENCE_BASED + VERSION_ROLLBACK",
        "no_model_calls": True,
        "competitor_rewrite": False,
        "publish_ready": False
    }
    write_json(report_path, result)
    print(json.dumps({
        "status":"STRUCTURAL_REVIEW_REQUIRED",
        "report":str(report_path),
        "benchmark_post_id":profile["source_post_id"],
        "first_published":profile["original_publication_date"],
        "modified":profile["last_public_modified"],
        "structure_diff":result["comparison"]["rows"],
        "caveat":result["comparison"]["important_context"]
    },indent=2))

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
    for name in ("run", "write", "pipeline", "usage", "review", "quality", "media-plan", "media-import", "media-export", "benchmark"):
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
    ca = sub.add_parser("qc-calibrate", help="Calibrate against actual human labels; never invent them")
    ca.add_argument("--packet",required=True)
    ca.add_argument("--source",required=True)
    ca.add_argument("--draft",required=True)
    ca.add_argument("--annotations",default=None)
    ca.add_argument("--report",required=True)
    claims = sub.add_parser("qc-claims", help="Trace important claims to exact retrieved passages, no Codex")
    claims.add_argument("--source",required=True)
    claims.add_argument("--draft",required=True)
    claims.add_argument("--sources",default=None,
                        help="Optional private JSON list of real fetched public sources")
    claims.add_argument("--report",required=True)
    claims.add_argument("--notes",default=None,
                        help="Optional actual human citation review decisions")
    gs = sub.add_parser("qc-goldset", help="Private human annotation packet, no Codex")
    gs.add_argument("--source",required=True)
    gs.add_argument("--draft",required=True)
    gs.add_argument("--report",required=True)
    gs.add_argument("--size",type=int,default=12)
    qa = sub.add_parser("qc-profile", help="Offline public-article QC blueprint (no Codex)")
    qa.add_argument("--post-json", required=True)
    qa.add_argument("--draft", required=True)
    qa.add_argument("--report", required=True)
    qa.add_argument("--draft-url", required=True,
                    help="URL/host context of existing Owner draft; avoid fixed brand")
    fv = sub.add_parser("fidelity", help="Offline full-article content mapping; no Codex")
    fv.add_argument("--source", required=True)
    fv.add_argument("--draft", required=True)
    fv.add_argument("--report", required=True)
    fv.add_argument("--notes", default=None,
                    help="Optional human-reviewed source mapping JSON in private .runs")
    args = parser.parse_args(argv)
    try:
        if args.command == "qc-calibrate":
            qc_calibrate(args.packet,args.source,args.draft,args.annotations,args.report)
            return 0
        if args.command == "qc-claims":
            qc_claims(args.source,args.draft,args.sources,args.report,args.notes)
            return 0
        if args.command == "qc-goldset":
            qc_goldset(args.source,args.draft,args.report,args.size)
            return 0
        if args.command == "qc-profile":
            qc_profile(args.post_json,args.draft,args.report,args.draft_url)
            return 0
        if args.command == "fidelity":
            fidelity(args.source, args.draft, args.report, args.notes)
            return 0
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
        elif args.command == "media-import":
            media_import(job)
        elif args.command == "media-export":
            media_export(job)
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
