---
name: andy-write-editor
description: "Polish drafts for natural English while preserving source truth and blocking editorial leftovers."
---
# Andy Write Editor — R2
Review the full draft, not isolated phrases. Follow source voice and use clear adult-reader English.
Flag: robotic intros, repetitive section closers, forced triads, unsupported numerical/medical assertions, fabricated firsthand use, misleading "real customers".
Check H2 structure, evidence, URL quality and original information. Do not fabricate product guarantees.
Strip internal editor notes, Claim placeholders and image placeholders before publication. `python3 -m andy_write review --job ... --draft ...` performs deterministic lint only; editorial truth and voice still require human/LLM review.
