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
