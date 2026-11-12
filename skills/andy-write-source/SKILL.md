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
