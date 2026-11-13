---
name: andy-write-source
description: "Classify every supplied paragraph and evidence candidate by topic with stable provenance."
---
# Andy Write Source — R1
Inputs: user-owned source text + research-pack.json.
Record source hash, source ID, segment ID, original paragraph reference and topic cluster.
Keep reference text uncommitted under .runs. Distinguish source-provided anecdotes from verified facts.
Flag model/manufacturer-specific instructions (oil, powder, heat tools, joint movement) as requiring manual verification.
Output source-catalog.json and evidence-ledger.json. Never promote retrieved URLs automatically to verified Claim.

## V1.1 complete-source contract

A source catalog is a navigation aid, not a replacement for the original. Its excerpts and paragraph-size filters never authorize truncating a rewritten article's source. The owning Draft Skill must include the complete Owner article using contract owner-rewrite-full-source-v1.1, with provenance, source hash and prompt integrity validation. Do not invoke Codex for source classification or integrity verification. Overlong source requires explicit chunking design, not silent trimming.

## V1.2 per-paragraph traceability contract

Do not confuse 260-character classification excerpts with the complete original.
Beyond the V1.1 full-text input gate, fidelity reporting now retains a stable
paragraph number and SHA-256 for every source item, including short/heading
items not eligible for automatic lexical scoring. The original prose remains
private and is never copied into the committed QA report.

Shared or boilerplate terms must not cause false retained-status decisions.
Distinctive source term overlap is only a candidate for human semantic review.
No Codex CLI may be invoked by this Skill.

## V1.2 public QC benchmark vs Owner rewrite provenance

Distinguish two evidence roles: (1) Owner/team-supplied ORIGINAL reference
authorizes source-grounded rewriting after hash validation; (2) a public
competitor article is a QC BENCHMARK ONLY, never an Owner original or a model
permission to produce a derivative of its copyrighted prose. Keep full
competitor HTML and Owner source private in Git-ignored .runs; commit only
structural metrics, risk counts, URLs, date/provenance and limitations.

Public source dates must distinguish original 2025 publication from a later
2026 revision. Structural volume does not equal factual soundness. For
numerical, medical, IP-rating, cleaning/compatibility, materials and safety
claims, the evidence must specifically support the exact statement, or
it stays pending human review.

## V1.2.1 source URL is not evidence of claim truth

Separate Owner source (rewriting provenance) from an independently
retrieved institutional or manufacturer paragraph. Require exact
retrieval channel, HTTPS URL, timestamp and hashed actual paragraph;
a page title, source domain or HTTP 200 does not entail the article's
claim. Flag source-topic mismatch, negation and numerical contradictions
for human review. A generic FTC/CDC article is not a product care manual.

The institutional evidence fetch script is read-only and bounded, with
private .runs storage. Log 403/404 honestly, never invent a successful
fetch or substitute a source from a different topic. No Codex for
research, source classification or factual QA.

## V1.2.2 manufacturer evidence identity

For product-specific material/safety assertions, attach an actual retrievable
manufacturer_primary source with matching manufacturer_domain and product_model
and an official_product_manual or official_model_specifications type.
A human review must cite a literal paragraph and verify the same model.
General public agency advice is not a substitute for a model's manual.
