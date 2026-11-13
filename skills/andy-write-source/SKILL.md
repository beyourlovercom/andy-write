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
